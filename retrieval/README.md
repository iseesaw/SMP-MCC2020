## FAQ

### 准备工作

- requirements

``` shell
    pip install -r requirements.txt
```

- dataset

下载开放数据集

### 参数设置

参考 `config.py` 文件进行配置

### 系统初始化

``` shell
python ir_system.py -mode init
```

### 运行服务

``` shell
python ir_system.py -mode server
```

或者

``` shell
gunicorn -b 127.0.0.1:10240 -w 4 ir_server:app
```

