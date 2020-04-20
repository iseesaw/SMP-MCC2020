#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : SMP-MCC评测会务组
# @Email  : smp_mcc@163.com
# @About  :
#   如有任何疑问，请随时联系评测会务组！
#   祝比赛顺利！

import os
from utils import load_dataset, preprocess

def data_process():
    data = load_dataset()
    final_data = []
    for topic, session_list in data.items():
        for session in session_list:
            sampling_chunking = preprocess(session)
            for sampling in sampling_chunking.get('sampling'):
                sampling = [s.replace('\n', ' ').strip() for s in sampling]
                final_data.append([topic] + sampling)
                # print([topic] + sampling)
            for chunking in sampling_chunking.get('chunking'):
                chunking = [c.replace('\n', ' ').strip() for c in chunking]
                final_data.append([topic] + chunking)
                # print([topic] + chunking)
    if not os.path.exists('data'):
        os.mkdir('data')
    with open('data/train.txt' ,'w', encoding='utf-8') as f:
        for session in final_data:
            f.write('\n'.join(session)+'\n\n')


data_process()