from utils import get_llm_stream, get_maxkb_stream
import aiohttp
import asyncio
import json
import time
import os
from quart import Quart, request, Response
import queue
import threading
import numpy as np
import struct
app = Quart(__name__)

# 添加新的类来管理音频数据队列
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

async def send_tts_request(session, text, index):
    url = "http://localhost:5002/tts"
    data = {
        "text": text,
        "index": index,
    }
    
    try:
        print(f"请求 {index} 开始")
        start_time = time.time()
        
        async with session.post(url, json=data) as response:
            if response.status == 200:
                # 创建输出文件
                output_path = f"stream_output_wav/output_{index}.wav"
                with open(output_path, "wb") as f:
                    # 流式接收数据
                    async for chunk in response.content.iter_chunks():
                        if not chunk:
                            break
                        # 从每个块中提取序号和音频数据
                        index_bytes = chunk[0][:4]  # 前4字节是序号
                        audio_data = chunk[0][4:]   # 剩余字节是音频数据
                        chunk_index = struct.unpack('!I', index_bytes)[0]
                        print(f"接收第 {chunk_index} 块数据")
                        f.write(audio_data)
                
                end_time = time.time()
                print(f"请求 {index} 完成，耗时: {end_time - start_time:.2f} 秒")
                return {
                    "audio_path": output_path,
                    "processing_time": end_time - start_time,
                    "index": index
                }
            else:
                print(f"请求 {index} 失败: {response.status}")
                return None
    except Exception as e:
        print(f"请求 {index} 发生错误: {str(e)}")
        return None
    
async def send_tts_request_by_chunk(session, text, index):
    url = "http://localhost:5002/tts"
    data = {
        "text": text,
        "index": index,
    }
    
    try:
        async with session.post(url, json=data) as response:
            if response.status == 200:
                # 读取头部信息
                header_line = await response.content.readline()
                header = json.loads(header_line.decode('utf-8'))
                sr = header['sample_rate']
                
                # 读取音频数据
                audio_bytes = bytearray()
                async for chunk in response.content:
                    audio_bytes.extend(chunk)
                
                # 转换为numpy数组
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                return index, audio_data, sr
                
    except Exception as e:
        print(f"请求 {index} 发生错误: {str(e)}")
        return None
    
async def process_stream(queue, pending_tasks): 
    audio_manager = AudioStreamManager()
    
    async def process_queue():
        while True:
            try:
                result = await queue.get()
                if result is None:  # 结束信号
                    if pending_tasks:
                        await asyncio.gather(*pending_tasks)
                    audio_manager.mark_completed()
                    break
                
                index, audio_data, sr = result
                print(f"add audio: {index}")
                audio_manager.add_audio(index, audio_data, sr)
                queue.task_done()
                
            except Exception as e:
                print(f"处理结果时出错: {e}")
    
    queue_task = asyncio.create_task(process_queue())
    return audio_manager, queue_task

async def process_text_stream(text_stream, session, result_queue):
    """处理文本流，发送请求"""
    index = 1
    active_tasks = set()
    
    start_time = time.time()
    stream_completed = False
    
    async for text in text_stream:
        print(f"发送请求 {index}")
        task = asyncio.create_task(send_tts_request_by_chunk(session, text, index))
        active_tasks.add(task)
        
        def done_callback(t, task=task):
            if t.exception() is None and t.result() is not None:
                asyncio.create_task(result_queue.put(t.result()))
                
            active_tasks.remove(task)
            if not active_tasks and stream_completed:
                asyncio.create_task(result_queue.put(None))

        task.add_done_callback(done_callback)
        index += 1
    end_time = time.time()
    stream_completed = True
    print(f"发送请求完成，耗时: {end_time - start_time:.2f} 秒")
    if not active_tasks:
        asyncio.create_task(result_queue.put(None))
        
async def process_question(question):
    """处理用户问题的主函数"""
    os.makedirs("stream_output_wav", exist_ok=True)
    
    result_queue = asyncio.Queue()
    
    async with aiohttp.ClientSession() as session:
        # text_stream = get_llm_stream(question, "1")
        text_stream = get_maxkb_stream(question)
        pending_tasks = await process_text_stream(text_stream, session, result_queue)
        audio_manager, queue_task = await process_stream(result_queue, pending_tasks)
        
        return audio_manager, queue_task

@app.route('/chat', methods=['POST'])
async def chat():
    """处理用户聊天请求的路由"""
    if not request.is_json:
        return {"error": "请求必须是JSON格式"}, 400
    
    data = await request.get_json()
    question = data.get('question')
    
    if not question:
        return {"error": "question不能为空"}, 400

    print("---------------------START PROCESS QUESTION---------------------")
    
    # 创建必要的队列和管理器
    result_queue = asyncio.Queue()
    audio_manager = AudioStreamManager()
    
    # 创建处理任务但不等待其完成
    async def process_background():
        async with aiohttp.ClientSession() as session:
            text_stream = get_maxkb_stream(question)
            await process_text_stream(text_stream, session, result_queue)
            
            # 处理结果队列
            while True:
                try:
                    result = await result_queue.get()
                    if result is None:  # 结束信号
                        audio_manager.mark_completed()
                        break
                    
                    index, audio_data, sr = result
                    print(f"add audio: {index}")
                    audio_manager.add_audio(index, audio_data, sr)
                    result_queue.task_done()
                    
                except Exception as e:
                    print(f"处理结果时出错: {e}")
    
    # 启动后台处理任务
    background_task = asyncio.create_task(process_background())
    
    print("---------------------START GENERATE---------------------")
    start_time = time.time()
    async def generate():
        while True:
            res = await audio_manager.get_next_audio()
            if res is not None:
                audio_data, sr, index = res
                yield audio_data.tobytes()
            elif audio_manager.is_completed:
                break
            await asyncio.sleep(0.01)
    
    return Response(
        generate(),
        mimetype='audio/wav'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004,debug=False)
