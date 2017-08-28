# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: cyj
@time: 2016/11/19
"""


# 打印函数执行时间
def print_exec_time(func):
    import time

    def wrap(*a, **kw):
        start_time = time.time()
        ret = func(*a, **kw)
        print("{0} exec time: {1}".format(func.__name__, time.time() - start_time))
        return ret

    return wrap


#  打印函数执行线程
def print_exec_thread(func):
    import threading

    def wrap(*a, **kw):
        print("exec {0} start in thread:{1}".format(func.__name__, threading.currentThread().getName()))
        ret = func(*a, **kw)
        print("exec {0} end in thread:{1}".format(func.__name__, threading.currentThread().getName()))
        return ret

    return wrap


# 单例装饰器
def singleton(cls):
    instances = dict()  # 初始为空

    def wrap(*args, **kwargs):
        if cls not in instances:  # 如果不存在, 则创建并放入字典
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrap



