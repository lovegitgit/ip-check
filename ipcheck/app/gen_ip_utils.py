#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from typing import List
from ipcheck.app.config import Config
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.ipparser.ip_dir_parser import IpDirParser
from ipcheck.app.ipparser.ip_file_parser import IpFileParser
from ipcheck.app.ipparser.ip_cidr_parser import IpCidrParser
from ipcheck.app.ipparser.ip_parser import IpParser
from ipcheck.app.ipparser.ip_port_parser import IpPortParser
from ipcheck.app.ipparser.hostname_parser import HostnameParser
from ipcheck.app.geo_utils import get_geo_info
import random

# 生成ip 列表
def gen_ip_list(shuffle=True):
    config = Config()
    ip_list = []
    for source in config.ip_source:
        ip_list.extend(gen_ip_list_by_arg(source))
    ip_list = list(dict.fromkeys(ip_list))
    if shuffle:
        random.shuffle(ip_list)
    return ip_list


def gen_ip_list_by_arg(source) -> List[IpInfo]:
    ip_list = []
    parsers = [IpDirParser(source), IpFileParser(source), IpParser(source), IpCidrParser(source), IpPortParser(source), HostnameParser(source)]
    for parser in parsers:
        if parser.is_valid:
            ips = parser.parse()
            ip_list.extend(ips)
            break
    ip_list = get_geo_info(ip_list)
    config = Config()
    if config.skip_all_filters:
        return ip_list
    if config.white_list:
        ip_list = filter_ip_list_by_white_list(ip_list, config.white_list)
    if config.block_list:
        ip_list = filter_ip_list_by_block_list(ip_list, config.block_list)
    if config.prefer_orgs:
        ip_list = filter_ip_list_by_orgs(ip_list, config.prefer_orgs)
    if config.block_orgs:
        ip_list = filter_ip_list_by_block_orgs(ip_list, config.block_orgs)
    if config.prefer_locs:
        ip_list = filter_ip_list_by_locs(ip_list, config.prefer_locs)
    return ip_list

def filter_ip_list_by_white_list(ip_list: List[IpInfo], white_list):
    fixed_list = []
    for ip_info in ip_list:
        for pref_str in white_list:
            if ip_info.ip.startswith(pref_str):
                fixed_list.append(ip_info)
                break
    return fixed_list

def filter_ip_list_by_block_list(ip_list: List[IpInfo], block_list):
    fixed_list = []
    for ip_info in ip_list:
        is_valid = True
        for block_str in block_list:
            if ip_info.ip.startswith(block_str):
                is_valid = False
                break
        if is_valid:
            fixed_list.append(ip_info)
    return fixed_list

def filter_ip_list_by_locs(ip_list: List[IpInfo], prefer_locs: List[str]):
    fixed_list = []
    for ip_info in ip_list:
        for loc in prefer_locs:
            if loc.upper().replace('_', '').replace(' ', '') in ip_info.country_city.upper().replace('_', ''):
                fixed_list.append(ip_info)
                break
    return fixed_list

def filter_ip_list_by_orgs(ip_list: List[IpInfo], prefer_orgs: List[str]):
    fixed_list = []
    for ip_info in ip_list:
        for org in prefer_orgs:
            if org.upper().replace(' ', '').replace('-', '') in ip_info.org.upper().replace(' ', '').replace('-', ''):
                fixed_list.append(ip_info)
                break
    return fixed_list

def filter_ip_list_by_block_orgs(ip_list: List[IpInfo], block_orgs: List[str]):
    fixed_list = []
    for ip_info in ip_list:
        is_valid = True
        for org in block_orgs:
            if org.upper().replace(' ', '').replace('-', '') in ip_info.org.upper().replace(' ', '').replace('-', ''):
                is_valid = False
                break
        if is_valid:
           fixed_list.append(ip_info)
    return fixed_list