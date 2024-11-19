import requests
import json
import time
import aiohttp
import asyncio
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

PUNCTUATION_MARKS = frozenset(',;?!、，。？！；：…~')

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
        content = await process_line(line.decode('utf-8'))
        for char in content:
            if char != "\n" and char not in PUNCTUATION_MARKS:
                current_sentence.append(char)

            # 当遇到标点符号时，输出完整句子
            if (char in PUNCTUATION_MARKS) or (char == "\n"):
                current_sentence.append(" ")
                complete_sentence = ''.join(current_sentence)
                elapsed_time = time.time() - start_time
                current_sentence = []  # 清空当前句子缓存
                #如果整个句子全是符号，则跳过
                if set(complete_sentence).issubset(PUNCTUATION_MARKS.union("\n").union(" ")):
                    print("全是符号，跳过")
                    continue
                if len(complete_sentence) > 0:
                    print(f"{Colors.RED}complete_sentence:{complete_sentence} len:{len(complete_sentence)}{Colors.ENDC}")
                    yield complete_sentence
    if current_sentence:
        yield ''.join(current_sentence)


async def call_maxkb_api(question: str):
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

    async with aiohttp.ClientSession() as session:
        async with session.post(base_url, headers=headers, json=data) as response:
            async for line in response.content:
                yield line.decode('utf-8')

# 添加新的异步函数来处理输出
async def get_maxkb_stream(question: str):
    current_sentence = []
    async for line in call_maxkb_api(question=question):
        if line.startswith('data: '):
            try:
                json_data = json.loads(line[6:])
                if 'choices' in json_data and json_data['choices']:
                    delta = json_data['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        for char in content:
                            if char != "\n":
                                current_sentence.append(char)
                            if char in PUNCTUATION_MARKS:
                                complete_sentence = ''.join(current_sentence)
                                current_sentence = []
                                yield complete_sentence
                                print("complete_sentence:",complete_sentence,"len",len(complete_sentence))
            except json.JSONDecodeError:
                continue


if __name__ == "__main__":
    import asyncio
    
    # 运行异步函数
    ans = get_maxkb_stream(question="如何配置 cname")
    print(ans)



