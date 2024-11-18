import gradio as gr
import time

def say_hello(text):
    print("hello")
    time.sleep(1)
    return "完成!"

with gr.Blocks() as demo:
    btn = gr.Button(value="点击我")
    btn.click(say_hello, inputs=gr.Textbox(value="1"))
    

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7863)
