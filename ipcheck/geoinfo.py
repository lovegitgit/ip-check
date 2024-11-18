#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from ipcheck import GEO2CITY_DB_NAME, GEO2ASN_DB_NAME, GEO2CITY_DB_PATH, GEO2ASN_DB_PATH, GEO_CONFIG_PATH, GEO_DEFAULT_CONFIG
from ipcheck.app.config import Config
from ipcheck.app.gen_ip_utils import gen_ip_list
from ipcheck.app.geo_utils import check_or_gen_def_config, download_geo_db, parse_geo_config, check_geo_version, save_version
import argparse
import subprocess
import sys

def get_info():
    parser = argparse.ArgumentParser(description='geo-info 获取ip(s) 的归属地信息')
    parser.add_argument("sources", nargs="+", help="待获取归属地信息的ip(s)")
    args = parser.parse_args()
    config = Config()
    config.skip_all_filters = True
    config.ip_source = args.sources
    ip_list = gen_ip_list(False)
    if ip_list:
        for ip_info in ip_list:
            print(ip_info.geo_info_str)
    else:
        print('请检查是否输入了有效ip(s)')


def filter_ips():
    parser = argparse.ArgumentParser(description='ifilter: ip 筛选工具')
    parser.add_argument("sources", nargs="+", help="待筛选的ip(s)")
    parser.add_argument("-w", "--white_list", type=str, nargs='+', default=None, help='偏好ip参数, 格式为: expr1 expr2, 如8 9 会筛选8和9开头的ip')
    parser.add_argument("-b", "--block_list", type=str, nargs='+', default=None, help='屏蔽ip参数, 格式为: expr1 expr2, 如8 9 会过滤8和9开头的ip')
    parser.add_argument("-pl", "--prefer_locs", type=str, nargs='+', default=None, help='偏好国家地区选择, 格式为: expr1 expr2, 如hongkong japan 会筛选HongKong 和Japan 地区的ip')
    parser.add_argument("-po", "--prefer_orgs", type=str, nargs='+', default=None, help='偏好org 选择, 格式为: expr1 expr2, 如org1 org2 会筛选org1, org2 的服务商ip')
    parser.add_argument("-bo", "--block_orgs", type=str, nargs='+', default=None, help='屏蔽org 选择, 格式为: expr1 expr2, 如org1 org2 会过滤org1, org2 的服务商ip')
    parser.add_argument("-o", "--output", type=str, default=None, help="输出文件")
    args = parser.parse_args()
    config = Config()
    config.ip_source = args.sources
    out_file = args.output
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
    parser = argparse.ArgumentParser(description='igeo-dl 升级/下载geo 数据库')
    parser.add_argument("-u", "--url", type=str, default=None, help="geo 数据库下载地址, 要求结尾包含GeoLite2-City.mmdb 或GeoLite2-ASN.mmdb")
    parser.add_argument("-p", "--proxy", type=str, default=None, help="下载时使用的代理")
    args = parser.parse_args()
    url = args.url
    proxy = args.proxy
    if not args.url:
        return self_update(proxy)
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
    parser = argparse.ArgumentParser(description='geo-cfg 编辑geo config')
    parser.add_argument("-e", "--example", action="store_true", default=False, help="显示配置文件示例")
    args = parser.parse_args()
    if args.example:
        print(GEO_DEFAULT_CONFIG)
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


def self_update(proxy=None):
    check_or_gen_def_config()
    db_asn_url, db_city_url, cfg_proxy, db_api_url = parse_geo_config()
    proxy = proxy if proxy else cfg_proxy
    has_update, current_version = check_geo_version(db_api_url, proxy)
    allow_update = False
    prompt_str = '检测到GEO数据库有更新, 是否更新: Y(es)/N(o)\n' if has_update else 'GEO数据库已最新, 是否重新下载GEO数据库: Y(es)/N(o)\n'
    if not current_version:
        prompt_str = '检测GEO数据库更新失败, 是否强制下载GEO数据库: Y(es)/N(o)\n'
    while True:
        answer = input(prompt_str)
        if answer.upper() in ['Y', 'YES']:
            allow_update = True
            break
        elif answer.upper() in ['N', 'NO']:
            allow_update = False
            break
        else:
            print('输入有误, 请重新输入!')
    if allow_update:
        print('ASN 数据库下载地址:', db_asn_url)
        res_asn = download_geo_db(db_asn_url, GEO2ASN_DB_PATH, proxy)
        print('CITY 数据库下载地址:', db_city_url)
        res_city = download_geo_db(db_city_url, GEO2CITY_DB_PATH, proxy)
        if res_asn and res_city:
            save_version(current_version)


if __name__ == '__main__':
    get_info()