import numpy as np
import gradio as gr
import requests
import soundfile as sf
import io
from pydub import AudioSegment
import time
def numpy_to_mp3(audio_array, sampling_rate):
    # Normalize audio_array if it's floating-point
    if np.issubdtype(audio_array.dtype, np.floating):
        max_val = np.max(np.abs(audio_array))
        audio_array = (audio_array / max_val) * 32767 # Normalize to 16-bit range
        audio_array = audio_array.astype(np.int16)

    # Create an audio segment from the numpy array
    audio_segment = AudioSegment(
        audio_array.tobytes(),
        frame_rate=sampling_rate,
        sample_width=audio_array.dtype.itemsize,
        channels=1
    )

    # Export the audio segment to MP3 bytes - use a high bitrate to maximise quality
    mp3_io = io.BytesIO()
    audio_segment.export(mp3_io, format="mp3", bitrate="320k")

    # Get the MP3 bytes
    mp3_bytes = mp3_io.getvalue()
    mp3_io.close()

    return mp3_bytes

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
                    # yield numpy_to_mp3(audio_chunk, 32000)
                    yield (32000,audio_chunk)
                    
                    end_time = time.time()
                    print(f"处理时间: {end_time - start_time}秒")
                    
                    all_audio_data.extend(chunk)
            
            # 保存完整的音频文件
            audio_data = np.frombuffer(all_audio_data, dtype=np.int16)
            sf.write("output.wav", audio_data, 32000)
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        yield None
def show_interrupt_button():
    print("显示打断按钮")
    return gr.update(visible=True)

def hide_interrupt_button():
    print("隐藏打断按钮")
    return gr.update(visible=False)


def kill_request(request_id):
    url = "http://localhost:5006/kill"
    data = {
        "request_id": request_id
    }
    requests.get(url, params=data)
    
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(): 
            msg = gr.Textbox(value="1", label="问题")
            request_id = gr.Textbox(value="1", label="request_id")
        with gr.Column():
            # 设置streaming=True和autoplay=True
            audio_output = gr.Audio(
                streaming=True,
                autoplay=True,
                label="音频输出"
            )
    btn = gr.Button("播放")
    btn_interrupt = gr.Button("打断",visible=False)
    btn.click(
        process_audio_stream, 
        inputs=[msg, request_id], 
        outputs=[audio_output]
    )
    btn.click(
        show_interrupt_button,
        outputs=[btn_interrupt]
    )
    
    btn_interrupt.click(
        kill_request,
        inputs=[request_id],
        outputs=[]
    ).then(
        hide_interrupt_button,
        outputs=[btn_interrupt]
    )
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7862, debug=True)
