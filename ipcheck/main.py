#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import signal
import ipcheck
from ipcheck.app.config import Config
from ipcheck.app.ip_info import IpInfo
import argparse
from ipcheck.app.gen_ip_utils import gen_ip_list
from ipcheck.app.statemachine import StateMachine
from ipcheck.app.valid_test import ValidTest
from ipcheck.app.rtt_test import RttTest
from ipcheck.app.speed_test import SpeedTest
from typing import List
from ipcheck.app.utils import is_ip_address, is_ip_network, gen_time_desc, write_file


# 注册全局退出监听
def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    StateMachine.print_cache()
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

def check_or_gen_def_config(def_cfg_path):
    if not os.path.exists(def_cfg_path):
        print('警告: 配置文件不存在, 正在生成默认配置... ...')
        from ipcheck import IP_CHECK_DEFAULT_CONFIG
        write_file(IP_CHECK_DEFAULT_CONFIG, def_cfg_path)
        print('配置文件已生成位于 {}'.format(def_cfg_path))

# 从手动参数中覆盖默认config
def load_config():
    parser = argparse.ArgumentParser(description='ip-check 参数')
    parser.add_argument("-w", "--white_list", type=str, nargs='+', default=None, help='偏好ip参数, 格式为: expr1 expr2, 如8 9 会筛选8和9开头的ip')
    parser.add_argument("-b", "--block_list", type=str, nargs='+', default=None, help='屏蔽ip参数, 格式为: expr1 expr2, 如8 9 会过滤8和9开头的ip')
    parser.add_argument("-pl", "--prefer_locs", type=str, nargs='+', default=None, help='偏好国家地区选择, 格式为: expr1 expr2, 如hongkong japan 会筛选HongKong 和Japan 地区的ip')
    parser.add_argument("-po", "--prefer_orgs", type=str, nargs='+', default=None, help='偏好org 选择, 格式为: expr1 expr2, 如org1 org2 会筛选org1, org2 的服务商ip')
    parser.add_argument("-bo", "--block_orgs", type=str, nargs='+', default=None, help='屏蔽org 选择, 格式为: expr1 expr2, 如org1 org2 会过滤org1, org2 的服务商ip')
    parser.add_argument("-pp", "--prefer_ports", type=int, default=None, nargs='+', help='针对ip:port 格式的测试源筛选端口, 格式为: expr1 expr2, 如443 8443 会筛选出443 和8443 端口的ip')
    parser.add_argument("-lv", "--max_vt_ip_count", type=int, default=0, help="最大用来检测有效(valid) ip数量限制")
    parser.add_argument("-lr", "--max_rt_ip_count", type=int, default=0, help="最大用来检测rtt ip数量限制")
    parser.add_argument("-ls", "--max_st_ip_count", type=int, default=0, help="最大用来检测下载(speed) 速度的ip数量限制")
    parser.add_argument("-lb", "--max_bt_ip_count", type=int, default=0, help="最大better ip的ip数量限制")
    parser.add_argument("-p", "--port", type=int, default=0, help="用来检测的端口")
    parser.add_argument("-H", "--host", type=str, default=None, help="可用性域名")
    parser.add_argument("-dr", "--disable_rt", action="store_true", default=False, help="是否禁用RTT 测试")
    parser.add_argument("-dv", "--disable_vt", action="store_true", default=False, help="是否禁用可用性测试")
    parser.add_argument("-ds", "--disable_st", action="store_true", default=False, help="是否禁用速度测试")
    parser.add_argument("source", nargs="+", help="测试源文件")
    parser.add_argument("-o", "--output", type=str, default=None, help="输出文件")
    parser.add_argument("-f","--fast_check", action="store_true", default=False, help="是否执行快速测试")
    parser.add_argument("-s", "--speed", type=int, default=0, help="期望ip的最低网速 (kB/s)")
    parser.add_argument("-as", "--avg_speed", type=int, default=0, help="期望ip的最低平均网速 (kB/s)")
    parser.add_argument("-r", "--rtt", type=int, default=0, help="期望的最大rtt (ms)")
    parser.add_argument("-l", "--loss", type=int, default=0, help="期望的最大丢包率")
    parser.add_argument("-c", "--config", type=str, default=None, help="配置文件")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="显示调试信息")
    parser.add_argument("-ns", "--no_save", action="store_true", default=False, help="是否忽略保存测速结果文件")
    parser.add_argument("--dry_run", action="store_true", default=False, help="是否跳过所有测试")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s version {ipcheck.__version__} installed in {os.path.dirname(__file__)}",
    )
    args = parser.parse_args()
    config_path = args.config
    if config_path and os.path.exists(config_path):
        pass
    else:
        defalt_config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        check_or_gen_def_config(defalt_config_path)
        config_path = defalt_config_path
    print('当前配置文件为:', config_path)
    Config.CONFIG_PATH = config_path
    config = Config()
    config.verbose = args.verbose
    print('是否开启调试信息:', config.verbose)
    config.ip_source = args.source
    print('测试源文件为:', config.ip_source)
    block_list, white_list = args.block_list, args.white_list
    if block_list and white_list:
        print('偏好参数与黑名单参数同时存在, 自动忽略黑名单参数!')
        block_list = None
    if white_list:
        print('白名单参数为:', white_list)
        config.white_list = white_list
    if block_list:
        print('黑名单参数为:', block_list)
        config.block_list = block_list
    config.prefer_locs = args.prefer_locs
    if config.prefer_locs:
        print('优选地区参数为:', config.prefer_locs)
    prefer_orgs, block_orgs = args.prefer_orgs, args.block_orgs
    if prefer_orgs and block_orgs:
        print('偏好org参数与屏蔽org参数同时存在, 自动忽略屏蔽org参数!')
        block_orgs = None
    config.prefer_orgs = args.prefer_orgs
    if prefer_orgs:
        print('优选org 参数为:', prefer_orgs)
        config.prefer_orgs = prefer_orgs
    if block_orgs:
        print('屏蔽org 参数为:', block_orgs)
        config.block_orgs = block_orgs
    if args.prefer_ports:
        config.prefer_ports = [ port for port in args.prefer_ports if 0 < port < 65535 ]
    if config.prefer_ports:
        print('ip:port 测试源端口为:', config.prefer_ports)
    config.vt_enabled = False if args.disable_vt else True
    config.rt_enabled = False if args.disable_rt else True
    config.st_enabled = False if args.disable_st else True
    config.dry_run = args.dry_run
    if config.dry_run:
        print('跳过所有测试!!!')
        config.vt_enabled = False
        config.rt_enabled = False
        config.st_enabled = False
    if not config.vt_enabled:
        print('可用性检测已关闭')
    if not config.rt_enabled:
        print('rtt 测试已关闭')
    if not config.st_enabled:
        print('速度测试已关闭')
    port = args.port
    if port:
        config.ip_port = port
    print('测试端口为:', config.ip_port)
    if args.host:
        config.vt_host_name = args.host
    if args.rtt and args.rtt > 0:
        config.rt_max_rtt = args.rtt
    print('期望最大rtt 为: {} ms'.format(config.rt_max_rtt))
    if args.speed:
        config.st_download_speed = args.speed
    print('期望网速为: {} kB/s'.format(config.st_download_speed))
    if args.avg_speed:
        config.st_avg_download_speed = args.avg_speed
    config.st_avg_download_speed = min(config.st_download_speed, config.st_avg_download_speed)
    print('期望平均网速为: {} kB/s'.format(config.st_avg_download_speed))

    # 检查快速测速开关
    if args.fast_check:
        config.st_fast_check = True
    if config.st_fast_check:
        print('快速测速已开启')

    if args.output:
        config.out_file = args.output
    else:
        fixed_file = args.source[0]
        if not is_ip_address(fixed_file) and is_ip_network(fixed_file):
            fixed_file = fixed_file.replace('/', '@')
        source_file = os.path.join(fixed_file)
        dir_name = os.path.dirname(source_file)
        base_name = os.path.basename(source_file)

        dst_name = base_name.replace('.txt', '')
        dst_name = dst_name.replace('::', '--')
        dst_name = dst_name.replace(':', '-')
        if not dst_name:
            dst_name = dir_name
        config.out_file = os.path.join(dir_name, 'result_{}_{}.txt'.format(dst_name, config.ip_port))
    print('优选ip 文件为:', config.out_file)
    config.no_save = args.dry_run if args.dry_run else args.no_save
    print('是否忽略保存测速结果到文件:', config.no_save)
    # 处理限制参数
    lv, lr, ls, lb, loss = args.max_vt_ip_count, args.max_rt_ip_count, args.max_st_ip_count, args.max_bt_ip_count, args.loss
    if lv > 0:
        config.vt_ip_limit_count = lv
    if lr > 0:
        config.rt_ip_limit_count = lr
    if ls > 0:
        config.st_ip_limit_count = ls
    if lb > 0:
        config.st_bt_ip_limit = lb
    if loss > 0:
        config.rt_max_loss = loss
    return config


def print_better_ips(ips: List[IpInfo]):
    print('优选ip 如下: ')
    for ip_info in ips:
        print(ip_info)


def write_better_ips_to_file(ips: List[IpInfo], path):
    with open(path, 'w', encoding='utf-8') as f:
        for ip_info in ips:
            f.write(ip_info.get_info())
            f.write('\n')
        f.write('\n')
        f.write(gen_time_desc())
        f.write('\n')
    print('测试通过%d个优选ip 已导出到' % len(ips), path)


def main():
    config = load_config()
    ip_list = gen_ip_list()
    ip_list_size = len(ip_list)
    if not ip_list_size:
        print('没有从参数中生产待测试ip 列表, 请检查参数!')
        os._exit(0)
    else:
        print('从参数中生成了{} 个待测试ip'.format(ip_list_size))
    # 可用性测试
    valid_test_config = config.get_valid_test_config()
    if config.verbose:
        print('\n可用性测试配置为:')
        print(valid_test_config)
    valid_test = ValidTest(ip_list, valid_test_config)
    passed_ips = valid_test.run()

    # rtt 测试
    if passed_ips:
        rtt_test_config = config.get_rtt_test_config()
        if config.verbose:
            print('\nrtt 测试配置为:')
            print(rtt_test_config)
        rtt_test = RttTest(passed_ips, rtt_test_config)
        # [IpInfo]
        passed_ips = rtt_test.run()
        passed_ips = sorted(passed_ips, key=lambda x: x.rtt)
    else:
        print('可用性测试没有获取到可用ip, 测试停止!')
        return

    # 测速
    if passed_ips:
        speed_test_config = config.get_speed_test_config()
        if config.verbose:
            print('\n速度测试配置为:')
            print(speed_test_config)
        speed_test = SpeedTest(passed_ips, speed_test_config)
        passed_ips = speed_test.run()
    else:
        print('rtt 测试没有获取到可用ip, 测试停止!')
        return

    # 对结果进行排序
    if passed_ips:
        passed_ips = sorted(passed_ips, key=lambda x: x.max_speed, reverse=True)
        print_better_ips(passed_ips)
        if not config.no_save:
            write_better_ips_to_file(passed_ips, config.out_file)
    else:
        print('下载测试没有获取到可用ip, 测试停止!')
        return


def config_edit():
    def_config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    parser = argparse.ArgumentParser(description='ip-check 参数配置向导')
    parser.add_argument("-o", "--output", type=str, default=def_config_path, help="参数配置文件路径")
    parser.add_argument("-e", "--example", action="store_true", default=False, help="显示配置文件示例")
    args = parser.parse_args()
    config_path = args.output
    check_or_gen_def_config(config_path)
    if args.example:
        from ipcheck import IP_CHECK_DEFAULT_CONFIG
        print(IP_CHECK_DEFAULT_CONFIG)
        return
    print('编辑配置文件 {}'.format(config_path))
    platform = sys.platform
    if platform.startswith('win'):
        subprocess.run(['notepad.exe', config_path])
    elif platform.startswith('linux'):
        subprocess.run(['vim', config_path])
    else:
        print('未知的操作系统, 请尝试手动修改{}!'.format(config_path))


if __name__ == '__main__':
    main()