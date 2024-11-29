#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from typing import List
from ipcheck.app.config import Config
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.ip_parser import IpParser
from ipcheck.app.geo_utils import get_geo_info
import random

# 生成ip 列表
def gen_ip_list(shuffle=True):
    config = Config()
    ip_list = gen_ip_list_by_arg(config.ip_source)
    ip_list = list(dict.fromkeys(ip_list))
    if shuffle:
        random.shuffle(ip_list)
    return ip_list

def gen_ip_list_by_arg(sources) -> List[IpInfo]:
    ip_parser = IpParser(sources)
    ip_list = ip_parser.parse()
    ip_list = get_geo_info(ip_list)
    config = Config()
    if config.skip_all_filters:
        return ip_list
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