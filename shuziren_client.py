import numpy as np
import gradio as gr
import requests
import soundfile as sf
import io
from pydub import AudioSegment
import time
import uuid
def process_audio_stream(question, request_id):

    
    url = "http://localhost:5006/chat"
    data = {
        "question": question,
        "request_id": request_id
    }
    
    try:
        response = requests.post(url, json=data, stream=True)
        
        if response.status_code == 200:
            # 用于收集所有音频数据
            all_audio_data = bytearray()
            
            for chunk in response.iter_content(chunk_size=32000):
                if chunk:
                    # 确保采样率匹配（这里假设是32000）
                    start_time = time.time()
                    print(f"收到 chunk: {len(chunk)}")
                    
                    audio_chunk = np.frombuffer(chunk, dtype=np.int16)
                    yield (32000,audio_chunk)
                    
                    end_time = time.time()
                    print(f"处理时间: {end_time - start_time}秒")
                    
                    all_audio_data.extend(chunk)
            yield (32000,np.array([],dtype=np.int16))
            # 保存完整的音频文件
            audio_data = np.frombuffer(all_audio_data, dtype=np.int16)
            sf.write("output.wav", audio_data, 32000)
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        yield None

def get_oral_audio_path(text, request_id):
    url = "http://localhost:5006/tts"
    data = {
        "text": text,
        "request_id": request_id
    }
    
    try:
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            print(f"收到tts响应: {response.content.decode('utf-8')}")
            return response.content.decode('utf-8')
        else:
            return None
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None

def test_audio_stop():
    print("audio_question音频播放完结")

def show_interrupt_button():
    print("显示打断按钮")
    return gr.update(visible=True)

def hide_interrupt_button():
    print("隐藏打断按钮")
    return gr.update(visible=False)

def play_or_pause_oral_audio():
    print("播放或暂停口播音频")
    return """function() {
        var audioPlayer = document.querySelector('#oral_audio_player');
        if (audioPlayer) {
            const playPauseButton = audioPlayer.querySelector('.play-pause-button');
            playPauseButton.click();
        }
    }"""

def kill_request(request_id):
    url = "http://localhost:5006/kill"
    data = {
        "request_id": request_id
    }
    requests.get(url, params=data)

def generate_content(goods_name, goods_point, activity, benefit, target_people, user_point, style):
    url = "http://183.131.7.9:8003/api/application/68b32f0e-64e2-11ef-977b-26cf8447a8c9/content_generate"
    
    data = {
        "goods_name": goods_name,
        "goods_point": goods_point,
        "activity": activity,
        "benefit": benefit,
        "target_people": target_people,
        "user_point": user_point,
        "style": style
    }
    return """亲爱的女士们，欢迎来到我们的直播间。在这个充满节奏的现代生活中，时尚不仅是一种生活方式，更是一种自信的表达。"""
    return """亲爱的女士们，欢迎来到我们的直播间。在这个充满节奏的现代生活中，时尚不仅是一种生活方式，更是一种自信的表达。今天，我们要为大家带来的，是一款能够在日常生活中为您增添一抹现代时尚的单品——女士拖鞋舒适鞋。这不仅是一双鞋，更是您的时尚宣言，是您在每一步中彰显个性与魅力的利器。想象一下，在色彩斑斓的城市街头，每一步都能为您的整体造型增添亮丽色彩。今天，让我们一同探索这双鞋如何成为您生活中的时尚伴侣。
    首先，我们来细细品味这款女士拖鞋的外观设计。这双鞋的色块图案和大胆的色彩组合，绝对会让您一见钟情。每一个图案都像是一幅现代艺术作品，经过精心设计，色彩的拼接不仅仅是视觉上的享受，更是一种艺术的呈现。这样的设计不仅让鞋子本身成为焦点，更让您无论在什么场合都能自信满满，成为众人瞩目的焦点。这是一种无法忽视的时尚魅力，让每一个穿着者都能感受到设计师对现代时尚的理解与诠释。
    接下来，我们要谈谈这双拖鞋的百搭性。无论您是去参加一个轻松的朋友聚会，还是出席一场正式的商务会议，这双拖鞋都能轻松驾驭。您可以搭配牛仔裤、短裙，甚至是正式的西装，它都能为您的造型增添一抹亮色。这样的百搭特性为爱时尚的您提供了更多的搭配选择，不需要花费太多时间在搭配上，就能轻松出门，展现出您与众不同的个人风格。
    当然，美观只是这款拖鞋的一个方面，舒适性同样不容忽视。这双鞋的设计充分考虑了日常步行的舒适性，让您在逛街、上班或者参加聚会时，双脚始终保持轻松和舒适。耐穿的材质确保了长时间使用也依然如新，是每位追求品质生活女性的理想选择。它是您衣橱中不可或缺的单品，让您在每一步中都能感受到舒适与时尚的完美结合。
    亲爱的朋友们，现在是心动时刻！我们的618大促活动已经正式开启，现在下单，不仅可以享受直播间专属优惠价，还能体验任意两件商品购买，第三件免费带回家的活动。如此超值的优惠，让这个春季焕然一新！这款女士拖鞋专为年轻女性设计，结合时尚与舒适，是您在日常步行中的最佳选择。千万不要错过这个让您时尚与舒适并存的机会，赶紧下单，体验这款拖鞋给您带来的无限魅力吧！
    """
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            data = response.json()['data']
            # 从返回的json中提取contents列表
            contents = data.get('contents', [])
            # 按rank排序并合并所有content
            sorted_contents = sorted(contents, key=lambda x: x['rank'])
            combined_content = '\n'.join(item['content'] for item in sorted_contents)
            print(combined_content)
            return combined_content
        else:
            return f"请求失败: {response.status_code}"
    except Exception as e:
        return f"发生错误: {str(e)}"

with gr.Blocks() as demo:
    # 添加一个隐藏的文本框来存储request_id
    request_id_box_for_oral_audio = gr.Textbox(visible=False)
    request_id_box_for_chat = gr.Textbox(visible=False)
    with gr.Row():
        with gr.Column(scale=1):
            goods_name = gr.Textbox(label="商品名称",value="女士拖鞋舒适鞋日常步行")
            goods_point = gr.Textbox(label="商品卖点",value="1.引人注目的色块图案。2.充满活力和大胆的色彩组合。为任何服装增添现代和时尚的色彩。在不同的色调之间创造一种视觉上吸引人的对比。对于那些喜欢用自己的时尚选择来表达自己的人来说，这是完美的选择。提升你的整体风格，为你的外表增添一抹亮色。百搭设计，可在各种场合佩戴。适合休闲和正式场合。很容易与其他衣橱必备单品混搭。时尚收藏中必备的一款。")
            activity = gr.Textbox(label="活动",value="618大促,春季焕新")
            benefit = gr.Textbox(label="优惠信息",value="买二送一，直播间优惠价格")
            target_people = gr.Textbox(label="目标人群",value="年轻女性")
            user_point = gr.Textbox(label="用户关注点",value="耐穿")
            style = gr.Radio(label="风格", choices=[1, 2, 3], value=1)
            generate_btn = gr.Button("生成内容")
            
        with gr.Column(scale=1):
            output_text = gr.Textbox(label="生成的口播文本",lines=16,max_lines=16)
            oral_audio = gr.Audio(label="音频播放",elem_id="oral_audio_player", type="filepath",loop=True,autoplay=True)
            test_audio_btn_interrupt = gr.Button("暂停口播 / 播放口播")
        
    with gr.Row():
        with gr.Column(): 
            msg = gr.Textbox(value="1", label="问题")
        with gr.Column():
            audio_chat = gr.Audio(
                streaming=True,
                autoplay=True,
                label="音频输出"
            )

    test_audio_btn_interrupt.click(
        fn=lambda: None,
        js=play_or_pause_oral_audio()
    )
    # 生成口播内容音频，然后等待 1.请求 maxkb 接口获得口播内容 2.请求 tts 接口获得音频数据 3.播放音频
    generate_btn.click(
        # 生成口播内容
        fn=generate_content,
        inputs=[goods_name, goods_point, activity, benefit, target_people, user_point, style],
        outputs=[output_text]
    ).then( 
        # trick 生成新的request_id
        fn=lambda: str(uuid.uuid4()),  # 生成新的request_id
        outputs=request_id_box_for_oral_audio
    ).then(
        # 获取口播音频
        fn=get_oral_audio_path,
        inputs=[output_text, request_id_box_for_oral_audio],  # 使用request_id_box替代直接的字符串
        outputs=[oral_audio]
    )

    btn_play = gr.Button("播放")
    btn_interrupt = gr.Button("打断", visible=False)
    
    btn_play.click(
        fn=lambda: str(uuid.uuid4()),
        outputs=request_id_box_for_chat
    ).then(
        process_audio_stream, 
        inputs=[msg, request_id_box_for_chat], 
        outputs=[audio_chat]  
    ).then(
        fn= lambda: None,
        js=play_or_pause_oral_audio()
    )
    # 音频播放完结
    audio_chat.stop(
        fn=test_audio_stop,
        js=play_or_pause_oral_audio()
    )
    
    # 添加pause事件处理
    audio_chat.pause(
        fn=lambda: None,
        js=play_or_pause_oral_audio()
    )
    
    # 添加play事件处理 
    audio_chat.play(
        fn=lambda: None,
        js=play_or_pause_oral_audio()
    )

    btn_play.click(
        show_interrupt_button,
        outputs=[btn_interrupt]
    )
    btn_interrupt.click(
        kill_request,
        inputs=[request_id_box_for_chat],
        outputs=[]
    ).then(
        hide_interrupt_button,
        outputs=[btn_interrupt]
    )
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7862, debug=True)
