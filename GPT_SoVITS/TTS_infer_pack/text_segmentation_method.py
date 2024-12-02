



import re
from typing import Callable

punctuation = set(['!', '?', '…', ',', '.', '-'," "])
METHODS = dict()

def get_method(name:str)->Callable:
    method = METHODS.get(name, None)
    if method is None:
        raise ValueError(f"Method {name} not found")
    return method

def get_method_names()->list:
    return list(METHODS.keys())

def register_method(name):
    def decorator(func):
        METHODS[name] = func
        return func
    return decorator

splits = {"，", "。", "？", "！", ",", ".", "?", "!", "~", ":", "：", "—", "…", }

def split_big_text(text, max_len=510):
    # 定义全角和半角标点符号
    punctuation = "".join(splits)

    # 切割文本
    segments = re.split('([' + punctuation + '])', text)
    
    # 初始化结果列表和当前片段
    result = []
    current_segment = ''
    
    for segment in segments:
        # 如果当前片段加上新的片段长度超过max_len，就将当前片段加入结果列表，并重置当前片段
        if len(current_segment + segment) > max_len:
            result.append(current_segment)
            current_segment = segment
        else:
            current_segment += segment
    
    # 将最后一个片段加入结果列表
    if current_segment:
        result.append(current_segment)
    
    return result



def split(todo_text):
    todo_text = todo_text.replace("……", "。").replace("——", "，")
    if todo_text[-1] not in splits:
        todo_text += "。"
    i_split_head = i_split_tail = 0
    len_text = len(todo_text)
    todo_texts = []
    while 1:
        if i_split_head >= len_text:
            break  # 结尾一定有标点，所以直接跳出即可，最后一段在上次已加入
        if todo_text[i_split_head] in splits:
            i_split_head += 1
            todo_texts.append(todo_text[i_split_tail:i_split_head])
            i_split_tail = i_split_head
        else:
            i_split_head += 1
    return todo_texts


# 不切
@register_method("cut0")
def cut0(inp):
    if not set(inp).issubset(punctuation):
        return inp
    else:
        print("cut0,INP:",inp)
        return inp


# 凑四句一切
@register_method("cut1")
def cut1(inp):
    inp = inp.strip("\n")
    inps = split(inp)
    split_idx = list(range(0, len(inps), 4))
    split_idx[-1] = None
    if len(split_idx) > 1:
        opts = []
        for idx in range(len(split_idx) - 1):
            opts.append("".join(inps[split_idx[idx]: split_idx[idx + 1]]))
    else:
        opts = [inp]
    opts = [item for item in opts if not set(item).issubset(punctuation)]
    return "\n".join(opts)


# 凑50字一切
@register_method("cut2")
def cut2(inp):
    inp = inp.strip("\n")
    inps = split(inp)
    if len(inps) < 2:
        return inp
    opts = []
    summ = 0
    tmp_str = ""
    for i in range(len(inps)):
        summ += len(inps[i])
        tmp_str += inps[i]
        if summ > 50:
            summ = 0
            opts.append(tmp_str)
            tmp_str = ""
    if tmp_str != "":
        opts.append(tmp_str)
    # print(opts)
    if len(opts) > 1 and len(opts[-1]) < 50:  ##如果最后一个太短了，和前一个合一起
        opts[-2] = opts[-2] + opts[-1]
        opts = opts[:-1]
    opts = [item for item in opts if not set(item).issubset(punctuation)]
    return "\n".join(opts)

# 按中文句号。切
@register_method("cut3")
def cut3(inp):
    inp = inp.strip("\n")
    opts = ["%s" % item for item in inp.strip("。").split("。")]
    opts = [item for item in opts if not set(item).issubset(punctuation)]
    return "\n".join(opts)

#按英文句号.切
@register_method("cut4")
def cut4(inp):
    inp = inp.strip("\n")
    opts = ["%s" % item for item in inp.strip(".").split(".")]
    opts = [item for item in opts if not set(item).issubset(punctuation)]
    return "\n".join(opts)

# 按标点符号切
# contributed by https://github.com/AI-Hobbyist/GPT-SoVITS/blob/main/GPT_SoVITS/inference_webui.py
@register_method("cut5")
def cut5(inp):
    inp = inp.strip("\n")
    punds = {',', '.', ';', '?', '!', '、', '，', '。', '？', '！', ';', '：', '…'}
    mergeitems = []
    items = []

    for i, char in enumerate(inp):
        if char == "\n":
            continue
        if char in punds:
            if char == '.' and i > 0 and i < len(inp) - 1 and inp[i - 1].isdigit() and inp[i + 1].isdigit():
                items.append(char)
            else:
                items.append(char)
                mergeitems.append("".join(items))
                items = []
        else:
            items.append(char)

    if items:
        mergeitems.append("".join(items))

    opt = [item for item in mergeitems if not set(item).issubset(punds)]
    return "\n".join(opt)



if __name__ == '__main__':
    method = get_method("cut5")
    sentences = method("""大家好，欢迎来到我们的直播间，我是你们的好朋友！今天给大家带来的不仅仅是一双拖鞋，而是一种全新的舒适体验——我们的女士拖鞋舒适鞋！这绝对不是普通的拖鞋，它将时尚与舒适完美结合，让你的每一次步行都充满愉悦与自信。

首先，让我们来聊聊这款拖鞋的独特设计。它采用了引人注目的色块图案，非常时尚大方。这种设计不仅让你在家中轻松漫步时显得与众不同，也让你在外出散步时成为众人瞩目的焦点。这款拖鞋能够轻松搭配各种服装风格，无论你是休闲风还是时尚风，它都能为你的整体造型增添一抹亮色。

接下来，我们来谈谈舒适度。女士拖鞋舒适鞋的鞋底采用了柔软舒适的材质，无论你走多久都不会感到压力。鞋底的设计不仅支撑良好，还能有效缓解长时间步行带来的疲劳感。试想一下，当你结束一天的工作或购物之后，回到家可以换上这样一双舒适的拖鞋，那种放松的感觉是多么美妙。

此外，这款拖鞋的材质也是一大亮点。它使用了防滑耐磨的优质材料，确保你的每一步都安全可靠。无论是瓷砖地板还是木地板，这款拖鞋都能提供出色的抓地力，防止意外滑倒的发生。耐磨的材质还保证了拖鞋的使用寿命，让你在日常生活中无后顾之忧。

最后，不得不提的是它的轻便易携特性。这款拖鞋不仅重量轻，而且非常容易携带。无论是旅行、健身房还是日常外出，它都能成为你的贴心伴侣。轻便的设计让你在任何场合都能轻松自如地行走。

现在，我知道大家已经迫不及待想要拥有这样一双完美的拖鞋了。好消息是，今天我们直播间特别推出618大促活动，春季焕新季！现在购买两件商品，不仅享受直播间专属优惠价格，还能免费获得第三件，机会不容错过，赶快下单焕新你的春季衣橱吧！女士拖鞋舒适鞋是一款集时尚、舒适、安全、便携于一身的优秀产品。无论是作为自用还是送给亲友，这款拖鞋都是一个绝佳的选择。点击屏幕下方的购买链接，立刻将它带回家。数量有限，先到先得哦！赶紧行动起来，让我们一起走出舒适，走出时尚！
    """)
    sentences = sentences.strip("\n")
    sentences = sentences.split("\n")
    # 判断每个句子是否全是空字符
   
    if not sentences[-1].strip():  # 如果去掉空格后为空字符串，说明全是空字符
        print(f"句子 '{sentences[-1]}' 全是空字符")
    else:
        print(f"句子: {sentences[-1]}")
    