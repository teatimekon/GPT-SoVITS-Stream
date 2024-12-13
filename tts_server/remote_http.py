import json
from time import time
import aiohttp
import requests
from datetime import datetime


class RemoteHTTP:
    def __init__(self):
        pass

    def get_comment_from_bilibili(self, roomid="1752664819", interval=21600):
        base_url = f"https://api.live.bilibili.com/xlive/web-room/v1/dM/gethistory?roomid={roomid}"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9",
            "cookie": "buvid3=1B828E88-AC4F-DB49-3827-73745807738A67544infoc; b_nut=1725417767; _uuid=533110F79-9899-6C8D-D25F-ADDDA5ADFBA867984infoc; enable_web_push=DISABLE; home_feed_column=4; browser_resolution=1280-712; buvid_fp=72f6220d58ccc4b3902adb118254b09d; buvid4=BCE24EF7-81BE-D807-4EBD-F0CF225CC18168918-024090402-DCSBeTJsu+tYpc4MLY3O2A==; DedeUserID=325523894; DedeUserID__ckMd5=45a3853a51cdc154; CURRENT_FNVAL=4048; rpdid=|(u~JJYY)l)k0J'u~klRu~)kl; CURRENT_QUALITY=64; bsource=search_google; SESSDATA=f60aeb77%2C1748313863%2C735e6*b2CjCL_8xkaHWWlt-RcKhßrY7KG0k518OTOWbFy1cgPe0Ng7dZlxaQaMU0MkFnrd14sxNoSVjk0cHdGV0pTdmNlRmU1S2ZLYzBKRG5LUUxKUEpmeE5DRzdnaTl4NUZKVXJRYVNjS2hpV19qSUZGc29URm05RDVjNVlBZl8zeVJxY192NEtlbXV0a1hRIIEC; bili_jct=32fdb315a97563338fc5655799ab92ee; sid=fqwwm4ag; LIVE_BUVID=AUTO8017327661148108; PVID=1; Hm_lvt_8a6e55dbd2870f0f5bc9194cddf32a02=1732766135; Hm_lpvt_8a6e55dbd2870f0f5bc9194cddf32a02=1732766135; HMACCOUNT=5906BE59DF0DB634; bp_t_offset_325523894=1004714715936456704; b_lsid=71D7219D_19370FA922F",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        }
        response = requests.get(base_url, headers=headers)
        if response.status_code == 200:
            data = json.loads(response.text)
            current_time = time()
            danmu_texts = []

            for danmu in data["data"]["room"]:
                danmu_time_str = danmu.get("timeline")
                if danmu_time_str:
                    try:
                        danmu_time = datetime.strptime(
                            danmu_time_str, "%Y-%m-%d %H:%M:%S"
                        ).timestamp()
                        if current_time - danmu_time <= interval:
                            danmu_texts.append(danmu["text"])
                    except ValueError as e:
                        print(f"无法解析时间字符串: {danmu_time_str}, 错误: {e}")

            return danmu_texts
        else:
            raise Exception(f"请求失败: {response.status_code}, {response.text}")

    def choose_comment(self, goods_info, comments, choose_nums):
        url = "http://183.131.7.9:8083/api/application/68b32f0e-64e2-11ef-977b-26cf8447a8c9/choose_comment"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Referer": "http://183.131.7.9:8003/ui/application/68b32f0e-64e2-11ef-977b-26cf8447a8c9/SIMPLE/overview",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
        }
        payload = {
            "goods_info": goods_info,
            "comments": comments,
            "choose_nums": choose_nums,
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            response_data = response.json()
            return [item["content"] for item in response_data.get("data", [])]

        else:
            raise Exception(f"请求失败: {response.status_code}, {response.text}")
    def get_chat_completion(self, question):
        api_key = "application-df40f7b453cb74ee46da8dc31cc385f7"
        base_url = "http://183.131.7.9:8083/api/application/68b32f0e-64e2-11ef-977b-26cf8447a8c9/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                # {
                #     "role": "assistant",
                #     "content": "你是杭州飞致云信息科技有限公司旗下产品 MaxKB 知识库问答系统的智能小助手，你的工作是帮助 MaxKB 用户解答使用中遇到的问题，用户找你回答问题时，你要把主题放在 MaxKB 知识库问答系统身上。"
                # },
                {"role": "user", "content": question}
            ],
            "stream": False,
        }
        try:
            response = requests.post(base_url, headers=headers, json=data, timeout=10)
            print(f"response{response.text}")
            if response.status_code == 200:
                response_data = response.json()
                return (
                    response_data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
            else:
                raise Exception(f"请求失败: {response.status_code}, {response.text}")
        except requests.exceptions.Timeout:
            print("请求超时")
            return "抱歉请求超时，我无法回答您的问题"
        
    def beauty_comment(self, question, answer, style):
        url = "http://183.131.7.9:8083/api/application/68b32f0e-64e2-11ef-977b-26cf8447a8c9/beauty_comment"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Referer": "http://183.131.7.9:8003/ui/application/68b32f0e-64e2-11ef-977b-26cf8447a8c9/SIMPLE/overview",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
        }
        payload = {
            "question": question,
            "answer": answer,
            "style": style,
            # "paragraph_now": paragraph_now,
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json().get("content")  
        else:
            raise Exception(f"请求失败: {response.status_code}, {response.text}")
        
        # audio转视频

    async def audio_to_video(audio_path):
        form_data = aiohttp.FormData()
        form_data.add_field('uploaded_audio', audio_path)

        
        async with aiohttp.ClientSession() as session:
            base_url = "http://183.131.7.9:5000/generate_video"
            async with session.post(base_url, data=form_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"视频生成成功，url: {result['video_url']}")
                    return result
                else:
                    return {"error": "Failed to generate video"}
