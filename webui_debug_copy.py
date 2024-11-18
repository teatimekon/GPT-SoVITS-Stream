import gradio as gr

# def second_app_interface(text):
#     return f"Welcome to the second app, {text}!"

# with gr.Blocks() as second_app:
#     text_input = gr.Textbox(label="Enter something")
#     output = gr.Textbox(label="Output")
#     text_input.change(second_app_interface, inputs=text_input, outputs=output)

# # 启动第二个 Gradio 应用，使用不同的端口
# second_app.launch(server_name="0.0.0.0", server_port=7861)

from pyinstrument import Profiler

profiler = Profiler()
profiler.start()

print('bella')

profiler.stop()
profiler.print()