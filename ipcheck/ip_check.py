#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
from ipcheck import WorkMode, IpcheckStage, IP_CHECK_DEF_CONFIG_PATH, IP_CHECK_CONFIG_PATH
from ipcheck.app.config import Config
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.cli_args import parse_args
from ipcheck.app.gen_ip_utils import gen_ip_list
from ipcheck.app.statemachine import state_machine
from ipcheck.app.valid_test import ValidTest
from ipcheck.app.rtt_test import RttTest
from ipcheck.app.speed_test import SpeedTest
from ipcheck.app.geo_utils import parse_geo_config, check_geo_version
from typing import Iterable
from ipcheck.app.utils import is_ip_address, is_ip_network, gen_time_desc, parse_url, is_hostname, copy_file, print_file_content

# msg to notify user about geo db update
update_message = None

def print_cache():
    if state_machine.stop_event.is_set():
        state_machine.print_cache()

def check_or_gen_def_config(def_cfg_path):
    if not os.path.exists(def_cfg_path):
        print('警告: 配置文件不存在, 正在生成默认配置... ...')
        copy_file(IP_CHECK_DEF_CONFIG_PATH, def_cfg_path)
        print('配置文件已生成位于 {}'.format(def_cfg_path))

# 从手动参数中覆盖默认config
def load_config():
    args = parse_args(WorkMode.IP_CHECK)
    config_path = args.config
    if config_path:
        if not os.path.exists(config_path):
            raise RuntimeError(f'用户指定配置文件{config_path} 不存在!')
    else:
        check_or_gen_def_config(IP_CHECK_CONFIG_PATH)
        config_path = IP_CHECK_CONFIG_PATH
    print('当前配置文件为:', config_path)
    Config.CONFIG_PATH = config_path
    config = Config()
    config.pure_mode = args.pure_mode
    print('纯净模式:', config.pure_mode)
    config.ro_verbose = args.verbose
    print('是否开启调试信息:', config.ro_verbose)
    if config.ro_verbose:
        config.vt_print_err = True
        config.rt_print_err = True
        config.st_print_err = True
    config.ro_ip_source = args.source
    print('测试源文件为:', config.ro_ip_source)
    block_list, white_list = args.block_list, args.white_list
    if block_list and white_list:
        print('偏好参数与黑名单参数同时存在, 自动忽略黑名单参数!')
        block_list = None
    if white_list:
        print('白名单参数为:', white_list)
        config.ro_white_list = white_list
    if block_list:
        print('黑名单参数为:', block_list)
        config.ro_block_list = block_list
    config.ro_prefer_locs = args.prefer_locs
    if config.ro_prefer_locs:
        print('优选地区参数为:', config.ro_prefer_locs)
    prefer_orgs, block_orgs = args.prefer_orgs, args.block_orgs
    if prefer_orgs and block_orgs:
        print('偏好org参数与屏蔽org参数同时存在, 自动忽略屏蔽org参数!')
        block_orgs = None
    config.ro_prefer_orgs = args.prefer_orgs
    if prefer_orgs:
        print('优选org 参数为:', prefer_orgs)
        config.ro_prefer_orgs = prefer_orgs
    if block_orgs:
        print('屏蔽org 参数为:', block_orgs)
        config.ro_block_orgs = block_orgs
    if args.prefer_ports:
        config.ro_prefer_ports = [ port for port in args.prefer_ports if 0 < port < 65535 ]
    if config.ro_prefer_ports:
        print('ip:port 测试源端口为:', config.ro_prefer_ports)
    config.vt_enabled = not args.disable_vt
    config.rt_enabled = not args.disable_rt
    config.st_enabled = not args.disable_st
    config.ro_dry_run = args.dry_run
    if config.ro_dry_run:
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
    config.ip_port = args.port
    print('测试端口为:', config.ip_port)
    config.vt_file_check = args.disable_file_check == False
    print('可用性测试文件检测开关为:', config.vt_file_check)
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
        config.ro_out_file = args.output
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
        config.ro_out_file = os.path.join(dir_name, 'result_{}_{}.txt'.format(dst_name, config.ip_port))
    print('优选ip 文件为:', config.ro_out_file)
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
    if loss >= 0:
        config.rt_max_loss = loss
    config.ro_only_v4 = args.only_v4
    config.ro_only_v6 = args.only_v6
    if args.cr_size > 0:
        config.cidr_sample_ip_num = args.cr_size
    print('cidr 抽样ip 个数为:', config.cidr_sample_ip_num)
    if args.url:
        host_name, path = parse_url(args.url)
        config.vt_host_name = host_name
        config.vt_path = path
        config.st_url = args.url
        config.vt_file_url = args.url
    if not is_hostname(config.vt_host_name):
        raise ValueError('可用性测试域名不合法, 请检查参数!')
    return config


def print_better_ips(ips: Iterable[IpInfo]):
    print('优选ip 如下: ')
    for ip_info in ips:
        print(ip_info)


def write_better_ips_to_file(ips: Iterable[IpInfo], path):
    with open(path, 'w', encoding='utf-8') as f:
        for ip_info in ips:
            f.write(ip_info.get_info())
            f.write('\n')
        f.write('\n')
        f.write(gen_time_desc())
        f.write('\n')
    print('测试通过%d个优选ip 已导出到' % len(ips), path)

def write_pure_ips_to_file(ips: Iterable[IpInfo], path):
    with open(path, 'w', encoding='utf-8') as f:
        for ip_info in ips:
            f.write(ip_info.ip)
            f.write('\n')
    print('测试通过%d个优选ip 已导出到' % len(ips), path)


def check_geo_update():
    global update_message
    try:
        _, _, proxy, db_api_url = parse_geo_config()
        if db_api_url:
            has_update, remote_version, local_version = check_geo_version(db_api_url, proxy, verbose=False)
            if has_update and remote_version:
                remote_tag = remote_version.get('tag_name', 'unknown')
                local_tag = local_version.get('tag_name', 'unknown')
                update_message = f"\n[notice] A new release of geo database is available: {local_tag} -> {remote_tag}\n[notice] To update, run: igeo-dl"
    except Exception:
        pass


def run_ip_check():
    state_machine.work_mode = WorkMode.IP_CHECK
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
    if config.ro_verbose:
        print('\n可用性测试配置为:')
        print(valid_test_config)
    valid_test = ValidTest(ip_list, valid_test_config)
    passed_ips = valid_test.run()
    print_cache()

    # rtt 测试
    if passed_ips:
        rtt_test_config = config.get_rtt_test_config()
        if config.ro_verbose:
            print('\nrtt 测试配置为:')
            print(rtt_test_config)
        rtt_test = RttTest(passed_ips, rtt_test_config)
        passed_ips = rtt_test.run()
        passed_ips = sorted(passed_ips, key=lambda x: x.rtt)
    else:
        print('可用性测试没有获取到可用ip, 测试停止!')
        return
    print_cache()

    # 测速
    if passed_ips:
        speed_test_config = config.get_speed_test_config()
        if config.ro_verbose:
            print('\n速度测试配置为:')
            print(speed_test_config)
        speed_test = SpeedTest(passed_ips, speed_test_config)
        passed_ips = speed_test.run()
    else:
        print('rtt 测试没有获取到可用ip, 测试停止!')
        return
    print_cache()

    # 对结果进行排序
    if passed_ips:
        passed_ips = sorted(passed_ips, key=lambda x: x.max_speed, reverse=True)
        print_better_ips(passed_ips)
        if not config.no_save:
            if config.pure_mode:
                write_pure_ips_to_file(passed_ips, config.ro_out_file)
            else:
                write_better_ips_to_file(passed_ips, config.ro_out_file)
    else:
        print('下载测试没有获取到可用ip, 测试停止!')
        return


def main():
    threading.Thread(target=check_geo_update, daemon=True).start()
    run_ip_check()
    if update_message:
        print(update_message)
    os._exit(0)


def config_edit():
    state_machine.work_mode = WorkMode.IP_CHECK_CFG
    args = parse_args(WorkMode.IP_CHECK_CFG)
    config_path = args.output
    check_or_gen_def_config(config_path)
    if args.example:
        print_file_content(IP_CHECK_DEF_CONFIG_PATH)
        return
    print('编辑配置文件 {}'.format(config_path))
    platform = sys.platform
    if platform.startswith('win'):
        subprocess.run(['notepad.exe', config_path])
    elif platform.startswith('linux'):
        subprocess.run(['vim', config_path])
    else:
        print('未知的操作系统, 请尝试手动修改{}!'.format(config_path))
