#启动llm 的服务层，请求接口得到 stream 响应

lsof -i:7862 | grep python | awk '{print $2}' | xargs kill -9
lsof -i:5001 | grep python | awk '{print $2}' | xargs kill -9
lsof -i:5004 | grep python | awk '{print $2}' | xargs kill -9
lsof -i:5002 | grep python | awk '{print $2}' | xargs -I {} sh -c 'pkill -P {} && kill {}'


nohup python -u shuziren_client.py > logs/shuziren_client.log 2>&1 &        #7862

# nohup python -u tts/tts_multiprocess_server.py > logs/tts_server.log 2>&1 &    #5002

nohup python -u llm_server/Swaph/app.py > logs/llm_server.log 2>&1 &    #5001

nohup python -u tts_server/shuziren_tts_server_interrupt.py > logs/shuziren_server.log 2>&1 &    #5006