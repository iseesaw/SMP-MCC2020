#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : SMP-MCC评测会务组
# @Email  : smp_mcc@163.com
# @About  :
#   如有任何疑问，请随时联系评测会务组！
#   祝比赛顺利！

import time

from flask import Flask, jsonify, request

from config import CONFIG

import transformers
import torch
import os
import json
import random
import numpy as np
from torch.utils.tensorboard import SummaryWriter
from datetime import datetime
from tqdm import tqdm
from torch.nn import DataParallel
import logging
from transformers.modeling_gpt2 import GPT2Config, GPT2LMHeadModel
from transformers import BertTokenizer
from os.path import join, exists
from itertools import zip_longest, chain
from dataset import MyDataset
from torch.utils.data import Dataset, DataLoader
from torch.nn import CrossEntropyLoss
from sklearn.model_selection import train_test_split
from train import create_model
import torch.nn.functional as F

app = Flask(__name__)

# 加载模型
device = 'cuda' if CONFIG.get('cuda') else 'cpu'
tokenizer = BertTokenizer(vocab_file=CONFIG.get('voca_path'))
model = GPT2LMHeadModel.from_pretrained(CONFIG.get('dialogue_model_path'))
model.to(device)
model.eval()

def top_k_top_p_filtering(logits, top_k=0, top_p=0.0, filter_value=-float('Inf')):
    """ Filter a distribution of logits using top-k and/or nucleus (top-p) filtering
        Args:
            logits: logits distribution shape (vocabulary size)
            top_k > 0: keep only top k tokens with highest probability (top-k filtering).
            top_p > 0.0: keep the top tokens with cumulative probability >= top_p (nucleus filtering).
                Nucleus filtering is described in Holtzman et al. (http://arxiv.org/abs/1904.09751)
        From: https://gist.github.com/thomwolf/1a5a29f6962089e871b94cbd09daf317
    """
    assert logits.dim() == 1  # batch size 1 for now - could be updated for more but the code would be less clear
    top_k = min(top_k, logits.size(-1))  # Safety check
    if top_k > 0:
        # Remove all tokens with a probability less than the last token of the top-k
        # torch.topk()返回最后一维最大的top_k个元素，返回值为二维(values,indices)
        # ...表示其他维度由计算机自行推断
        indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
        logits[indices_to_remove] = filter_value  # 对于topk之外的其他元素的logits值设为负无穷

    if top_p > 0.0:
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)  # 对logits进行递减排序
        cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        # Remove tokens with cumulative probability above the threshold
        sorted_indices_to_remove = cumulative_probs > top_p
        # Shift the indices to the right to keep also the first token above the threshold
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0

        indices_to_remove = sorted_indices[sorted_indices_to_remove]
        logits[indices_to_remove] = filter_value
    return logits


def generate(context=['你喜欢看什么电影？'], topic='电影'):
    """
    生成
    """
    if CONFIG.get('save_samples_path'):
        if not os.path.exists(CONFIG.get('save_samples_path')):
            os.makedirs(CONFIG.get('save_samples_path'))
        samples_file = open(CONFIG.get('save_samples_path') + '/samples.txt', 'a', encoding='utf8')
        samples_file.write("聊天记录{}:\n".format(datetime.now()))
    history = []
    for text in context:
        history.append(tokenizer.encode(text))
    input_ids = [tokenizer.cls_token_id]  # 每个input以[CLS]为开头

    for history_id, history_utr in enumerate(history[-CONFIG.get('max_history_len'):]):
        input_ids.extend(history_utr)
        input_ids.append(tokenizer.sep_token_id)
    curr_input_tensor = torch.tensor(input_ids).long().to(device)
    generated = []
        # 最多生成max_len个token
    for _ in range(CONFIG.get('max_len')):
        outputs = model(input_ids=curr_input_tensor)
        next_token_logits = outputs[0][-1, :]
        # 对于已生成的结果generated中的每个token添加一个重复惩罚项，降低其生成概率
        for id in set(generated):
            next_token_logits[id] /= CONFIG.get('repetition_penalty')
        next_token_logits = next_token_logits / CONFIG.get('temperature')
        # 对于[UNK]的概率设为无穷小，也就是说模型的预测结果不可能是[UNK]这个token
        next_token_logits[tokenizer.convert_tokens_to_ids('[UNK]')] = -float('Inf')
        filtered_logits = top_k_top_p_filtering(next_token_logits, top_k=CONFIG.get('topk'), top_p=CONFIG.get('topp'))
        # torch.multinomial表示从候选集合中无放回地进行抽取num_samples个元素，权重越高，抽到的几率越高，返回元素的下标
        next_token = torch.multinomial(F.softmax(filtered_logits, dim=-1), num_samples=1)
        if next_token == tokenizer.sep_token_id:  # 遇到[SEP]则表明response生成结束
            break
        generated.append(next_token.item())
        curr_input_tensor = torch.cat((curr_input_tensor, next_token), dim=0)
        # his_text = tokenizer.convert_ids_to_tokens(curr_input_tensor.tolist())
        # print("his_text:{}".format(his_text))
    history.append(generated)
    text = tokenizer.convert_ids_to_tokens(generated)
    if CONFIG.get('save_samples_path'):
        samples_file.write("chatbot:{}\n".format("".join(text)))
    return ("".join(text))


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
    msg = generate()
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
    context = [msg['msg'] for msg in data.get('msgs')]
    # 对应检索构造方法
    msg = generate(context=context, topic=data.get('topic'))

    # 返回您的机器人回复
    resp = {
        "msg": msg,
        "from_id": data["robot_id"],
        "timestamp": time.time()
    }
    return jsonify(resp)


def run_server():
    app.run(host=CONFIG.get('HOST'), port=CONFIG.get('PORT'))

if __name__ == '__main__':
    run_server()