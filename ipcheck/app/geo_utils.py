#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import configparser
import os
import geoip2.database
from typing import List
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.utils import download_file, write_file, get_json_from_net
import json

from ipcheck import GEO2CITY_DB_NAME, GEO2ASN_DB_NAME, GEO2CITY_DB_PATH, GEO2ASN_DB_PATH, GEO_CONFIG_PATH, GEO_DEFAULT_CONFIG, GEO_VERSION_PATH

def download_geo_db(url :str, path:str, proxy=None):
    print('正在下载geo database ... ...')
    res = download_file(url, path, proxy)
    result_str = '成功.' if res else '失败!'
    print('下载geo database到{} {}'.format(path, result_str))
    return res

def check_geo_loc_db():
    if os.path.exists(GEO2CITY_DB_PATH):
        return True
    else:
        print('ip 数据库不存在, 请手动下载{} 到 {}'.format(GEO2CITY_DB_NAME, GEO2CITY_DB_PATH))
        return False

def check_geo_asn_db():
    if os.path.exists(GEO2ASN_DB_PATH):
        return True
    else:
        print('ip 数据库不存在, 请手动下载{} 到 {}'.format(GEO2ASN_DB_NAME, GEO2ASN_DB_PATH))
        return False

def handle_blank_in_str(handle_str: str):
    res = handle_str
    if handle_str:
        res = handle_str.replace(' ', '_')
    return res


# 获取位置信息与组织
def get_geo_info(infos: List[IpInfo]) -> List[IpInfo]:
    if not check_geo_loc_db() or not check_geo_asn_db():
        raise Exception('IP 数据库不存在, 无法获取IP 归属地信息, 请检查!')
    res = []
    with geoip2.database.Reader(GEO2CITY_DB_PATH) as reader1, geoip2.database.Reader(GEO2ASN_DB_PATH) as reader2:
        for ipinfo in infos:
            ip = ipinfo.ip
            country, city = 'None', 'None'
            try:
                response1 = reader1.city(remove_ipv6_mark(ip))
                country = response1.country.name
                city = response1.city.name
            except Exception:
                pass
            country = handle_blank_in_str(country)
            city = handle_blank_in_str(city)
            org, asn, network = 'None', 'None', 'None'
            try:
                response2 = reader2.asn(remove_ipv6_mark(ip))
                org = response2.autonomous_system_organization
                asn = response2.autonomous_system_number
                network = response2.network
            except Exception:
                pass
            ipinfo.country_city = '{}-{}'.format(country, city)
            ipinfo.org = org
            ipinfo.asn = asn
            ipinfo.network = network
            res.append(ipinfo)
    return res

def remove_ipv6_mark(ip_str: str):
    if ip_str.startswith('[') and ip_str.endswith(']'):
        ip_str = ip_str[1: -1]
    return ip_str

def parse_geo_config():
    def get_option_safely(section: str, option: str, default_value=None):
        nonlocal parser
        if parser.has_option(section, option):
            return parser.get(section, option)
        else:
            return default_value

    parser = configparser.ConfigParser()
    parser.read(GEO_CONFIG_PATH, 'utf-8')
    db_asn_url = get_option_safely('common', 'db_asn_url')
    db_city_url = get_option_safely('common', 'db_city_url')
    proxy = get_option_safely('common', 'proxy')
    db_api_url = get_option_safely('common', 'db_api_url')
    return db_asn_url, db_city_url, proxy, db_api_url

def check_geo_version(api_url: str, proxy=None):
    def get_old_version():
        old_version = {}
        if os.path.exists(GEO_VERSION_PATH) and os.path.isfile(GEO_VERSION_PATH):
            try:
                with open(GEO_VERSION_PATH, encoding='utf-8') as f:
                    old_version = json.load(f)
            except:
                pass
        return old_version

    def get_current_version():
        return get_json_from_net(api_url, proxy)

    old_version = get_old_version()
    current_version = get_current_version()
    has_update = old_version.get('tag_name', 'old_tag') != current_version.get('tag_name', 'new_tag')
    return has_update, current_version


def save_version(version: json):
    with open(GEO_VERSION_PATH, 'w', encoding='utf-8') as f:
        json.dump(version, f, indent=4)

def check_or_gen_def_config():
    if not os.path.exists(GEO_CONFIG_PATH):
        print('警告: 配置文件不存在, 正在生成默认配置... ...')
        write_file(GEO_DEFAULT_CONFIG, GEO_CONFIG_PATH)
        print('配置文件已生成位于 {}, 请按需要修改!'.format(GEO_CONFIG_PATH))