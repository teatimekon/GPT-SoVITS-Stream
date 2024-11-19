import os
from gradio_client import Client
from tools.i18n.i18n import I18nAuto
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
client = Client("http://127.0.0.1:9873")
i18n = I18nAuto("Auto")
# 使用 client.upload() 上传文件
audio_path = "input_audio.wav"

tmp_path = "/tmp/gradio/"
uploaded_audio = {
    "path": tmp_path + audio_path,
}
inputs = {
    "text": "早上好",
    "text_lang": i18n("中文"),
    "top_k": 5,
    "top_p": 1.0,
    "temperature": 1,
    "ref_audio_path": uploaded_audio,
    "aux_ref_audio_paths": [],
    "prompt_text": "那不好意思打扰您了，如果您后期有网站建设的需求呢，可以拨打4008883324",
    "prompt_lang": i18n("中文"),
    "speed_factor": 1.0,
    "ref_text_free": False,
    "split_bucket": True,
    "fragment_interval": 0.5,
    "seed": -1,
    "keep_random": True,
    "api_name": "/inference"
}

texts = [
    "今天天气真不错，阳光明媚。",
    "我最近在学习一门新的编程语言。",
    "周末我打算去公园散步。",
    "这家餐厅的菜品味道很好。",
    "明天下午我要去参加一个重要会议。",
    "你有没有看过最新上映的那部电影？",
    "我家楼下新开了一家便利店。",
    "春天来了,花园里的花都开了。",
    "这本书的内容很有意思。",
    "我们下周要去郊游。"
]
def single_predict(i):
    try:
        inputs["text"] = texts[i]
        print(f"send inputs {i}")
        start = time.time()
        result = client.predict(**inputs)
        end = time.time()
        print(f"result {i} finished in {end - start} seconds")
        # print(f"result {i}", result)
        return result
    except Exception as e:
        print(f"Error in prediction {i}: {str(e)}")
        return None

# 使用线程池并行处理
with ThreadPoolExecutor(max_workers=10) as executor:  # 限制并发数为3
    futures = [executor.submit(single_predict, 0) for i in range(3)]
    start = time.time()
    i = 0
    for future in as_completed(futures):
        try:
            future.result()
            i += 1
        except Exception as e:
            print(f"Task failed: {str(e)}")
    end = time.time()
    print(f"Total time taken: {end - start} seconds")