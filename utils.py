import requests
import json
import time
import aiohttp

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GREY = '\033[90m'


async def get_llm_stream(question: str, conv_id: str):
    url = "http://127.0.0.1:5001/stream"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    payload = json.dumps({
        "question": question, 
        "conversation_id": conv_id
    })
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers,data=payload) as response:
            if response.status == 200:
                start_time = time.time()
                async for sentence in process_stream_response(response, start_time):
                    yield sentence
            else:
                print(f"请求失败: {response.status}")
                print(await response.text())
                print("-" * 50)

async def process_stream_response(response, start_time):
    """处理流式响应数据，按句子输出"""
    PUNCTUATION_MARKS = frozenset(',;?!、，。？！；：…~:')
    
    async def process_line(line: str) -> str:
        """处理单行数据"""
        if line == '\n':
            return "\n"
        if not line.startswith('data: '):
            return ""
        # 移除 "data: " 前缀和最后一个换行符    
        return line[6:-1]

    current_sentence = []
    is_processing_data = True # 是否是正确的响应，从第一个开始是，再下一个不是，再下一个是。。依次循环
    async for line in response.content:
        
        if not is_processing_data:
            # \n杂项，跳过，并开始处理 data
            is_processing_data = True
            continue
        
        if line.decode('utf-8').startswith("data: "):
            # 遇到data: 开头，代表下一个必定是\n杂项
            is_processing_data = False
        
        """
        data可能的格式及处理方法：
        1. 空字符串：代表一小段话结尾，要处理成句子
        2. 换行符：代表一小段话结尾，要处理成句子
        3. 其他字符串：代表一小段话未结束，要继续拼接
        """
        print(f"{Colors.RED}{line}{Colors.ENDC}")
        content = await process_line(line.decode('utf-8'))
        print("content",content,"len",len(content))
        for char in content:
            if char != "\n" :
                current_sentence.append(char)
                
            # 当遇到标点符号时，输出完整句子
            if (char in PUNCTUATION_MARKS) or (char == "\n"):
                complete_sentence = ''.join(current_sentence)
                elapsed_time = time.time() - start_time
                current_sentence = []  # 清空当前句子缓存
                #如果整个句子全是符号，则跳过
                if set(complete_sentence).issubset(PUNCTUATION_MARKS.union("\n").union(" ")):
                    print("全是符号，跳过")
                    continue
                if len(complete_sentence) > 0:
                    print("complete_sentence:",complete_sentence,"len",len(complete_sentence))
                    yield complete_sentence
    if current_sentence:
        print("最后的句子",current_sentence)
        yield ''.join(current_sentence)


def get_rag_stream(question: str):
    application_id = "cef470c6-603b-11ef-87f1-26cf8447a8c9"
    conversation_id = get_rag_conversation_id(application_id)
    conversation_id = conversation_id.json()["data"]
    message = send_chat_message(question, conversation_id, application_id)
    
    return message

def get_rag_conversation_id(application_id):
    url = f'http://0.0.0.0:8085/api/application/{application_id}/chat/open'
    auth_token = "eyJ1c2VybmFtZSI6ImFkbWluIiwiaWQiOiJmMGRkOGY3MS1lNGVlLTExZWUtOGM4NC1hOGExNTk1ODAxYWIiLCJlbWFpbCI6IiIsInR5cGUiOiJVU0VSIn0:1t8xtC:JfOV5571AAnlSzlpnglNIv9XTcx2456TXJ9ITHL8UWA"
    headers = {
        'AUTHORIZATION': auth_token,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    return requests.get(url, headers=headers, verify=False)

def send_chat_message(message, chat_uuid, application_id):
    url = f'http://0.0.0.0:8085/api/application/chat_message/{chat_uuid}'
    headers = {
        'AUTHORIZATION': f"application-{application_id}",
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }

    data = {
        "message": message,
        "re_chat": False,
        "stream": False
    }

    return requests.post(url, headers=headers, json=data, verify=False)

def call_maxkb_api(question: str):
    api_key = "application-f9bd7e9a307f4cb9bd96cd90bcd0fd1c"
    base_url = "http://183.131.7.9:8003/api/application/cef470c6-603b-11ef-87f1-26cf8447a8c9/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "你是杭州飞致云信息科技有限公司旗下产品 MaxKB 知识库问答系统的智能小助手，你的工作是帮助 MaxKB 用户解答使用中遇到的问题，用户找你回答问题时，你要把主题放在 MaxKB 知识库问答系统身上。",
                "content": question
            }
        ],
        "stream": True
    }
    return requests.post(base_url, headers=headers, json=data,stream=True)

if __name__ == "__main__":
    # ans = get_llm_stream("你好，我是胡桃，我是请求 1","1")
    # for chunk in ans:
    #     print(chunk, end='\n', flush=True)
    # res = get_rag_stream(question="1")
    # print(res)
    # ans = call_maxkb_api(question="你好")
    # for res in ans.iter_content(chunk_size=1024):
    #     print(res)
    from nltk.book import *



