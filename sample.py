# -*- coding: utf-8 -*-
import asyncio
import random
import blivedm


import requests
import argparse
from flask import Flask, request, jsonify
import logging
import json
import sys

import json
from datetime import datetime
import queue
import argparse
import threading

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
app = Flask(__name__)






# 创建一个队列
message_queue = queue.Queue()


def addMessage(order,command,sender,message):
    #     # 模拟发送者和消息内容
    # sender = "Alice"
    # message = "Hello, world!"
    # print("addMessage")

    # 获取当前时间
    date_time = datetime.now()
    current_time = date_time.strftime("%Y-%m-%d %H:%M:%S")

    # 构建包含发送者和发送时间字段的字典
    message_dict = {
        "command":command,
        "sender": sender,
        "message": message,
        "send_time": current_time,
        "date_time": date_time.toordinal(),
        "order":order
    }

    # 将字典转换为JSON字符串
    # message_json = json.dumps(message_dict)
    # print(message_json)

    # 将JSON字符串添加到队列中
    message_queue.put(message_dict)

def popMessage():
    # 从队列中获取消息
    received_dict  = message_queue.get()
    return received_dict




# 直播间ID的取值看直播间URL
TEST_ROOM_IDS = [
    13459394,
    27771611,
]


async def main():
    # await run_single_client()
    await run_multi_clients()


async def run_single_client():
    """
    演示监听一个直播间
    """
    room_id = random.choice(TEST_ROOM_IDS)
    # 如果SSL验证失败就把ssl设为False，B站真的有过忘续证书的情况
    client = blivedm.BLiveClient(room_id, ssl=True)
    handler = MyHandler()
    client.add_handler(handler)

    client.start()
    try:
        # 演示5秒后停止
        await asyncio.sleep(5)
        client.stop()

        await client.join()
    finally:
        await client.stop_and_close()


async def run_multi_clients():
    """
    演示同时监听多个直播间
    """
    clients = [blivedm.BLiveClient(room_id) for room_id in TEST_ROOM_IDS]
    handler = MyHandler()
    for client in clients:
        client.add_handler(handler)
        client.start()

    try:
        await asyncio.gather(*(
            client.join() for client in clients
        ))
    finally:
        await asyncio.gather(*(
            client.stop_and_close() for client in clients
        ))


class MyHandler(blivedm.BaseHandler):
    # # 演示如何添加自定义回调
    # _CMD_CALLBACK_DICT = blivedm.BaseHandler._CMD_CALLBACK_DICT.copy()
    #
    # # 入场消息回调
    # async def __interact_word_callback(self, client: blivedm.BLiveClient, command: dict):
    #     print(f"[{client.room_id}] INTERACT_WORD: self_type={type(self).__name__}, room_id={client.room_id},"
    #           f" uname={command['data']['uname']}")
    # _CMD_CALLBACK_DICT['INTERACT_WORD'] = __interact_word_callback  # noqa

    async def _on_heartbeat(self, client: blivedm.BLiveClient, message: blivedm.HeartbeatMessage):
        print(f'[{client.room_id}] 当前人气值：{message.popularity}')

    async def _on_danmaku(self, client: blivedm.BLiveClient, message: blivedm.DanmakuMessage):
        addMessage(10,"message",message.uname,message.msg)
        print(f'[{client.room_id}] {message.uname}：{message.msg}')

    async def _on_gift(self, client: blivedm.BLiveClient, message: blivedm.GiftMessage):
        addMessage(2,"gift_send",message.uname,message.gift_name)
        print(f'[{client.room_id}] {message.uname} 赠送{message.gift_name}x{message.num}'
              f' （{message.coin_type}瓜子x{message.total_coin}）')

    async def _on_buy_guard(self, client: blivedm.BLiveClient, message: blivedm.GuardBuyMessage):
        addMessage(1,"gift_buy",message.uname,message.gift_name)
        print(f'[{client.room_id}] {message.username} 购买{message.gift_name}')

    async def _on_super_chat(self, client: blivedm.BLiveClient, message: blivedm.SuperChatMessage):
        addMessage(5,"super_message",message.uname,message.message)
        print(f'[{client.room_id}] 醒目留言 ¥{message.price} {message.uname}：{message.message}')



@app.route('/', methods=['GET'])
def forward_request_get():
    # return "hello world"
    # message_dict = popMessage()
    # # 将字典转换为JSON字符串
    # message_json = json.dumps(message_dict)
    # return message_json
    
    # 弹出并封装消息
    messages = []
    count = 0
    while not message_queue.empty() and count<10:
        message = message_queue.get()
        messages.append(message)
    
    blivedm_dict = {
        "messages":messages,
    }

    # 将消息封装成JSON数组
    json_blivedm = json.dumps(blivedm_dict)
    # 打印JSON数组
    # print(json_array)
    return json_blivedm


@app.route('/', methods=['POST'])
def forward_request():
    request_data = request.json

    # headers = {'Content-Type': 'application/json', 'Authorization': request.headers.get('Authorization')}
    # logging.info(request_data)
    # response = requests.post('https://api.openai.com/v1/chat/completions', json=request_data,headers=headers)
    # logging.info(response.json())
    # return jsonify(response.json())


# 启动Flask应用的函数
def run_flask_app(args):
    # 将命令行参数传递给app.run()方法
    try:
        # 将命令行参数传递给app.run()方法
        app.run(port=args.port)
    except KeyboardInterrupt:
        # 执行清理操作（如果有需要）
        pass
    # 继续执行后续代码
    print("后续代码运行中...")

def runWeb():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Start a Flask server.')
    parser.add_argument('--port', type=int, default=8000, help='Port number to use for the server.')
    args = parser.parse_args()

    # 在单独的线程中启动Flask应用，并传递args参数
    flask_thread = threading.Thread(target=run_flask_app, args=(args,))
    flask_thread.start()


if __name__ == '__main__':
    runWeb()
    asyncio.run(main())
