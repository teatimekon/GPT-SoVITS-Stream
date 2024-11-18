from flask import Flask, send_file
import os
import time
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAV_DIR = os.path.join(BASE_DIR, "stream_output_wav")
print(WAV_DIR)  
# 确保输出目录存在
os.makedirs(WAV_DIR, exist_ok=True)

app = Flask(__name__)

@app.route('/audio/<filename>')
def serve_audio(filename):
    try:
        file_path = os.path.join(WAV_DIR, filename)
        if not os.path.exists(file_path):
            return f"文件不存在: {file_path}", 404
        return send_file(file_path, mimetype="audio/wav")
    except Exception as e:
        return f"错误: {str(e)}", 404

@app.route('/current')
def get_current_file():
    try:
        files = os.listdir(WAV_DIR)
        if not files:
            return "没有找到文件", 404
        files = [f for f in files if f.endswith('.wav')]  # 只列出 wav 文件
        if not files:
            return "没有找到 wav 文件", 404
        files.sort()
        return files[0]
    except Exception as e:
        return f"错误: {str(e)}", 404
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)