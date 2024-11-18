import requests
import os
import numpy as np
import soundfile as sf
import time
def test_chat_api():
    # 设置API地址
    url = "http://localhost:5004/chat"
    
    # 准备测试问题
    question = "你好，请介绍一下自己"
    
    # 准备请求数据
    data = {
        "question": question
    }
    
    print(f"发送问题: {question}")
    
    try:
        # 发送POST请求并获取流式响应
        response = requests.post(url, json=data, stream=True)
        
        if response.status_code == 200:
            # 确保输出目录存在
            os.makedirs("test_output", exist_ok=True)
            output_file = "test_output/response.wav"
            
            # 用于存储所有音频数据
            all_audio_data = bytearray()
            start_time = time.time()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    # 将每个 chunk 添加到总的音频数据中
                    all_audio_data.extend(chunk)
                    
                    end_time = time.time()
                    print(f"接收到chunk，耗时: {end_time - start_time:.2f} 秒")
            end_time = time.time()
            print(f"接收到响应，耗时: {end_time - start_time:.2f} 秒")
            # 将整个累积的数据转换为 numpy array
            audio_array = np.frombuffer(all_audio_data, dtype=np.int16)
            sf.write(output_file, audio_array, 32000)
            
            print(f"音频已保存到: {output_file}")
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    test_chat_api()