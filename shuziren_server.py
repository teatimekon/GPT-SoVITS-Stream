from utils import get_llm_stream
import aiohttp
import asyncio
import json
import time
import os
import struct
from utils import Colors
import numpy as np
import soundfile as sf

async def send_tts_request(session, text, index):
    url = "http://localhost:5002/tts"
    data = {
        "text": text,
        "index": index,
    }
    
    try:
        print(f"请求 {index} 开始")
        start_time = time.time()
        
        # 使用 aiohttp 的异步请求
        async with session.post(url, json=data) as response:
            if response.status == 200:
                # 读取采样率(2字节)
                sr_bytes = await response.content.read(4)
                if len(sr_bytes) != 4:
                    raise ValueError("无法读取采样率")
                sr = struct.unpack('!I', sr_bytes)[0]
                print(f"{Colors.RED}采样率:{sr} {Colors.ENDC}")
                # 读取数据长度(4字节)
                data_len_bytes = await response.content.read(4)
                if len(data_len_bytes) != 4:
                    raise ValueError("无法读取数据长度")
                data_len = struct.unpack('!I', data_len_bytes)[0]
                print(f"{Colors.RED}数据长度:{data_len} {Colors.ENDC}")
                # 读取音频数据
                audio_bytes = await response.content.read(data_len)
                print(f"{Colors.RED}audio_bytes长度: {len(audio_bytes)} {Colors.ENDC}")
                # 转换为numpy数组
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                
                print(f"采样率:{sr}, 数据长度:{audio_data.shape}")
                return audio_data, sr

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
                total_length = header['total_length']
                
                # 读取音频数据
                audio_bytes = bytearray()
                async for chunk in response.content:
                    audio_bytes.extend(chunk)
                
                # 转换为numpy数组
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                sf.write(f"stream_output_wav/chunk_{index}.wav", audio_data, sr)
                return index, audio_data, sr
                
    except Exception as e:
        print(f"请求 {index} 发生错误: {str(e)}")
        return None
    
async def process_stream(queue, pending_tasks): 
    """处理结果队列"""
    while True:
        start_time = time.time()
        try:
            result = await queue.get()
            if result is None:  # 结束信号
                # 确保所有任务都完成
                if pending_tasks:
                    print(f"等待 {len(pending_tasks)} 个未完成的任务...")
                    await asyncio.gather(*pending_tasks)
                break
            print(f"sr: {result[2]}")
            queue.task_done()
            
        except Exception as e:
            print(f"处理结果时出错: {e}")

async def process_text_stream(text_stream, session, result_queue):
    """处理文本流，发送请求"""
    pending_tasks = set()
    index = 1
    
    try:
        async for text in text_stream:
            print(f"发送请求 {index}")
            task = asyncio.create_task(send_tts_request_by_chunk(session, text, index))
            pending_tasks.add(task)
            
            # 设置回调来处理完成的任务
            def done_callback(t, task=task):
                pending_tasks.discard(task)
                if t.exception() is None and t.result() is not None:
                    
                    asyncio.create_task(result_queue.put(t.result()))
            
            task.add_done_callback(done_callback)
            
            # 等待 0.2 秒再发送下一个
            await asyncio.sleep(0.01)
            index += 1
        
        # 等待所有任务完成
        if pending_tasks:
            print(f"等待 {len(pending_tasks)} 个任务完成...")
            await asyncio.gather(*pending_tasks)
            
    finally:
        # 发送结束信号
        await result_queue.put(None)
        return pending_tasks
    
async def main(ans):
    # 确保输出目录存在
    os.makedirs("stream_output_wav", exist_ok=True)
    
    start_time = time.time()
    result_queue = asyncio.Queue()
    
    async with aiohttp.ClientSession() as session:  #session会话对象，可发送请求、可复用、保持连接，用于异步
        # 处理文本流并获取未完成的任务
        pending_tasks = await process_text_stream(ans, session, result_queue)
        
        # 创建结果处理任务
        process_task = asyncio.create_task(process_stream(result_queue, pending_tasks))
        
        # 等待结果处理完成
        await process_task
    
    end_time = time.time()
    print(f"\n总耗时: {end_time - start_time:.2f} 秒")

if __name__ == "__main__":
    while True:
        question = input("请输入问题:")
        ans = get_llm_stream(question,"1")
        asyncio.run(main(ans))
        print("--------------------------------")
    


