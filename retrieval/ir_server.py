#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : SMP-MCC评测会务组
# @Email  : smp_mcc@163.com
# @About  :
#   如有任何疑问，请随时联系评测会务组！
#   祝比赛顺利！

import time
import jieba
import random

from whoosh.query import Term
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.index import open_dir

import requests
from flask import Flask, jsonify, request

from config import CONFIG

app = Flask(__name__)

# 加载索引文件
IDX = open_dir(dirname=CONFIG.get('IR_DIR'))


def search(context='你喜欢看什么电影？', topic='电影', method='sampling', limit=100, data=None, rtype='test'):
    """检索函数
    :param context: 对话历史
    :param topic: 对话主题
    :param method: 对话对构造方法
    :param limit: 返回结果个数
    """
    with IDX.searcher() as searcher:
        # 检索 context 字段
        parser = QueryParser("context", schema=IDX.schema)

        # 检索特定主题及构造方法内回复
        filterq = Term('topic', topic) & Term('method', method)

        # 检索
        q = parser.parse(context)
        results = searcher.search(q, limit=limit, filter=filterq)

        # 返回最终结果，随机topK策略
        cands = [res['response'] for res in results[:5]]

        # 如果返回结果为空并且配置了生成模块，则调用生成式模型接口（仅当群聊时）
        if not len(cands) and CONFIG.get('GEN_API'):
            try:
                reply = requests.post(CONFIG.get(
                    'GEN_API')+'/'+rtype, json=data)
                gen_res = reply.json().get('msg')
            except Exception as e:
                print(str(e))
                gen_res = '我不知道呀'
        else:
            gen_res = '我不知道呀'
            
        return random.choice(cands) if len(cands) else gen_res


@app.route("/", methods=["GET"])
def hello():
    return "Here is service for FAQ."


@app.route('/test', methods=["POST"])
def test():
    """单轮测试接口
    data = {
        content: '',
        topic: ''
    }
    """
    data = request.json
    t = time.time()

    # 检索结果返回
    msg = search(context=data.get('content'),
                 topic=data.get('topic'),
                 method='sampling',
                 data=data,
                 rtype='test')
    return jsonify({'msg': msg, 'takes': time.time() - t})


@app.route('/get_res', methods=["POST"])
def get_resp():
    """群聊接口
    data = {
        # 当前群聊唯一id
        "group_id": group_id, 
        # 当前群聊主题
        "topic": topic,
        # 您的机器人唯一id
        "robot_id": your_robot_id, 
        # 自该机器人上次回复之后的群聊消息记录
        # 按时间顺序保存
        "msgs": [
            {
                "from_id": robot_id, # 群聊机器人唯一id
                "msg": msg, # 群聊消息
                "timestamp": timestamp # 消息时间
            },
            ...
        ]
    }
    """
    # 获取群聊请求数据
    # type: json
    data = request.json

    # 对话历史
    context = '\t'.join([msg['msg'] for msg in data.get('msgs')])
    # 对应检索构造方法
    method = 'sampling' if len(data.get('msgs')) == 1 else 'chunking'
    msg = search(
        context=context,
        topic=data.get('topic'),
        method=method,
        data=data,
        rtype='get_res')

    # 返回您的机器人回复
    resp = {
        "msg": msg,
        "from_id": data["robot_id"],
        "timestamp": time.time()
    }
    return jsonify(resp)


def run_server():
    app.run(host=CONFIG.get('HOST'), port=CONFIG.get('PORT'))
