# 标准库导入
import asyncio
import os
import uuid
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import signal
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
import multiprocessing
import multiprocessing.resource_tracker
import multiprocessing.spawn
import multiprocessing.util
from time import time

# 第三方库导入
import numpy as np
import psutil
import soundfile as sf
import torch
from quart import Quart, request, Response, send_file
from quart_cors import cors

# 本地模块导入
from TTS_infer_pack.TTS import TTS, TTS_Config
from TTS_infer_pack.text_segmentation_method import get_method
from tts_server.dao import DatabaseManager
from tts_server.remote_http import RemoteHTTP
from utils import get_maxkb_stream, get_llm_stream, Colors

app = Quart(__name__)
scheduler = AsyncIOScheduler()
app = cors(app, allow_origin="*")
max_workers = 4
future_map = defaultdict(set)
task_control = Manager().dict()

db_config = {
    'dbname': 'maxkb',
    'user': 'postgres',
    'password': 'Password123@postgres',
    'host': '183.131.7.9',
    'port': '5432'
}

def init_worker():
    # 初始化TTS模型
    global tts
    config = TTS_Config("GPT_SoVITS/configs/tts_infer.yaml")
    if torch.cuda.is_available():
        config.device = "cuda:2"
    else:
        config.device = "cpu"
    tts = TTS(config)
    
input_audio_path = "input_audio/input_audio.wav"
input_text_path = "input_audio/input_text.txt"
input_text = ""

with open(input_text_path, "r", encoding="utf-8") as file:
    input_text = file.read()

# 初始化进程池
executor = ProcessPoolExecutor(max_workers=max_workers,initializer=init_worker,mp_context=multiprocessing.get_context('spawn'))

def dummy_task():
    print("进程初始化完成")
    
def dummy_workers():
    print("预热所有进程...")
    dummy_futures = []
    
    for _ in range(max_workers):
        future = executor.submit(dummy_task)
        dummy_futures.append(future)
    for future in dummy_futures:
        future.result()
    print("所有进程已完成初始化")

#滑动窗口
class AudioStreamManager:
    def __init__(self):
        self.audio_buffer = {}  # 存储音频数据的缓冲区
        self.next_index = 1     # 下一个要发送的音频索引
        self.is_completed = False
        
    def add_audio(self, index, audio_data, sr):
        self.audio_buffer[index] = (audio_data, sr)
        
    async def get_next_audio(self):
        """获取下一个音频数据"""
        if self.next_index in self.audio_buffer:
            audio_data, sr = self.audio_buffer[self.next_index]
            self.next_index += 1
            return audio_data, sr,self.next_index-1
        return None
    
    def mark_completed(self):
        self.is_completed = True
        
class TaskCancelledException(Exception):
    pass

def tts_run(
    text: str,
    ref_wav_path: str,
    prompt_text: str = None,
    top_k: int = 5,
    top_p: float = 1.0,
    temperature: float = 1.0,
    speed_factor: float = 1.1,
    ref_text_free: bool = False,
    index: int = None,
    task_control_dict: dict = None,
    request_id: str = None,
    text_split_method: str = "cut0"
):    
    
    inputs = {
        "text": text,
        "text_lang": "zh",
        "ref_audio_path": ref_wav_path,
        "prompt_text": "" if ref_text_free else (prompt_text or ""),
        "prompt_lang": "all_zh",
        "text_split_method": text_split_method,
        "top_k": top_k,
        "top_p": top_p,
        "temperature": temperature,
        "speed_factor": speed_factor,
        "ref_text_free": ref_text_free,
        "return_fragment": False,
        "batch_size": 1,
        "fragment_interval":0.5
    }
    #default output
    audio_data = np.array([])
    sr = 32000
    output_path = f"stream_output_wav/output_{index}.wav"
    
    print(f"运行任务 {index},request_id {request_id}")
    pid = os.getpid()
    if task_control_dict[request_id]:
        print(f"Worker {pid} ，任务{request_id}_{index}在执行前被取消")
        return output_path, index,sr,audio_data
    # 设置信号处理器
    def signal_handler(signum, frame):
        print(f"Worker {pid} 收到信号 {signum}，准备取消任务")
        raise TaskCancelledException("Task cancelled by signal")
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    
    
    try:
        print(f"tts_worker,id:{index} 开始推理...")
        start_time_inference = time()
        item = tts.run(inputs)
        
        for chunk in item:
            sr, audio_data = chunk
            print(f"{Colors.OKGREEN}inference_time_epoch_{inputs['text']}:{time()-start_time_inference:0.2f}秒{Colors.ENDC}")
            output_path = f"stream_output_wav/output_{index}.wav"
            sf.write(output_path, audio_data, sr)
            print(f"音频数据大小:{audio_data.shape}  ,{audio_data}")
        return output_path, index,sr,audio_data
    
    except TaskCancelledException:
        print(f"tts_worker,id:{index} 任务被取消")
        return output_path, index,sr,audio_data
    except Exception as e:
        print(f"tts_worker,id:{index} 任务执行失败 {e}")
        raise
    
@app.route('/chat', methods=['POST'])
async def chat():
    data = await request.get_json()
    question = data.get('question')
    request_id = data.get('request_id')
    llm_stream = get_llm_stream(question,"1")
    index = 1
    audio_manager = AudioStreamManager()
    stream_completed = False
    task_control[request_id] = False    # 任务开始，打断设置为 false
    # 处理单个任务的结果
    def done_callback(future):
        try:
            output_path, idx, sr, audio_data = future.result()
            print(f"任务完成，idx: {idx}")
            audio_manager.add_audio(idx, audio_data, sr)
        except Exception as e:
            print(f"{Colors.RED}任务被取消: {e}{Colors.ENDC}")
        finally:
            # 从活跃任务中移除
            if request_id in future_map and future in future_map[request_id]:
                future_map[request_id].remove(future)
            # 如果所有任务完成，标记音频流完成
            if stream_completed and not future_map[request_id]:
                print(f"{Colors.OKGREEN}所有任务完成_done_callback{Colors.ENDC}")
                audio_manager.mark_completed()
        
    # 创建任务
    async for sentence in llm_stream:
        inputs = {
            "text": sentence,
            "ref_wav_path": input_audio_path,
            "prompt_text": input_text,
            "index": index 
        }
        # 直接提交到进程池并添加回调
        future = executor.submit(
            tts_run,
            inputs["text"],
            inputs["ref_wav_path"],
            inputs["prompt_text"],
            index=inputs["index"],
            request_id=request_id,
            task_control_dict=task_control
        )
        future.add_done_callback(done_callback)
        future_map[request_id].add(future)
        index += 1
    
    stream_completed = True
    
    
    # 生成音频数据流
    async def generate():
        while True:
            res = await audio_manager.get_next_audio()
            if res is not None:
                audio_data, sr, index = res
                yield audio_data.tobytes()
            elif audio_manager.is_completed:
                print(f"{Colors.OKGREEN}所有任务完成_generate{Colors.ENDC}")
                task_control.pop(request_id,None)
                future_map.pop(request_id,None)
                break
            await asyncio.sleep(0.01)
            
    return Response(generate(), mimetype='audio/wav')

@app.route('/tts', methods=['POST'])
async def tts():
    data = await request.get_json()
    text = data.get('text')
    request_id = data.get('request_id')
    rank = data.get('rank')
    index = request_id + "_" + str(rank)
    task_control[request_id] = False    # 任务开始，打断设置为 false

    loop = asyncio.get_event_loop()
    future = executor.submit(
        tts_run,
        text,
        input_audio_path,
        input_text,
        text_split_method="cut1",
        index=index,
        request_id=request_id,
        task_control_dict=task_control,
    )
    
    output_path, idx, sr, audio_data = await loop.run_in_executor(None, future.result)
    # 返回相对路径，去掉前面的目录部分
    relative_path = os.path.basename(output_path)
    res = {
        "path": f"stream_output_wav/{relative_path}",
        "index": idx
    }
    return res

@app.route('/tts_by_content', methods=['POST'])
async def tts_by_content():
    data = await request.get_json()
    text = data.get('text')
    request_id = data.get('request_id')
    
    sentences = get_method("cut5")(text).strip("\n").split("\n")
    for index,sentence in enumerate(sentences):
        if not sentence.strip():  # 如果去掉空格后为空字符串，说明全是空字符
            print(f"第{index}个句子 '{sentence}' 全是空字符")
            continue

        
    
@app.route('/test', methods=['GET'])
async def test():
    print(f"我的 map长度{len(future_map)}")
    print(f"map内容{future_map}")
    return str(len(future_map))


@app.route('/kill', methods=['GET'])
async def kill():
    request_id = request.args.get('request_id')
    print(f"杀死{request_id}")
    if request_id not in future_map:
        print(f"{Colors.RED}杀死{request_id}失败{Colors.ENDC}")
        print(future_map)
        return "not found"
    
    start_time = time()
    print(f"{Colors.OKGREEN}开始杀死{request_id} map长度{len(future_map)} {Colors.ENDC}")
    
    # 1. 取消pending的任务
    futures = future_map.pop(request_id)
    for future in futures:
        future.cancel() # 取消任务
    
    # 2. 设置 flag 让 call queue 中的任务不再执行
    task_control[request_id] = True
    
    # 3. 中断子程中 running 的所有任务，发送SIGINT信号
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    for child in children:
        print(f"准备中断子进程 {child.pid}")
        try:
            os.kill(child.pid, signal.SIGINT)
        except ProcessLookupError:
            print(f"子进程 {child.pid} 不存在")
            continue
    
    
    end_time = time()
    print(f"map长度{Colors.OKGREEN} {len(future_map)} {Colors.ENDC},耗时{end_time-start_time}")
    return str(len(future_map))

def cleanup_audio_files():
    """定期清理生成的音频文件"""
    try:
        output_dir = "stream_output_wav"
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.endswith('.wav'):
                    file_path = os.path.join(output_dir, file)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"删除文件 {file_path} 失败: {e}")
    except Exception as e:
        print(f"清理音频文件时出错: {e}")

def clean_up():
    print("清理资源...")
    
    # 清理音频文件
    cleanup_audio_files()
    
    # 原有的清理代码...
    if 'executor' in globals():
        executor.shutdown(wait=False, cancel_futures=True)
    
    # 获取当前进程及其所有子进程
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    
    # 终止所有子进程
    for child in children:
        try:
            print(f"终止子进程 {child.pid}")
            child.terminate()
        except psutil.NoSuchProcess:
            continue
    
    # 等待子进程终止
    psutil.wait_procs(children, timeout=3)
    
    # 强制结束残留进程
    for child in children:
        try:
            if child.is_running():
                print(f"强制终止子进程 {child.pid}")
                child.kill()
        except psutil.NoSuchProcess:
            continue
            
    # 清理资源追踪器
    multiprocessing.resource_tracker.getfd()
    multiprocessing.resource_tracker._resource_tracker = None
    
    # 清理全局资源
    multiprocessing.util._exit_function()

@app.route('/audio/<path:filename>')
async def serve_audio(filename):
    """
    提供音频文件的访问
    filename: 音频文件的相对路径
    """
    try:
        # 确保文件路径是安全的
        if '..' in filename or filename.startswith('/'):
            return 'Invalid file path', 400
            
        # 构建完整的文件路径
        file_path = os.path.join(os.getcwd(), filename)
        
        if not os.path.exists(file_path):
            return 'File not found', 404
            
        # 发送文件，并设置正确的MIME类型
        return await send_file(
            file_path,
            mimetype='audio/wav'
        )
        
    except Exception as e:
        print(f"提供音频文件时出错: {e}")
        return 'Internal server error', 500

@app.route('/start_periodic_task', methods=['POST'])
async def start_periodic_task():
    data = await request.form
    interval = int(data.get('interval'))
    goods_info = data.get('goods_info')
    choose_num = data.get('choose_num')  
    room_id = data.get('room_id')
    if not interval:
        return {"error": "缺少执行间隔字段"}, 400
    
    # 定义要定时执行的任务
    async def periodic_task(job_id, interval, room_id):
        print(f"定时任务执行于: {time()}")
        remote_http = RemoteHTTP()
        
        #获取b站弹幕接口
        comments = remote_http.get_comment_from_bilibili(room_id, interval)
        # comments.append("这双鞋多少钱")
        
        #ai挑选弹幕
        choose_comments = remote_http.choose_comment(goods_info, comments, choose_num)
        
        answers = []
        
        for choose_comment in choose_comments:
            # 弹幕拿去问 rag
            answer = remote_http.get_chat_completion(choose_comment)
            answers.append(answer)

     
        #存到postgres中
        db_manager = DatabaseManager(db_config)
        db_manager.insert_comments_job(job_id, comments, choose_comments, answers, "", "")

    job_id = str(uuid.uuid4())
    # 添加定时任务
    job = scheduler.add_job(periodic_task, 'interval', seconds=interval, args=[job_id, interval,room_id])

    scheduler.start()
    
    return {"message": "定时任务已启动", "job_id": job.id, "pg_job_id": job_id}, 200

@app.route('/stop_periodic_task', methods=['POST'])
async def stop_periodic_task():
    data = await request.form
    job_id = data.get('job_id')  # 获取要停止的任务ID
    if not job_id:
        return {"error": "缺少任务ID字段"}, 500
    
    # 停止指定的任务
    job = scheduler.get_job(job_id)
    if job:
        job.remove()
        scheduler.shutdown()
        return {"message": "定时任务已停止"}, 200
    else:
        return {"error": "未找到指定的任务ID"}, 500

@app.route('/get_result_by_id', methods=['POST'])
async def get_result_by_id():
    data = await request.form
    job_id = data.get('job_id')  # 获取要查询的任务ID
    if not job_id:
        return {"error": "缺少任务ID字段"}, 400

    db_manager = DatabaseManager(db_config)
    result = db_manager.get_comments_job_by_id(job_id)

    if result:
        comments, choose_comments, answers, video_url, audio_url = result['comments'], result['choose_comments'], result['answers'],result['video_url'], result['audio_url']
        return {
            "job_id": job_id,
            "comments": comments,
            "choose_comments": choose_comments,
            "answers": answers,
            "video_url": video_url,
            "audio_url": audio_url
        }, 200
    else:
        return {"error": "未找到指定的任务ID"}, 404
    
if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs("stream_output_wav", exist_ok=True)
    
    dummy_workers()
    try:
        app.run(host="0.0.0.0", port=5006, debug=False, use_reloader=False)
    finally:
        clean_up()
        print("tts服务器已关闭")
    