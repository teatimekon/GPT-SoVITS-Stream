#启动llm 的服务层，请求接口得到 stream 响应

nohup python -u test_gradio.py > logs/test_gradio.log 2>&1 &

nohup python -u tts/tts_multiprocess_server.py > logs/tts_server.log 2>&1 &

nohup python -u llm_server/Swaph/app.py > logs/llm_server.log 2>&1 &

nohup python -u shuziren_server_new.py > logs/shuziren_server.log 2>&1 &