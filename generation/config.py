#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : SMP-MCC评测会务组
# @Email  : smp_mcc@163.com
# @About  :
#   如有任何疑问，请随时联系评测会务组！
#   祝比赛顺利！

CONFIG = {
    # 数据集位置
    'DATA_DIR': '../data/dataset/',
    # API 服务设置
    'HOST': '0.0.0.0',
    'PORT': 10250,
    # 词库
    'voca_path': 'vocabulary/vocab_small.txt',
    # 对话模型路径
    'dialogue_model_path': 'dialogue_model/model_epoch10',
    # dialogue history 的最大长度
    'max_history_len': 10,
    # 每个utterance的最大长度,超过指定长度则进行截断
    'max_len': 25,
    # 重复惩罚参数，若生成的对话重复性较高，可适当提高该参数
    'repetition_penalty': 1.0,
    # 生成的temperature
    'temperature': 1,
    # 最高k选1
    'topk': 8,
    # 最高积累概率
    'topp': 0,
}
