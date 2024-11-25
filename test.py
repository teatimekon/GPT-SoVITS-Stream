from utils import get_maxkb_stream,get_llm_stream
from collections import defaultdict
from quart import Quart, request, Response
from concurrent.futures import ProcessPoolExecutor
from time import time
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
import os
import time 
from multiprocessing import Manager
app = Quart(__name__)
max_workers = 4
future_map = defaultdict(set)
# 初始化进程池
executor = ProcessPoolExecutor(max_workers=max_workers,mp_context=multiprocessing.get_context('spawn'))
# task_control = defaultdict(lambda: {'cancel': False})

task_control = Manager().dict()

def circle_task(i,request_id):
    i = 0
    while True:
        time.sleep(1)
        print(f"运行任务 {i},request_id {request_id}, 次数{i}")
        i += 1
        if i == 5:
            break
class TaskCancelledException(Exception):
    pass

def worker(i,request_id,task_control_dict):
    pid = os.getpid()
    print(f"task_control {task_control_dict}")
    print(f"worker {pid},now working {request_id}_{i}")
    if task_control_dict[request_id]:
        print(f"Worker {pid} ，任务{request_id}_{i}在执行前被取消")
        return f"cancelled_before_start_{request_id}_{i}"

    # 设置信号处理器
    def signal_handler(signum, frame):
        print(f"Worker {pid} 收到信号 {signum}，准备取消任务")
        raise TaskCancelledException("Task cancelled by signal")
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        circle_task(i,request_id)
    except TaskCancelledException:
        print(f"Worker {pid} 任务被取消")
        return str(request_id) + "_" + str(i) + "_cancelled"
    except Exception as e:
        print(f"Worker {pid} 任务执行失败 {e}")
        raise
    
    return str(request_id) + "_" + str(i)

@app.route('/chat', methods=['GET'])
async def chat():
    request_id = request.args.get('request_id')
    print(f"我的 pid {os.getpid()},request_id 是 {request_id}")
    def done_callback(future):
        try:
            res = future.result()
            print(f"任务完成 {res}")
        except Exception as e:
            print(f"任务被取消 {e}")
        finally:    
            if request_id in future_map and future in future_map[request_id]:
                future_map[request_id].remove(future)
    
    task_control[request_id] = False
    task_control["test"] = 0
    for i in range(20):
        future = executor.submit(worker,i,request_id,task_control)
        # 添加回调函数
        future.add_done_callback(done_callback)
        # 添加到future_map
        future_map[request_id].add(future)
        print(f"submitted {request_id}_{i}")
        
    #任务完成了流式输出 
    async def generate():
        while True:
            if request_id not in future_map or len(future_map[request_id]) == 0:
                future_map.pop(request_id,None)
                task_control.pop(request_id,None)
                print(f"所有任务完成")
                break
            
            await asyncio.sleep(0.1)
            yield f"data: hello {request_id}\n\n"
    return Response(generate(),content_type='text/event-stream')


@app.route('/kill', methods=['GET'])
async def kill():
    request_id = request.args.get('request_id')
    if request_id not in future_map:
        return "not found"
    
    from utils import Colors
    start_time = time.time()
    print(f"{Colors.OKGREEN}开始杀死{request_id} map长度{len(future_map)} {Colors.ENDC}")
    
    task_control[request_id] = True
    
    #取消pending中的任务
    futures = future_map[request_id].copy()
    for future in futures:
        future.cancel() # 取消任务
    future_map.pop(request_id)
    
    #中断子进程中 running 的所有任务，发送SIGINT信号
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    for child in children:
        print(f"准备中断子进程 {child.pid}")
        try:
            os.kill(child.pid, signal.SIGINT)
        except ProcessLookupError:
            print(f"子进程 {child.pid} 不存在")
            continue
    
    end_time = time.time()
    print(f"map长度{Colors.OKGREEN} {len(future_map)} {Colors.ENDC},耗时{end_time-start_time}")
    return str(len(future_map))

@app.route('/test', methods=['GET'])
async def test():
    task_control["add_test"] = "added test"
    return str(len(future_map))

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
    try:
        app.run(host="0.0.0.0", port=5010, debug=False,use_reloader=False)
    finally:
        clean_up()
        print("test服务器已关闭")
    