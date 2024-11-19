import gradio as gr
import time

def say_hello(text):
    print(f"调用了 hello 接口: {text}")
    time.sleep(1)
    return f"Hello! 你说了: {text}"

def say_bye(text):
    print(f"调用了 bye 接口: {text}")
    time.sleep(1)
    return f"Bye! 你说了: {text}"

def calculate(num1, num2):
    print(f"调用了计算接口: {num1} + {num2}")
    return float(num1) + float(num2)

with gr.Blocks() as demo:
    # hello 接口
    with gr.Tab("Hello"):
        text_input1 = gr.Textbox(value="", label="输入文本")
        btn1 = gr.Button(value="说 Hello")
        output1 = gr.Textbox(label="输出结果")
        btn1.click(say_hello, inputs=text_input1, outputs=output1)
    
    # bye 接口
    with gr.Tab("Bye"):
        text_input2 = gr.Textbox(value="", label="输入文本")
        btn2 = gr.Button(value="说 Bye")
        output2 = gr.Textbox(label="输出结果")
        btn2.click(say_bye, inputs=text_input2, outputs=output2)
    
    # 计算接口
    with gr.Tab("计算"):
        num1 = gr.Number(label="数字1")
        num2 = gr.Number(label="数字2")
        btn3 = gr.Button(value="计算")
        output3 = gr.Number(label="结果")
        btn3.click(calculate, inputs=[num1, num2], outputs=output3)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7861)
