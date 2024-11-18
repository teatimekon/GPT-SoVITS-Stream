from flask import Flask, request, Response, stream_with_context
import aiohttp
import asyncio
import json
import time
import os
from queue import Queue
from threading import Thread

app = Flask(__name__)


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
    results = []
    while True:
        try:
            result = await queue.get()
            if result is None:
                if pending_tasks:
                    await asyncio.gather(*pending_tasks)
                break
                
            results.append({
                'audio_path': result.get('audio_path'),
                'processing_time': result.get('processing_time')
            })
            queue.task_done()
            
        except Exception as e:
            print(f"处理结果时出错: {e}")
    return results

async def process_text_stream(texts, session, result_queue):
    """处理文本列表，发送请求"""
    pending_tasks = set()
    index = 1
    
    try:
        for text in texts:
            print(f"发送请求 {index}")
            task = asyncio.create_task(send_tts_request(session, text, index))
            pending_tasks.add(task)
            
            def done_callback(t, task=task):
                pending_tasks.discard(task)
                if t.exception() is None and t.result() is not None:
                    asyncio.create_task(result_queue.put(t.result()))
            
            task.add_done_callback(done_callback)
            await asyncio.sleep(0.01)
            index += 1
        
        if pending_tasks:
            await asyncio.gather(*pending_tasks)
            
    finally:
        await result_queue.put(None)
        return pending_tasks

async def process_texts(texts):
    """处理文本并返回结果"""
    os.makedirs("stream_output_wav", exist_ok=True)
    result_queue = asyncio.Queue()
    
    async with aiohttp.ClientSession() as session:
        pending_tasks = await process_text_stream(texts, session, result_queue)
        results = await process_stream(result_queue, pending_tasks)
    
    return results

@app.route('/tts_stream', methods=['POST'])
def tts_stream():
    """流式TTS接口"""
    if not request.is_json:
        return {"error": "请求必须是JSON格式"}, 400
    
    data = request.get_json()
    texts = data.get('texts', [])
    
    if not texts:
        return {"error": "texts不能为空"}, 400

    def generate():
        results = asyncio.run(process_texts(texts))
        for result in results:
            yield json.dumps(result, ensure_ascii=False) + '\n'

    return Response(
        stream_with_context(generate()),
        mimetype='application/x-ndjson'
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)