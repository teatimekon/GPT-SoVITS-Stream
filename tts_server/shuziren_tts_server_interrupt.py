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
import json
import base64
from datetime import datetime
import hashlib

# 第三方库导入
import numpy as np
import psutil
import soundfile as sf
import torch
from quart import Quart, request, Response, send_file
from quart_cors import cors
import aiohttp

# 本地模块导入
from TTS_infer_pack.TTS import TTS, TTS_Config
from TTS_infer_pack.text_segmentation_method import get_method
from tts_server.dao import DatabaseManager
from tts_server.redis_dao import RedisManager
from tts_server.remote_http import RemoteHTTP
from utils import get_maxkb_stream, get_llm_stream, Colors

app = Quart(__name__)
scheduler = AsyncIOScheduler()
app = cors(app, allow_origin="*")
max_workers = 4
future_map = defaultdict(set)
task_control = Manager().dict()

db_config = {
    "dbname": "maxkb",
    "user": "postgres",
    "password": "Password123@postgres",
    "host": "183.131.7.9",
    "port": "5432",
}

redis_config = {
    "host": "localhost",
    "port": 6380,
    "db": 0,
    "password": "bobbyishandsome",
}


def init_worker():
    # 初始化TTS模型
    global tts
    config = TTS_Config("GPT_SoVITS/configs/tts_infer.yaml")
    if torch.cuda.is_available():
        config.device = "cuda:3"
    else:
        config.device = "cpu"
    tts = TTS(config)


input_audio_path = "input_audio/input_audio.wav"
input_text_path = "input_audio/input_text.txt"
input_text = ""

with open(input_text_path, "r", encoding="utf-8") as file:
    input_text = file.read()

# 初始化进程池
executor = ProcessPoolExecutor(
    max_workers=max_workers,
    initializer=init_worker,
    mp_context=multiprocessing.get_context("spawn"),
)


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


# 滑动窗口
class AudioStreamManager:
    def __init__(self):
        self.audio_buffer = {}  # 存储音频数据的缓冲区
        self.next_index = 1  # 下一个要发送的音频索引
        self.is_completed = False

    def add_audio(self, index, audio_data, sr, text):
        self.audio_buffer[index] = (audio_data, sr, text)

    async def get_next_audio(self):
        """获取下一个音频数据"""
        if self.next_index in self.audio_buffer:
            audio_data, sr, text = self.audio_buffer[self.next_index]
            self.next_index += 1
            return audio_data, sr, text, self.next_index - 1
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
    text_split_method: str = "cut0",
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
        "fragment_interval": 0.5,
    }
    # default output
    audio_data = np.array([])
    sr = 32000
    output_path = f"stream_output_wav/output_{index}.wav"

    print(f"运行任务 {index},request_id {request_id}")
    pid = os.getpid()
    if task_control_dict[request_id]:
        print(f"Worker {pid} ，任务{request_id}_{index}在执行前被取消")
        return output_path, index, sr, audio_data

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
            print(
                f"{Colors.OKGREEN}inference_time_epoch_{inputs['text']}:{time()-start_time_inference:0.2f}秒{Colors.ENDC}"
            )
            output_path = f"stream_output_wav/output_{index}.wav"
            sf.write(output_path, audio_data, sr)
            print(f"音频数据大小:{audio_data.shape}  ,{audio_data}")
        return output_path, index, sr, audio_data, text

    except TaskCancelledException:
        print(f"tts_worker,id:{index} 任务被取消")
        return output_path, index, sr, audio_data, text
    except Exception as e:
        print(f"tts_worker,id:{index} 任务执行失败 {e}")
        raise


@app.route("/chat", methods=["POST"])
async def chat():
    data = await request.get_json()
    question = data.get("question")
    request_id = data.get("request_id")
    goods_info = data.get("goods_info")
    goods_message = "\n\n 下面是你需要知道的额外信息：\n—————————————————\n 本次活动的商品信息:\n"
    for key, value in goods_info.items():
        goods_message += f"{key}: {value}\n"
    # llm_stream = get_llm_stream(question,"1")
    goods_message = goods_message + "\n—————————————————\n\n"
    question = goods_message + question


    print(f"{Colors.OKGREEN}问题{question}{Colors.ENDC}")
    llm_stream = get_maxkb_stream(question=question)
    index = 1
    audio_manager = AudioStreamManager()
    stream_completed = False
    task_control[request_id] = False  # 任务开始，打断设置为 false

    # 处理单个任务的结果
    def done_callback(future):
        try:
            output_path, idx, sr, audio_data, text = future.result()
            print(f"任务完成，idx: {idx}")
            audio_manager.add_audio(idx, audio_data, sr, text)
        except Exception as e:
            print(f"{Colors.RED}任务被取消: {e}{Colors.ENDC}")
        finally:
            # 从活跃任务中移除
            if request_id in future_map and future in future_map[request_id]:
                future_map[request_id].remove(future)
            # 如果所有任务完成，标记音频完成
            if stream_completed and not future_map[request_id]:
                print(f"{Colors.OKGREEN}所有任务完成_done_callback{Colors.ENDC}")
                audio_manager.mark_completed()

    # 创建任务
    async for sentence in llm_stream:
        inputs = {
            "text": sentence,
            "ref_wav_path": input_audio_path,
            "prompt_text": input_text,
            "index": index,
        }
        # 直接提交到进程池并添加回调
        future = executor.submit(
            tts_run,
            inputs["text"],
            inputs["ref_wav_path"],
            inputs["prompt_text"],
            index=inputs["index"],
            request_id=request_id,
            task_control_dict=task_control,
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
                audio_data, sr, text, index = res

                # 创建包含文本和音频的JSON数据
                chunk_data = {
                    "text": text,
                    "index": index,
                    "audio": base64.b64encode(audio_data.tobytes()).decode("utf-8"),
                }

                # yield JSON字符串
                yield json.dumps(chunk_data) + "\n"

            elif audio_manager.is_completed:
                print(f"{Colors.OKGREEN}所有任务完成_generate{Colors.ENDC}")
                task_control.pop(request_id, None)
                future_map.pop(request_id, None)
                break
            await asyncio.sleep(0.01)

    return Response(
        generate(),
        mimetype="application/x-ndjson",  # 使用换行分隔的JSON流
        headers={"Transfer-Encoding": "chunked"},
    )


# 单条文本转语音
async def process_tts(text, request_id, rank=0):
    text_hash = hashlib.md5(text.encode()).hexdigest()  
    index = text_hash
    task_control[request_id] = False  # 任务开始，打断设置为 false

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

    output_path, idx, sr, audio_data, text = await loop.run_in_executor(
        None, future.result
    )
    # 返回相对路径，去掉前面的目录部分
    relative_path = os.path.basename(output_path)
    res = {
        "path": f"stream_output_wav/{relative_path}",
    }
    return res


# audio转视频
async def audio_to_video(audio_path,text):
    form_data = aiohttp.FormData()
    form_data.add_field("audio_path", audio_path)
    form_data.add_field("video_path", "/disk6/dly/MuseTalk/results/input/default_video.mp4")
    form_data.add_field("bbox_shift", "0")
    form_data.add_field("text", text)
    async with aiohttp.ClientSession() as session:
        base_url = "http://183.131.7.9:5002/generate_video"
        timeout = aiohttp.ClientTimeout(total=None)  # 设置永不超时
        async with session.post(base_url, data=form_data, timeout=timeout) as response:
            if response.status == 200:
                result = await response.json()
                print(f"视频生成成功，url: {result['video_url']}")
                return result
            else:
                return {"error": "Failed to generate video"}


# 弹幕转视频
async def comment_to_video(comment, request_id):
    # 1. 文本转音频
    text_hash = hashlib.md5(comment.encode()).hexdigest()
    execpt_out_put_path = f"stream_output_wav/output_{text_hash}.wav"
    if os.path.exists(execpt_out_put_path):
        res = {"path": execpt_out_put_path}
    else:
        res = await process_tts(comment, request_id)
    # res = "input_audio/hutao_v1.wav"
    # 本地音频绝对路径发给echomimic
    abs_audio_path = os.path.join(os.getcwd(), res.get("path"))
    # 2. 音频转视频
    res = await audio_to_video(abs_audio_path,comment)
    
    #test
    # await asyncio.sleep(2)
    # res = {"video_url": "output_video_with_audio_20241206114838.mp4" }
    
    return res


# 音频的接口，输入文本，转音频
@app.route("/tts", methods=["POST"])
async def tts():
    data = await request.get_json()
    text = data.get("text")
    request_id = data.get("request_id")
    rank = data.get("rank")

    text_hash = hashlib.md5(text.encode()).hexdigest()
    execpt_out_put_path = f"stream_output_wav/output_{text_hash}.wav"
    if os.path.exists(execpt_out_put_path):
        return {"path": execpt_out_put_path}
    res = await process_tts(text, request_id, rank)

    return res


# 视频的接口，输入文本，文本通过 tts 转成音频，再调用 echomimic 接口生成视频，返回对应 url
@app.route("/tts_to_video", methods=["POST"])
async def tts_to_video():
    data = await request.get_json()
    text = data.get("text")
    request_id = data.get("request_id")
    
    if text == "":
        return {"error": "text is empty"}
    res = await comment_to_video(text, request_id)
    # res = {"video_url": "output_video_with_audio_20241210120605.mp4" }
    return res


@app.route("/test", methods=["GET"])
async def test():
    print(f"我的 map长度{len(future_map)}")
    print(f"map内容{future_map}")
    return str(len(future_map))


@app.route("/kill", methods=["GET"])
async def kill():
    request_id = request.args.get("request_id")
    print(f"杀死{request_id}")
    if request_id not in future_map:
        print(f"{Colors.RED}杀死{request_id}失败{Colors.ENDC}")
        print(future_map)
        return "not found"

    start_time = time()
    print(
        f"{Colors.OKGREEN}开始杀死{request_id} map长度{len(future_map)} {Colors.ENDC}"
    )

    # 1. 取消pending的任务
    futures = future_map.pop(request_id)
    for future in futures:
        future.cancel()  # 取消任务

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
    print(
        f"map长度{Colors.OKGREEN} {len(future_map)} {Colors.ENDC},耗时{end_time-start_time}"
    )
    return str(len(future_map))


@app.route("/video/<path:filename>")
async def serve_video(filename):
    # video的路径文件夹在/disk6/dly/bobby_echomimic/output/tmp下
    video_abs_folder = "/disk6/dly/MuseTalk/results/output/"
    video_abs_path = os.path.join(video_abs_folder, filename)
    return await send_file(video_abs_path, mimetype="video/mp4")


@app.route("/audio/<path:filename>")
async def serve_audio(filename):
    """
    提供音频文件的访问
    filename: 音频文件的相对路径
    """
    try:
        # 确保文件路径是安全的
        if ".." in filename or filename.startswith("/"):
            return "Invalid file path", 400

        # 构建完整的文件路径
        file_path = os.path.join(os.getcwd(), filename)

        if not os.path.exists(file_path):
            return "File not found", 404

        # 发送文件，并设置正确的MIME类型
        return await send_file(file_path, mimetype="audio/wav")

    except Exception as e:
        print(f"提供音频文件时出错: {e}")
        return "Internal server error", 500


def clean_up():
    print("清理资源...")

    # 清理音频文件
    # cleanup_audio_files()

    # 原有的清理代码...
    if "executor" in globals():
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


def cleanup_audio_files():
    """定期清理生成的音频文件"""
    try:
        output_dir = "stream_output_wav"
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.endswith(".wav"):
                    file_path = os.path.join(output_dir, file)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"删除文件 {file_path} 失败: {e}")
    except Exception as e:
        print(f"清理音频文件时出错: {e}")

# 修改后的periodic_task函数
async def periodic_task(job_id, interval, room_id, style, goods_info, choose_num):
    print(f"{Colors.OKGREEN}定时任务执行于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    remote_http = RemoteHTTP()
    
    # 获取弹幕和选择评论
    comments = remote_http.get_comment_from_bilibili(room_id, interval)
    # comments.append("这双鞋多少钱")
    print(f"{Colors.OKGREEN}获取弹幕{comments}{Colors.ENDC}")
    if not comments:
        return {"error": "comments is empty"}
    choose_comments = remote_http.choose_comment(goods_info, comments, choose_num)
    # choose_comments = ["111", "222", "333"]
    # 用于跟踪所有任务的完成状态
    tasks = []
    answers = []
    print(f"{Colors.OKGREEN}choose_comments{choose_comments}{Colors.ENDC}")
    async def process_comment(choose_comment,goods_info):
        # 获取answer
        combined_message = f"商品信息: {goods_info}\n问题: {choose_comment}\n要求：回答字数20字以内"
        answer = remote_http.get_chat_completion(combined_message)
        print(f"{Colors.OKGREEN}回答: {answer}{Colors.ENDC}")
        answers.append(answer)
        
        # 生成视频
        request_id = str(uuid.uuid4())
        video_url = await comment_to_video(answer, request_id)
        if video_url.get("error"):
            return {"error": "video_url is empty"}
        # 存入Redis
        redisManager = RedisManager(redis_config)
        queue_name = f"video_url_{job_id}"
        data = {
            "video_url": video_url.get("video_url"),
            "job_id": job_id,
            "choose_comment": choose_comment,
            "answer": answer,
        }
        print(f"{Colors.GREY}评论{choose_comment}  存入Redis{Colors.ENDC}")
        redisManager.enqueue(queue_name, data)
        
        return answer

    # 为每个评论创建异步任务
    for choose_comment in choose_comments:
        task = asyncio.create_task(process_comment(choose_comment,goods_info))
        tasks.append(task)
    
    # 创建数据库更新任务,但不等待它完成
    async def update_db():
        try:
            # 等待所有视频处理完成
            await asyncio.gather(*tasks)
            # 更新数据库
            db_manager = DatabaseManager(db_config)
            db_manager.insert_comments_job(
                job_id, comments, choose_comments, answers, "", ""
            )
        except Exception as e:
            print(f"数据库更新失败: {e}")

    # 启动数据库更新任务但不等待
    asyncio.create_task(update_db())

@app.route("/start_periodic_task", methods=["POST"])
async def start_periodic_task():
    data = await request.form
    interval = int(data.get("interval"))
    goods_info = data.get("goods_info")
    choose_num = data.get("choose_num")
    room_id = data.get("room_id")
    style = data.get("style")
    
    if not interval:
        return {"error": "缺少执行间隔字段"}, 400

    job_id = str(uuid.uuid4())
    print(f"{Colors.OKGREEN}添加定时任务{job_id}{Colors.ENDC}")
    # 添加定时任务
    job = scheduler.add_job(
        periodic_task,
        "interval", 
        seconds=interval,
        args=[job_id, interval, room_id, style, goods_info, choose_num],
        next_run_time=datetime.now()
    )

    # 立即返回,不等待任务完成
    return {
        "message": "定时任务已启动",
        "job_id": job.id,
        "pg_job_id": job_id
    }, 200

@app.route("/stop_periodic_task", methods=["POST"])
async def stop_periodic_task():
    data = await request.form
    job_id = data.get("job_id")  # 获取要停止的任务ID
    pg_job_id = data.get("pg_job_id")
    if not job_id:
        return {"error": "缺少任务ID字段"}, 500
    
    redis = RedisManager(redis_config)
    redis.delete_queue(f"video_url_{pg_job_id}")
    # 停止指定的任务
    job = scheduler.get_job(job_id)
    if job:
        job.remove()
        return {"message": "定时任务已停止"}, 200
    else:
        return {"error": "未找到指定的任务ID"}, 500


@app.route("/get_result_by_id", methods=["POST"])
async def get_result_by_id():
    data = await request.form
    job_id = data.get("job_id")  # 获取要查询的任务ID
    if not job_id:
        return {"error": "缺少任务ID字段"}, 400

    db_manager = DatabaseManager(db_config)
    result = db_manager.get_comments_job_by_id(job_id)

    if result:
        comments, choose_comments, answers, video_url, audio_url = (
            result["comments"],
            result["choose_comments"],
            result["answers"],
            result["video_url"],
            result["audio_url"],
        )
        return {
            "job_id": job_id,
            "comments": comments,
            "choose_comments": choose_comments,
            "answers": answers,
            "video_url": video_url,
            "audio_url": audio_url,
        }, 200
    else:
        return {"error": "未找到指定的任务ID"}, 404

@app.route("/get_queue_data", methods=["POST"])
async def get_queue_data():
    data = await request.form
    job_id = data.get("job_id")  
    if not job_id:
        return {"error": "缺少任务ID字段"}, 400

    queue_name = f"video_url_{job_id}"
    redis_manager = RedisManager(redis_config)
    
    # 从队列中取出数据
    data_dict = redis_manager.dequeue(queue_name)
    
    if data_dict:
        return {
            "job_id": job_id,
            "video_url": data_dict['video_url'],
            "choose_comment": data_dict['choose_comment'],
            "answer": data_dict['answer'], 
            "status": "success"
        }, 200
    else:
        # 改为返回200状态码，但在响应中指明没有数据
        return {
            "status": "empty",
            "message": "队列中暂无数据",
            "job_id": job_id
        }, 200


@app.before_serving
async def startup():
    # 在app启动服务前启动scheduler
    scheduler.start()

@app.after_serving
async def shutdown():
    # 在app停止服务时关闭scheduler
    scheduler.shutdown()

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs("stream_output_wav", exist_ok=True)

    dummy_workers()
    try:
        app.run(host="0.0.0.0", port=5011, debug=False, use_reloader=False)
    finally:
        clean_up()
        print("tts服务器已关闭")
