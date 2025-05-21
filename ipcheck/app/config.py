#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import sys

from ipcheck.app.common_config import CommonConfig
from ipcheck.app.valid_test_config import ValidTestConfig
from ipcheck.app.rtt_test_config import RttTestConfig
from ipcheck.app.speed_test_config import SpeedTestConfig
from ipcheck.app.utils import singleton

SECTION_COMMON = 'common'
SECTION_COMMON_PREFIX = ''

SECTION_VALID = 'valid test'
SECTION_VALID_PREFIX = 'vt_'

SECTION_RTT = 'rtt test'
SECTION_RTT_PREFIX = 'rt_'

SECTION_DOWNLOAD = 'speed test'
SECTION_DOWNLOAD_PREFIX = 'st_'

RUNTIME_ONLY_PREFIX = 'ro_'

SECTIONS = [SECTION_COMMON, SECTION_VALID, SECTION_RTT, SECTION_DOWNLOAD]
PREFIX_SECTION_PAIRS = {
    SECTION_COMMON_PREFIX: SECTION_COMMON,
    SECTION_VALID_PREFIX: SECTION_VALID,
    SECTION_RTT_PREFIX: SECTION_RTT,
    SECTION_DOWNLOAD_PREFIX: SECTION_DOWNLOAD
}
SECTION_PREFIX_PAIRS = {v: k for k, v in PREFIX_SECTION_PAIRS.items()}

@singleton
class Config(CommonConfig):
    CONFIG_PATH = None

    def __init__(self):
        # common 部分配置
        self.ip_port = 443
        self.no_save = False
        # cidr ip 数量限制
        self.cidr_sample_ip_num = 16
        # ro: runtime-only settings
        # 以下仅仅在运行时支持修改, 不支持文件配置
        # 测试ip 源, 可选ip、ip cidr、文本(读取ip、ip cidr)、zip 压缩包(遍历其中的txt 文本, 读取ip、ip cidr)
        self.ro_ip_source = None
        self.ro_out_file = None
        self.ro_verbose = None
        self.ro_white_list = None
        self.ro_block_list = None
        self.ro_prefer_locs = None
        self.ro_prefer_ports = None
        self.ro_prefer_orgs = None
        self.ro_block_orgs = None
        self.ro_dry_run = False
        self.ro_only_v4 = False
        self.ro_only_v6 = False

        # 可用性valid test测试选项
        # 是否测试可用性
        self.vt_enabled = True
        # 限制参与valid 测试的ip 数量
        self.vt_ip_limit_count = 1500
        # 可用性检测域名
        self.vt_host_name = 'cloudflare.com'
        # 是否使用user-agnet
        self.vt_user_agent = False
        # 可用性检测路径, 固定的, 取决于cloudflare
        self.vt_path = '/cdn-cgi/trace'
        # 可用性测试多线程数量
        self.vt_thread_num = 64
        # 可用性测试时的网络请求重试次数
        self.vt_max_retry = 4
        # 可用性测试retry 间隔因子
        self.vt_retry_factor = 0.3
        # 可用性测试的网络请求timeout, 单位 s
        self.vt_timeout = 3.5
        # 可用性测试检测的key
        self.vt_check_key = 'h'
        # # 是否检测地区信息, draft
        # self.vt_get_loc = True

        # 延时rtt test 测试选项
        self.rt_enabled = True
        # 限制参与rtt 测试的ip 数量
        self.rt_ip_limit_count = 1000
        # rtt tcpping 间隔
        self.rt_interval = 1
        # rtt 测试多线程数量
        self.rt_thread_num = 8
        # rtt 测试的网络请求timeout, 单位 s
        self.rt_timeout = 3
        # rtt 测试网络请求重试次数
        self.rt_max_retry = 6
        # rtt 测试及格线
        self.rt_max_rtt = 300
        # rtt 测试次数
        self.rt_test_count = 13
        # 最大丢包率
        self.rt_max_loss = 100

        # 下载速度测试 speed test 测试选项
        # 是否测试下载速度
        self.st_enabled = True
        # 参与测速ip 的数量限制
        self.st_ip_limit_count = 1000
        # 测试下载文件的域名
        self.st_host_name = 'cloudflaremirrors.com'
        # 是否使用user-agent
        self.st_user_agent = False
        # 测试下载文件的路径
        self.st_file_path = '/archlinux/iso/latest/archlinux-x86_64.iso'
        # 下载测试时网络请求的重试次数
        self.st_max_retry = 10
        # 下载测试retry 间隔因子
        self.st_retry_factor = 0.3
        # 下载测试网络请求timeout, 单位 s
        self.st_timeout = 5
        # 下载时长限制, 单位 s
        self.st_download_time = 10
        # 最小达标速度, 单位 kB/s
        self.st_download_speed = 5000
        # 最小平均速度
        self.st_avg_download_speed = 0
        # 是否执行快速测速开关
        self.st_fast_check = False
        # 获取到指定个优选ip 停止
        self.st_bt_ip_limit = 0
        # 是否丢弃测速中途异常ip
        self.st_rm_err_ip = False

        if self.CONFIG_PATH:
            self.__update(self.CONFIG_PATH)

    def __update(self, path):
        parser = configparser.ConfigParser()
        parser.read(path, 'utf-8')
        variables = vars(self)
        for section in parser.sections():
            prefix = SECTION_PREFIX_PAIRS.get(section, None)
            if prefix is None:
                continue
            for option in parser.options(section):
                value = parser.get(section, option)
                key = '{}{}'.format(prefix, option)
                if not self.check_key_valid(key):
                    continue
                original_value = variables.get(key)
                type_expr = None
                if original_value:
                    type_of_original_value = type(original_value)
                    if type_of_original_value == str:
                        type_expr = 'str'
                if type_expr:
                    expr = "self.{} = '{}'".format(key, value)
                else:
                    expr = 'self.{} = {}'.format(key, value)
                # print(expr)
                exec(expr)


    def check_key_valid(self, key):
        variables = vars(self)
        for k, _ in variables.items():
            if k.startswith(RUNTIME_ONLY_PREFIX):
                continue
            if k == key:
                return True
        return False


    def get_valid_test_config(self) -> ValidTestConfig:
        return ValidTestConfig(self)

    def get_rtt_test_config(self) -> RttTestConfig:
        return RttTestConfig(self)

    def get_speed_test_config(self) -> SpeedTestConfig:
        return SpeedTestConfig(self)

    @property
    def parser(self):
        parser = configparser.ConfigParser()
        for section in SECTIONS:
            parser[section] = {}
        variables = vars(self)
        for k, v in variables.items():
            if k.startswith(RUNTIME_ONLY_PREFIX):
                continue
            prefix = k[:3]
            section = PREFIX_SECTION_PAIRS.get(prefix, None)
            if section:
                parser[section].update({k[3:]: str(v)})
            else:
                parser[SECTION_COMMON].update({k: str(v)})
        return parser

    def save_to(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            self.parser.write(f)

if __name__ == '__main__':
    test_config = Config(sys.argv[1])
    print(test_config)