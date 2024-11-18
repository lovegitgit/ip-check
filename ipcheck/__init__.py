#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import importlib_metadata

metadata = importlib_metadata.metadata("ip-check")

__version__ = metadata['version']

# ip-check constants
IP_CHECK_DEFAULT_CONFIG = '''# 通用配置
[common]
# 测试端口
ip_port = 443
# 是否存储结果到文件
no_save = False

# 可用性检查配置
[valid test]
# 是否测试可用性
enabled = True
# 限制参与valid 测试的ip 数量
ip_limit_count = 1500
# 可用性检测域名
host_name = cloudflare.com
# 使用user-agent
user_agent = False
# 可用性检测路径, 固定的, 取决于cloudflare
path = /cdn-cgi/trace
# 可用性测试多线程数量
thread_num = 64
# 可用性测试时的网络请求重试次数
max_retry = 4
# retry, backoff_factor
retry_factor = 0.3
# 可用性测试的网络请求timeout, 单位 s
timeout = 3.5
# 可用性测试检测的key
check_key = h
# 是否获取IP 机场码信息, 当前仅支持cf ip, 如果测试其他cdn 需要关闭
get_loc = True

# rtt 测试配置
[rtt test]
enabled = True
# 限制参与rtt 测试的ip 数量
ip_limit_count = 1000
# rtt tcpping 间隔
interval = 1
# rtt 测试多线程数量
thread_num = 8
# rtt 测试的网络请求timeout, 单位 s
timeout = 3
# rtt 测试网络请求重试次数
max_retry = 6
# rtt 测试的延时及格值, 单位 ms
max_rtt = 300
# rtt 测试次数
test_count = 13
# 最大丢包率控制, 单位 百分比
max_loss = 100

# 下载速度测试配置
[speed test]
# 是否开启速度测试
enabled = True
# 限制参与速度测试的ip 数量
ip_limit_count = 1000
# 测试下载文件的域名
host_name = speed.cloudflare.com
# 使用user-agent
user_agent = False
# 测试下载文件的路径
file_path = /__down?bytes=500000000
# 测试下载文件的重试次数
max_retry = 10
# retry, backoff_factor
retry_factor = 0.3
# 下载测试网络请求timeout, 单位 s
timeout = 5
# 下载时长限制, 单位 s
download_time = 10
# 最小达标速度, 单位 kB/s
download_speed = 5000
# 最小平均速度
avg_download_speed = 0
# 是否执行快速测速开关
fast_check = False
# 获取到指定个优选ip 停止
bt_ip_limit = 0'''


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0'
]


# igeo constants
GEO2CITY_DB_NAME = 'GeoLite2-City.mmdb'
GEO2ASN_DB_NAME = 'GeoLite2-ASN.mmdb'
GEO2CITY_DB_PATH = os.path.join(os.path.dirname(__file__), GEO2CITY_DB_NAME)
GEO2ASN_DB_PATH = os.path.join(os.path.dirname(__file__), GEO2ASN_DB_NAME)
GEO_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'geo.ini')
GEO_VERSION_PATH = os.path.join(os.path.dirname(__file__), '.geo_version')
GEO_DEFAULT_CONFIG = '''[common]
# 下载使用代理,格式为 protocol://host:port, 如: socks5://127.0.0.1:1080
proxy =
# asn 数据库下载地址
db_asn_url = https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-ASN.mmdb
# city 数据库下载地址
db_city_url = https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb
# 数据库更新检测API
db_api_url = https://api.github.com/repos/P3TERX/GeoLite.mmdb/releases/latest
'''