#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from ipcheck import GEO2CITY_DB_NAME, GEO2ASN_DB_NAME, GEO2CITY_DB_PATH, GEO2ASN_DB_PATH, GEO_CONFIG_PATH, GEO_DEF_CONFIG_PATH, WorkMode
from ipcheck.app.config import Config
from ipcheck.app.gen_ip_utils import gen_ip_list
from ipcheck.app.geo_utils import check_or_gen_def_config, download_geo_db, parse_geo_config, check_geo_version, save_version
import subprocess
import sys
from ipcheck.app.utils import print_file_content
from ipcheck.app.statemachine import state_machine
from ipcheck.app.cli_args import parse_args

def ask_confirm(prompt_str):
    while True:
        answer = input(prompt_str)
        if answer.upper() in ['Y', 'YES']:
            return True
        elif answer.upper() in ['N', 'NO']:
            return False
        else:
            print('输入有误, 请重新输入!')


def get_info():
    state_machine.work_mode = WorkMode.IGEO_INFO
    args = parse_args(WorkMode.IGEO_INFO)
    config = Config()
    config.ro_ip_source = args.sources
    ip_list = gen_ip_list(False)
    if ip_list:
        for ip_info in ip_list:
            print(ip_info.geo_info_str)
    else:
        print('请检查是否输入了有效ip(s)')


def filter_ips():
    state_machine.work_mode = WorkMode.IP_FILTER
    args = parse_args(WorkMode.IP_FILTER)
    config = Config()
    config.ro_ip_source = args.sources
    out_file = args.output
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
    config.ro_only_v4 = args.only_v4
    config.ro_only_v6 = args.only_v6
    if args.cr_size > 0:
        config.cidr_sample_ip_num = args.cr_size
    print('cidr 抽样ip 个数为:', config.cidr_sample_ip_num)
    ip_list = gen_ip_list(False)
    if ip_list:
        ips = [ip_info.ip for ip_info in ip_list]
        ips = list(dict.fromkeys(ips))
        print('从筛选条件中生成了{}个ip:'.format(len(ips)))
        for ip in ips:
            print(ip)
        if out_file:
            with open(out_file, 'w', encoding='utf-8') as f:
                for ip in ips:
                    f.write(ip)
                    f.write('\n')
            print('筛选通过{}个ip 已导入到{}'.format(len(ips), out_file))
    else:
        print('未筛选出指定IP, 请检查参数!')


def download_db():
    state_machine.work_mode = WorkMode.IGEO_DL
    args = parse_args(WorkMode.IGEO_DL)
    url = args.url
    proxy = args.proxy
    auto_confirm = args.yes
    if not args.url:
        return self_update(proxy, auto_confirm)
    path = None
    if url.endswith(GEO2CITY_DB_NAME):
        path = GEO2CITY_DB_PATH
    if url.endswith(GEO2ASN_DB_NAME):
        path = GEO2ASN_DB_PATH
    if path:
        download_geo_db(url, path, proxy)
    else:
        print('请输入包含{} 或 {} 的url'.format(GEO2CITY_DB_NAME, GEO2ASN_DB_NAME))


def config_edit():
    state_machine.work_mode = WorkMode.IGEO_CFG
    args = parse_args(WorkMode.IGEO_CFG)
    if args.example:
        print_file_content(GEO_DEF_CONFIG_PATH)
        return
    check_or_gen_def_config()
    print('编辑配置文件 {}'.format(GEO_CONFIG_PATH))
    platform = sys.platform
    if platform.startswith('win'):
        subprocess.run(['notepad.exe', GEO_CONFIG_PATH])
    elif platform.startswith('linux'):
        subprocess.run(['vim', GEO_CONFIG_PATH])
    else:
        print('未知的操作系统, 请尝试手动修改{}!'.format(GEO_CONFIG_PATH))


def self_update(proxy=None, auto_confirm=False):
    check_or_gen_def_config()
    db_asn_url, db_city_url, cfg_proxy, db_api_url = parse_geo_config()
    proxy = proxy if proxy else cfg_proxy
    has_update, remote_version, local_version = check_geo_version(db_api_url, proxy)
    local_tag = local_version.get('tag_name', 'unknown')
    remote_tag = remote_version.get('tag_name', 'unknown')
    allow_update = False

    # remote_version 检查失败，直接提示并退出
    if not remote_version:
        prompt_str = '检测GEO数据库更新失败, 是否强制下载GEO数据库: Y(es)/N(o)\n'
        allow_update = ask_confirm(prompt_str)
        if not allow_update:
            return
    # 有更新，auto_confirm 时自动下载，否则询问
    elif has_update:
        if auto_confirm:
            print(f'检测到GEO数据库有更新: {local_tag} -> {remote_tag}, 自动更新下载中... ...')
            allow_update = True
        else:
            prompt_str = f'检测到GEO数据库有更新: {local_tag} -> {remote_tag}, 是否更新: Y(es)/N(o)\n'
            allow_update = ask_confirm(prompt_str)
        if not allow_update:
            return

    # 无更新，允许用户选择是否强制重新下载
    else:
        prompt_str = f'GEO数据库已最新: {remote_tag}, 是否强制重新下载GEO数据库: Y(es)/N(o)\n'
        if auto_confirm:
            print(f'检测到GEO数据库为最新: {remote_tag}, 无需更新!')
            return
        allow_update = ask_confirm(prompt_str)
        if not allow_update:
            return

    # 执行更新
    print('ASN 数据库下载地址:', db_asn_url)
    res_asn = download_geo_db(db_asn_url, GEO2ASN_DB_PATH, proxy)
    print('CITY 数据库下载地址:', db_city_url)
    res_city = download_geo_db(db_city_url, GEO2CITY_DB_PATH, proxy)
    if res_asn and res_city:
        save_version(remote_version)
