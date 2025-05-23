#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from typing import Iterable
from ipcheck.app.config import Config
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.ip_parser import IpParser
import random

# 生成ip 列表
def gen_ip_list(shuffle=True) -> Iterable[IpInfo]:
    config = Config()
    ip_parser = IpParser(config)
    ip_list = ip_parser.parse()
    if shuffle:
        random.shuffle(ip_list)
    return ip_list