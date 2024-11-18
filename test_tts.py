import aiohttp
import asyncio
import json
import time
import os

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
                result = await response.json()
                end_time = time.time()
                print(f"请求 {index} 完成，耗时: {end_time - start_time:.2f} 秒")
                return result
            else:
                print(f"请求 {index} 失败: {response.status}")
                return None
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
                
            print(f"音频路径: {result.get('audio_path')}")
            print(f"处理时间: {result.get('processing_time'):.2f} 秒")
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
            task = asyncio.create_task(send_tts_request(session, text, index))
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

async def mock_text_stream():
    """模拟文本流（用于测试）"""
    texts = [
        "你好，我是胡桃，我是请求 1",
        "你好，我是派蒙，我是一个旅行者，我来自提瓦特，我是请求 2",
        "你好，我是旅行者，我是请求 3",
        "你好，我是钟离，我是请求 4",
        "你好，我是魈，我是一个旅行者，我来自提瓦特，我是请求 5",
        "你好，我是甘雨，我是一个旅行，我是请求 6",
        "你好，我是刻晴，我是请求 7",
        "你好，我是北斗，我是请求 8",
        # ... 其他文本
    ]
    for text in texts:
        print(f"生成文本 {text}")
        yield text
        await asyncio.sleep(0.2)  # 模拟流式输入的间隔

async def main():
    # 确保输出目录存在
    os.makedirs("stream_output_wav", exist_ok=True)
    
    start_time = time.time()
    result_queue = asyncio.Queue()
    
    async with aiohttp.ClientSession() as session:  #session会话对象，可发送请求、可复用、保持连接，用于异步
        # 处理文本流并获取未完成的任务
        pending_tasks = await process_text_stream(mock_text_stream(), session, result_queue)
        
        # 创建结果处理任务
        process_task = asyncio.create_task(process_stream(result_queue, pending_tasks))
        
        # 等待结果处理完成
        await process_task
    
    end_time = time.time()
    print(f"\n总耗时: {end_time - start_time:.2f} 秒")

if __name__ == "__main__":
    asyncio.run(main())