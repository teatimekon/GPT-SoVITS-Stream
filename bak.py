import gradio as gr
import subprocess
import time

# 定义后台任务（示例任务可以是一个Python脚本或其他可执行文件）
def start_background_task():
    # 启动一个子进程运行脚本
    print('start_background_task')
    process = subprocess.Popen(["python", "GPT_SoVITS/inference_webui.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)  # 可选：等待子进程启动
    return process

# Gradio接口函数
def example_function(text):
    return f"Hello, {text}!"

# 启动后台任务
background_process = start_background_task()

# 创建Gradio应用
with gr.Blocks() as demo:
    text_input = gr.Textbox(label="Enter text")
    text_output = gr.Textbox(label="Output")
    submit_button = gr.Button("Submit")
    submit_button.click(example_function, inputs=text_input, outputs=text_output)

# 启动Gradio应用
demo.launch()

# 可选：在Gradio应用结束后终止后台任务
try:
    demo.launch()
finally:
    background_process.terminate()  # 关闭后台任务
