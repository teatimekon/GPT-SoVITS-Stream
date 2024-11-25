from utils import get_maxkb_stream,get_llm_stream
from quart import Quart, request, Response
from concurrent.futures import ProcessPoolExecutor
from time import time
from TTS_infer_pack.TTS import TTS, TTS_Config
from utils import Colors
import torch
import soundfile as sf
import numpy as np
import asyncio
import multiprocessing
import signal
import psutil
import atexit
import multiprocessing.resource_tracker
import multiprocessing.spawn
import multiprocessing.util

app = Quart(__name__)
max_workers = 4

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
#添加新的类来管理音频数据队列
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

def tts_run(
    text: str,
    ref_wav_path: str,
    prompt_text: str = None,
    top_k: int = 5,
    top_p: float = 1.0,
    temperature: float = 1.0,
    speed_factor: float = 1.1,
    ref_text_free: bool = False,
    cut_method: str = "cut0",
    index: int = None
):    
    inputs = {
        "text": text,
        "text_lang": "zh",
        "ref_audio_path": ref_wav_path,
        "prompt_text": "" if ref_text_free else (prompt_text or ""),
        "prompt_lang": "all_zh",
        "text_split_method": cut_method,
        "top_k": top_k,
        "top_p": top_p,
        "temperature": temperature,
        "speed_factor": speed_factor,
        "ref_text_free": ref_text_free,
        "return_fragment": False,
        "batch_size": 1,
        "fragment_interval":0.5
    }
    print(f"tts_worker,id:{index} 开始推理...")
    start_time_inference = time()
    item = tts.run(inputs)
    audio_data = np.array([])
    sr = 32000
    output_path = f"stream_output_wav/output_{index}.wav"
    for chunk in item:
        sr, audio_data = chunk
        print(f"{Colors.OKGREEN}inference_time_epoch_{inputs['text']}:{time()-start_time_inference:0.2f}秒{Colors.ENDC}")
        output_path = f"stream_output_wav/output_{index}.wav"
        sf.write(output_path, audio_data, sr)
        print(f"音频数据大小:{audio_data.shape}  ,{audio_data}")
        return output_path, index,sr,audio_data
    return output_path, index,sr,audio_data

@app.route('/chat', methods=['POST'])
async def chat():
    data = await request.get_json()
    question = data.get('question')
    llm_stream = get_llm_stream(question,"1")
    index = 1
    audio_manager = AudioStreamManager()
    active_tasks = set()
    stream_completed = False

    # 处理单个任务的结果
    def done_callback(future):
        try:
            output_path, idx, sr, audio_data = future.result()
            print(f"任务完成，idx: {idx}")
            audio_manager.add_audio(idx, audio_data, sr)
            active_tasks.remove(future)
            if not active_tasks and stream_completed:
                audio_manager.mark_completed()
        except Exception as e:
            print(f"任务处理出错: {e}")
        
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
            index=inputs["index"]
        )
        future.add_done_callback(done_callback)
        active_tasks.add(future)
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
                break
            await asyncio.sleep(0.01)
            
    return Response(generate(), mimetype='audio/wav')
 
def clean_up():
    print("清理资源...")
    
    # 关闭进程池
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


def signal_handler(signum, frame):
    print(f"接收到信号 {signum}")
    clean_up()
    exit(0)

if __name__ == "__main__":
    dummy_workers()
    try:
        app.run(host="0.0.0.0", port=5005, debug=False,use_reloader=False)
    finally:
        clean_up()
        print("tts服务器已关闭")
    