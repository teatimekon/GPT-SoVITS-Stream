# tts_server.py
from flask import Flask, request, jsonify,Response
from multiprocessing import Process, Manager, Queue
import multiprocessing as mp
import asyncio
from concurrent.futures import ProcessPoolExecutor
import time
import random
from queue import Empty
from TTS_infer_pack.TTS import TTS, TTS_Config
from time import time
from utils import Colors
import torch
import os
import soundfile as sf
import psutil
import signal
import atexit
import struct
import json
import numpy as np
os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = Flask(__name__)

def dummy_task():
    print("进程初始化完成")

def init_worker():
    """初始化worker进程中的TTS模型"""
    global worker_tts
    # 检查是否已经初始化
    worker_tts = None
    if not worker_tts or not hasattr(worker_tts, '_is_initialized') :
        print("初始化worker进程的TTS模型...")
        config = TTS_Config("GPT_SoVITS/configs/tts_infer.yaml")
        if torch.cuda.is_available():
            config.device = "cuda"
        else:
            config.device = "cpu"
        worker_tts = TTS(config)
        worker_tts._is_initialized = True
        print("Worker TTS模型初始化完成")

class TTS_Worker_Manager:
    def __init__(self):
        self.max_workers = 4
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers, initializer=init_worker,)
        self.dummy_workers()    #预热所有进程
        
    def process_request(self, data):
        index = data.get('index')
        future = self.executor.submit(tts_worker,**data)
        return future, index
    
    def dummy_workers(self):
        print("预热所有进程...")
        dummy_futures = []
        for _ in range(self.max_workers):
            future = self.executor.submit(dummy_task)
            dummy_futures.append(future)
        
        # 等待所有进程初始化完成
        for future in dummy_futures:
            future.result()
        print(f"所有 {self.max_workers} 个进程已完成初始化")
    def shutdown(self):
        self.executor.shutdown(wait=False)    
        
def tts_worker(
    text: str,
    ref_wav_path: str,
    prompt_text: str = None,
    top_k: int = 5,
    top_p: float = 1.0,
    temperature: float = 1.0,
    speed_factor: float = 1.1,
    ref_text_free: bool = False,
    cut_method: str = "cut0",
    main_start_time: float = None,
    index: int = None
):
    
    global worker_tts   
    
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
    item = worker_tts.run(inputs)
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
@app.route('/tts', methods=['POST']) 
async def tts_process():
    data = request.json
    index = data.get('index')
    iter_start_time = time()
    prompt_text = ""
    with open("input_audio/input_text.txt", "r", encoding="utf-8") as file:
        prompt_text = file.read()
    inputs = {
        "text": text,
        "index": data.get('index'),
        "ref_wav_path": "input_audio/input_audio.wav",
        "prompt_text": prompt_text,
    }
    # 提交任务
    future, req_index = worker_manager.process_request(inputs)
    
    # 等待当前任务完成并将结果放入队列
    result = future.result()
    iter_end_time = time()
    
    print(f"{Colors.RED}请求 {index} 完成，耗时: {iter_end_time - iter_start_time:.2f} 秒{Colors.ENDC}")
    
    def generate_audio_data_stream(result):
        chunk_size = 8192
        audio_data = result[3]
        sr = result[2]
        
        # 将音频数据转换为字节流
        audio_bytes = audio_data.tobytes()
        
        # 构建头部信息
        header = {
            'sample_rate': sr,
            'chunk_size': chunk_size
        }
        
        # 发送头部信息
        header_bytes = json.dumps(header).encode('utf-8')
        yield header_bytes + b'\n'  # 使用换行符作为分隔符
        
        # 分块发送音频数据
        for i in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[i:i + chunk_size]
            yield chunk
    def generate_audio_data(result):
        sr = result[2]
        audio_data = result[3]
        # 数据格式: [采样率(4字节) | 数据长度(4字节) | 音频数据]
        audio_data_bytes = audio_data.tobytes()
        data_len_bytes = struct.pack('!I', len(audio_data_bytes))
        sr_bytes = struct.pack('!I', sr)
        print(f"{Colors.RED}sr_bytes长度: {len(sr_bytes)} {Colors.ENDC}")
        print(f"{Colors.RED}data_bytes长度: {len(audio_data_bytes)} {Colors.ENDC}")
        return sr_bytes + data_len_bytes + audio_data_bytes
    return Response(
        generate_audio_data_stream(result),
        content_type='application/octet-stream'
    )

def monitor_resources():
    """监控系统资源使用情况"""
    current_process = psutil.Process()
    print(f"\n当前进程 (PID {current_process.pid}) 资源使用情况:")
    print(f"CPU 使用率: {current_process.cpu_percent()}%")
    print(f"内存使用: {current_process.memory_info().rss / 1024 / 1024:.1f} MB")
    
    if torch.cuda.is_available():
        print("\nGPU 内存使用情况:")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.memory_allocated(i) / 1024 / 1024:.1f} MB")
            
def clean_up():
    print("清理资源...")
    if 'worker_manager' in globals():
        worker_manager.executor.shutdown(wait=False, cancel_futures=True)
    monitor_resources()
    
    current_process = psutil.Process()
    children_processes = current_process.children(recursive=True)
    
    for child in children_processes:
        print(f"终止子进程 {child.pid}")
        child.terminate()
    current_process.terminate()
    
            
if __name__ == '__main__':
    
    
    worker_manager = TTS_Worker_Manager()
    
    app.run(port=5002)
    clean_up()
    print("tts服务器已关闭")
    