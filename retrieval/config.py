#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : SMP-MCC评测会务组
# @Email  : smp_mcc@163.com
# @About  :
#   如有任何疑问，请随时联系评测会务组！
#   祝比赛顺利！

CONFIG = {
    # 索引文件保存位置
    'IR_DIR': 'mcc_ir',
    # 数据集位置
    'DATA_DIR': '../data/dataset',
    # 停用词保存位置
    'STOP_WORDS': '../data/哈工大停用词表.txt',
    # API 服务设置
    'HOST': '0.0.0.0',
    'PORT': 10240,
    # 生成模型API接口（默认存在 test 和 get_res 两种路由）
    'GEN_API': 'http://127.0.0.1:10250'
}
