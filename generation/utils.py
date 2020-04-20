#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : SMP-MCC评测会务组
# @Email  : smp_mcc@163.com
# @About  :
#   如有任何疑问，请随时联系评测会务组！
#   祝比赛顺利！

import os
import json
from tqdm import tqdm

from config import CONFIG


def load_dataset():
    """加载各主题对话数据
    :return: Dict
    {
        '电影': [],
        '数码产品': [],
        '音乐': [],
        '美食': [],
        '体育': []
    }
    """
    print('开始加载数据集...')
    data = {}
    for topic in os.listdir(CONFIG.get('DATA_DIR')):
        data[topic] = []
        topic_path = os.path.join(CONFIG.get('DATA_DIR'), topic)
        print('加载<%s>主题数据...' % topic)
        for file in tqdm(os.listdir(topic_path)):
            with open(os.path.join(topic_path, file), 'r', encoding='utf-8') as f:
                # 将文件名作为唯一标识id
                sess = json.load(f)
                sess['pid'] = file.split('.')[0]
                data[topic].append(sess)

    print('结束数据集加载....')
    return data


def preprocess(session, chunk=5, delimiter='\t', attn_title=False):
    """对话对构造
    主要方法：
        Sampling（主要对启动句的回复，以及较短间隔的回复）：
            - title（亦即楼主帖子 content）作为 **context**
            - 发帖人首次回复之前的其他人回复作为候选回复（或者是开始 **chunk** 个非楼主回复）
            - 随机选择候选回复作为 **response**
        Chunking（正常对话）:
            - 以发帖人某次回复作为分块界限
            - 将其之前对话中连续 chunk(default 5) 个回复作为 **context**
            - 将发帖人此次回复作为 **response**
            -（可以将帖子标题加入到每个 context 中，作为影响因子）
    :param session: dict
    :param chunk: integer, 分块长度
    :param delimiter: str, 对话历史拼接分隔符
    :param attn_title: boolean, 是否将帖子 title（亦即topic中content）始终拼接到 context 首部
    :return: dict
        {
            sampling: [(context1, context2,..., response)],
            chunking: [(context1, context2,..., response)]
        }
    """
    # 发帖人及其帖子
    user = session.get('topic').get('name')
    post = session.get('topic')
    post['user'] = user

    # 所有对话
    replys = session.get('replys')
    replys.insert(0, post)

    # sampling
    cands = [i for i, reply in enumerate(
        replys[:chunk]) if reply.get('user') != user]
    sampling_pairs = []
    # 帖子内容作为 context，其他用户回复作为 response
    for cand in cands:
        context = post.get('content')
        response = replys[cand].get('content')
        sampling_pairs.append([context, response])

    # chunking
    # 获得发帖人所有回复位置
    ids = [i for i, reply in enumerate(replys) if reply.get(
        'user') == user and i >= (chunk-1)]
    chunking_pairs = []
    # 当回复数大于 chunk
    if len(session.get('replys')) > chunk:
        # 发帖人回复位置为空，截取前 chunk 个回复构建 context
        if not len(ids):
            context = [r.get('content') for r in replys[:chunk]]
            response = replys[chunk].get('content')
            chunking_pairs.append(context+[response])
        # 发帖人回复位置不为空时，截取回复位置前 chunk 个回复构建 context
        else:
            for i in ids:
                start = i - chunk + 1
                context = [r.get('content') for r in replys[start:i]]
                # 是否在 context 首部拼接 title
                if attn_title and not start:
                    context = [post.get('content')] + context
                response = replys[i].get('content')
                chunking_pairs.append(context + [response])

    return {
        'sampling': sampling_pairs,
        'chunking': chunking_pairs
    }

