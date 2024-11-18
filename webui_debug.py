import gradio as gr
import subprocess
import time

# 自动启动第二个 Gradio 应用
def start_second_gradio_app():
    # 使用 Popen 启动第二个 Gradio 应用脚本
    process = subprocess.Popen(["python", "webui_debug_copy.py"])
    time.sleep(1)  # 确保第二个应用有足够的时间启动
    return process

# 第一个 Gradio 应用接口函数
def main_app_interface(name):
    return f"Hello, {name}!"

# 在第一个 Gradio 应用启动前，自动启动第二个 Gradio 应用
background_process = start_second_gradio_app()

# 创建第一个 Gradio 应用
with gr.Blocks() as main_app:
    name_input = gr.Textbox(label="Enter your name")
    output = gr.Textbox(label="Output")

    # 第一个 Gradio 应用功能
    name_input.change(main_app_interface, inputs=name_input, outputs=output)

# 启动第一个 Gradio 应用
try:
    main_app.launch()
finally:
    # 退出第一个应用时，关闭第二个应用的进程
    background_process.terminate()
