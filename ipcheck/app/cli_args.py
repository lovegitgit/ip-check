#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os

from ipcheck import __version__, IP_CHECK_CONFIG_PATH, WorkMode
from ipcheck.app.utils import UniqueListAction


WORKMODE_META = {
    WorkMode.IP_CHECK: {"cli": "ip-check", "desc": "ip-check 参数"},
    WorkMode.IP_CHECK_CFG: {"cli": "ip-check-cfg", "desc": "ip-check 参数配置向导"},
    WorkMode.IGEO_INFO: {"cli": "igeo-info", "desc": "geo-info 获取ip(s) 的归属地信息"},
    WorkMode.IGEO_DL: {"cli": "igeo-dl", "desc": "igeo-dl 升级/下载geo 数据库"},
    WorkMode.IGEO_CFG: {"cli": "igeo-cfg", "desc": "geo-cfg 编辑geo config"},
    WorkMode.IP_FILTER: {"cli": "ip-filter", "desc": "ip-filter: ip 筛选工具"},
}


def get_cli_name(work_mode):
    return WORKMODE_META[work_mode]["cli"]


def _add_common_filter_args(parser, help_v4="仅测试ipv4", help_v6="仅测试ipv6"):
    parser.add_argument("-w", "--white_list", action=UniqueListAction, type=str, nargs='+', default=None, help='偏好ip参数, 格式为: expr1 expr2, 如8 9 会筛选8和9开头的ip')
    parser.add_argument("-b", "--block_list", action=UniqueListAction, type=str, nargs='+', default=None, help='屏蔽ip参数, 格式为: expr1 expr2, 如8 9 会过滤8和9开头的ip')
    parser.add_argument("-pl", "--prefer_locs", action=UniqueListAction, type=str, nargs='+', default=None, help='偏好国家地区选择, 格式为: expr1 expr2, 如hongkong japan 会筛选HongKong 和Japan 地区的ip')
    parser.add_argument("-po", "--prefer_orgs", action=UniqueListAction, type=str, nargs='+', default=None, help='偏好org 选择, 格式为: expr1 expr2, 如org1 org2 会筛选org1, org2 的服务商ip')
    parser.add_argument("-bo", "--block_orgs", action=UniqueListAction, type=str, nargs='+', default=None, help='屏蔽org 选择, 格式为: expr1 expr2, 如org1 org2 会过滤org1, org2 的服务商ip')
    parser.add_argument("-4", "--only_v4", action="store_true", default=False, help=help_v4)
    parser.add_argument("-6", "--only_v6", action="store_true", default=False, help=help_v6)
    parser.add_argument("-cs", "--cr_size", type=int, default=0, help="cidr 随机抽样ip 数量限制")


def build_parser(work_mode):
    if work_mode == WorkMode.IP_CHECK:
        parser = argparse.ArgumentParser(description=WORKMODE_META[work_mode]["desc"])
        _add_common_filter_args(parser)
        parser.add_argument("-pp", "--prefer_ports", action=UniqueListAction, type=int, default=None, nargs='+', help='针对ip:port 格式的测试源筛选端口, 格式为: expr1 expr2, 如443 8443 会筛选出443 和8443 端口的ip')
        parser.add_argument("-lv", "--max_vt_ip_count", type=int, default=0, help="最大用来检测有效(valid) ip数量限制")
        parser.add_argument("-lr", "--max_rt_ip_count", type=int, default=0, help="最大用来检测rtt ip数量限制")
        parser.add_argument("-ls", "--max_st_ip_count", type=int, default=0, help="最大用来检测下载(speed) 速度的ip数量限制")
        parser.add_argument("-lb", "--max_bt_ip_count", type=int, default=0, help="最大better ip的ip数量限制")
        parser.add_argument("-p", "--port", type=int, default=443, help="用来检测的端口")
        parser.add_argument("-H", "--host", type=str, default=None, help="可用性域名")
        parser.add_argument("-dr", "--disable_rt", action="store_true", default=False, help="是否禁用RTT 测试")
        parser.add_argument("-dv", "--disable_vt", action="store_true", default=False, help="是否禁用可用性测试")
        parser.add_argument("-ds", "--disable_st", action="store_true", default=False, help="是否禁用速度测试")
        parser.add_argument("source", action=UniqueListAction, nargs="+", help="测试源文件")
        parser.add_argument("-o", "--output", type=str, default=None, help="输出文件")
        parser.add_argument("-f", "--fast_check", action="store_true", default=False, help="是否执行快速测试")
        parser.add_argument("-s", "--speed", type=int, default=0, help="期望ip的最低网速 (kB/s)")
        parser.add_argument("-as", "--avg_speed", type=int, default=0, help="期望ip的最低平均网速 (kB/s)")
        parser.add_argument("-r", "--rtt", type=int, default=0, help="期望的最大rtt (ms)")
        parser.add_argument("-l", "--loss", type=int, default=-1, help="期望的最大丢包率")
        parser.add_argument("-c", "--config", type=str, default=None, help="配置文件")
        parser.add_argument("-u", "--url", type=str, default=None, help="测速地址")
        parser.add_argument("-v", "--verbose", action="store_true", default=False, help="显示调试信息")
        parser.add_argument("-ns", "--no_save", action="store_true", default=False, help="是否忽略保存测速结果文件")
        parser.add_argument("--dry_run", action="store_true", default=False, help="是否跳过所有测试")
        parser.add_argument("-df", "--disable_file_check", action="store_true", default=False, help="是否禁用可用性检测文件可用性")
        parser.add_argument("--pure_mode", action="store_true", default=False, help="纯净模式, 不使用geo 数据库进行ip 信息补全, 仅记录ip")
        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s version {__version__} installed in {os.path.dirname(os.path.dirname(__file__))}",
        )
        return parser
    if work_mode == WorkMode.IP_CHECK_CFG:
        parser = argparse.ArgumentParser(description=WORKMODE_META[work_mode]["desc"])
        parser.add_argument("-o", "--output", type=str, default=IP_CHECK_CONFIG_PATH, help="参数配置文件路径")
        parser.add_argument("-e", "--example", action="store_true", default=False, help="显示配置文件示例")
        return parser
    if work_mode == WorkMode.IGEO_INFO:
        parser = argparse.ArgumentParser(description=WORKMODE_META[work_mode]["desc"])
        parser.add_argument("sources", action=UniqueListAction, nargs="+", help="待获取归属地信息的ip(s)")
        return parser
    if work_mode == WorkMode.IP_FILTER:
        parser = argparse.ArgumentParser(description=WORKMODE_META[work_mode]["desc"])
        parser.add_argument("sources", action=UniqueListAction, nargs="+", help="待筛选的ip(s)")
        _add_common_filter_args(parser, help_v4="仅筛选ipv4", help_v6="仅筛选ipv6")
        parser.add_argument("-o", "--output", type=str, default=None, help="输出文件")
        return parser
    if work_mode == WorkMode.IGEO_DL:
        parser = argparse.ArgumentParser(description=WORKMODE_META[work_mode]["desc"])
        parser.add_argument("-u", "--url", type=str, default=None, help="geo 数据库下载地址, 要求结尾包含GeoLite2-City.mmdb 或GeoLite2-ASN.mmdb")
        parser.add_argument("-p", "--proxy", type=str, default=None, help="下载时使用的代理")
        parser.add_argument("-y", "--yes", action="store_true", default=False, help="自动确认更新并下载 GEO 数据库")
        return parser
    if work_mode == WorkMode.IGEO_CFG:
        parser = argparse.ArgumentParser(description=WORKMODE_META[work_mode]["desc"])
        parser.add_argument("-e", "--example", action="store_true", default=False, help="显示配置文件示例")
        return parser
    raise ValueError(f"Unknown work mode: {work_mode}")


def parse_args(work_mode):
    return build_parser(work_mode).parse_args()
