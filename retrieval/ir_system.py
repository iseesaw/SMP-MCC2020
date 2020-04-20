#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : SMP-MCC评测会务组
# @Email  : smp_mcc@163.com
# @About  :
#   如有任何疑问，请随时联系评测会务组！
#   祝比赛顺利！

import os
import sys
import random

from tqdm import tqdm

from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID

from jieba.analyse import ChineseAnalyzer

from config import CONFIG
from utils import load_dataset, preprocess, load_stopwords


def run_init():
    """初始化检索系统
    """
    print('开始初始化检索系统...')
    data = load_dataset()

    # 初始化字段
    stoplist = list(load_stopwords())
    analyzer = ChineseAnalyzer(stoplist=stoplist)
    schema = Schema(
        pid=ID(stored=True),
        topic=ID(stored=True),
        method=ID(stored=True),
        context=TEXT(stored=True, analyzer=analyzer),
        response=TEXT(stored=True, analyzer=analyzer))

    # 创建索引文件保存目录
    if not os.path.exists(CONFIG.get('IR_DIR')):
        os.mkdir(CONFIG.get('IR_DIR'))
    idx = create_in(CONFIG.get('IR_DIR'), schema)

    # 构建索引
    print('开始构建索引...')
    count = {}
    writer = idx.writer()
    # 所有主题
    for topic in data:
        # 特定主题下所有帖子
        for sess in tqdm(data.get(topic)):
            pid = sess.get('pid')
            all_pairs = preprocess(sess)
            # 添加两种类型对话对 (context, response)
            for method, pairs in all_pairs.items():
                for i, pair in enumerate(pairs):
                    writer.add_document(
                        topic=topic,
                        method=method,
                        context=pair[0],
                        response=pair[1],
                        pid=f'{pid}-{method}-{i}')
                    count[method] = count.get(method, 0) + 1

    print('开始写入索引...')
    writer.commit()
    print(f'初始化成功，写入情况如下:')
    print(count)


if __name__ == '__main__':
    try:
        argv = sys.argv[1]
        if argv == 'init':
            run_init()
        elif argv == 'server':
            from ir_server import run_server
            run_server()
        else:
            print('请输入运行参数：init/server')
    except Exception as e:
        if len(sys.argv) != 2:
            print('请输入运行参数：init/server')
        else:
            print(e)
