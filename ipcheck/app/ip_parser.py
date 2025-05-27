#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from concurrent.futures import ThreadPoolExecutor
from os import path
import random
import socket
import ipaddress
from typing import Iterable
from ipcheck import GEO2CITY_DB_NAME, GEO2ASN_DB_NAME, WorkMode
from ipcheck.app.config import Config
from ipcheck.app.geo_utils import get_geo_info
from ipcheck.app.statemachine import StateMachine
from ipcheck.app.utils import is_ip_network, get_net_version, is_valid_port, is_hostname, get_resolve_ips, is_ip_address, get_current_ts, floyd_sample
from ipcheck.app.ip_info import IpInfo


def filter_ip_list_by_locs(ip_list: Iterable[IpInfo], prefer_locs: Iterable[str]):
    if not StateMachine().geo_loc_avaiable:
        print('{} 数据库不可用, 跳过地区过滤... ...'.format(GEO2CITY_DB_NAME))
        return ip_list
    fixed_list = []
    for ip_info in ip_list:
        for loc in prefer_locs:
            if loc.upper().replace('_', '').replace(' ', '') in ip_info.country_city.upper().replace('_', ''):
                fixed_list.append(ip_info)
                break
    return fixed_list

def filter_ip_list_by_orgs(ip_list: Iterable[IpInfo], prefer_orgs: Iterable[str]):
    if not StateMachine().geo_asn_org_avaiable:
        print('{} 数据库不可用, 跳过org 过滤... ...'.format(GEO2ASN_DB_NAME))
        return ip_list
    fixed_list = []
    for ip_info in ip_list:
        for org in prefer_orgs:
            if org.upper().replace(' ', '').replace('-', '') in ip_info.org.upper().replace(' ', '').replace('-', ''):
                fixed_list.append(ip_info)
                break
    return fixed_list

def filter_ip_list_by_block_orgs(ip_list: Iterable[IpInfo], block_orgs: Iterable[str]):
    if not StateMachine().geo_asn_org_avaiable:
        print('{} 数据库不可用, 跳过org过滤... ...'.format(GEO2ASN_DB_NAME))
        return ip_list
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

class IpParser:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.args = self.__parse_sources()

    def parse(self):
        ip_set = set()
        t1 = get_current_ts()
        host_name_args = set()
        # 先用ip 表达式解析
        for arg in self.args:
            ips = parse_ip_by_ip_expr(arg, self.config)
            if ips:
                ip_set.update(ips)
            else:
                host_name_args.add(arg)
        # 接着适用域名解析
        if host_name_args:
            with ThreadPoolExecutor(max_workers=16) as executor:
                results = list(executor.map(lambda arg: parse_ip_by_host_name(arg, self.config), host_name_args))
                for result in results:
                    if result:
                        ip_set.update(result)
        t2 = get_current_ts()
        if StateMachine().work_mode == WorkMode.IP_CHECK:
            print('解析ip 耗时: {}秒'.format(round(t2 - t1, 2)))
        ip_set = get_geo_info(ip_set)
        t3 = get_current_ts()
        if StateMachine().work_mode == WorkMode.IP_CHECK:
            print('获取geo 信息耗时: {}秒'.format(round(t3 - t2, 2)))
        if StateMachine().work_mode == WorkMode.IGEO_INFO:
            return ip_set
        if self.config.ro_prefer_orgs:
            ip_set = filter_ip_list_by_orgs(ip_set, self.config.ro_prefer_orgs)
        if self.config.ro_block_orgs:
            ip_set = filter_ip_list_by_block_orgs(ip_set, self.config.ro_block_orgs)
        if self.config.ro_prefer_locs:
            ip_set = filter_ip_list_by_locs(ip_set, self.config.ro_prefer_locs)
        t4 = get_current_ts()
        if StateMachine().work_mode == WorkMode.IP_CHECK:
            print('预处理ip 总计耗时: {}秒'.format(round(t4 - t1, 2)))
        return ip_set

    def __parse_sources(self):
        args = []
        for arg in self.config.ro_ip_source:
            if path.exists(path.join(arg)) and path.isfile(path.join(arg)):
                with open(path.join(arg), 'r', encoding='utf-8') as f:
                    for line in f.readlines():
                        line = line.strip()
                        if line and not line.startswith('#'):
                            args.append(line)
            else:
                args.append(arg)
        return args

def is_allow_in_wb_list(ip_str: str, config: Config):
    if config.ro_white_list:
        for line in config.ro_white_list:
            if ip_str.startswith(line):
                return True
        return False
    if config.ro_block_list:
        blocked = False
        for line in config.ro_block_list:
            if ip_str.startswith(line):
                blocked = True
                break
        return not blocked
    return True

def is_allow_in_v4_v6(ip_str: str, config: Config):
    if config.ro_only_v4 ^ config.ro_only_v6:
        if config.ro_only_v4:
            return get_net_version(ip_str) == 4
        elif config.ro_only_v6:
            return get_net_version(ip_str) == 6
    else:
        return True

def is_port_allowed(port_str: int, config: Config):
    if not is_valid_port(port_str):
        return False
    if not config.ro_prefer_ports:
        return True
    port = int(port_str)
    return port in config.ro_prefer_ports

def parse_ip_by_ip_expr(arg: str, config: Config):
    def parse_ip():
        lst = []
        ip_str = arg
        if ip_str.startswith('[') and ip_str.endswith(']'):
            ip_str = arg[1: -1]
        if is_ip_address(ip_str) and is_allow_in_wb_list(ip_str, config) and is_allow_in_v4_v6(ip_str, config):
            lst = [IpInfo(ip_str, config.ip_port)]
        return lst

    def parse_cidr():
        lst = []
        if is_ip_network(arg) and is_allow_in_v4_v6(arg, config):
            net = ipaddress.ip_network(arg, strict=False)
            num_hosts = net.num_addresses
            # 针对igeo-info 仅返回一个ip
            if StateMachine().work_mode == WorkMode.IGEO_INFO:
                sample_size = 1
            # 避免cidr 过大导致的运行时间过久
            else:
                sample_size = min(config.cidr_sample_ip_num, num_hosts)
            if num_hosts < 2 ** 32:
                indexes = random.sample(range(0, num_hosts), sample_size)
            else:
                indexes = floyd_sample(num_hosts, sample_size)
            random_hosts = [ipaddress.ip_address(net.network_address + index) for index in indexes]
            lst = [IpInfo(str(ip), config.ip_port) for ip in random_hosts if is_allow_in_wb_list(str(ip), config)]
        return lst

    def parse_ip_port():
        lst = []
        if ':' in arg:
            index = arg.rindex(':')
            ip_part = arg[:index]
            if ip_part.startswith('[') and ip_part.endswith(']'):
                ip_part = ip_part[1: -1]
            port_part = arg[index + 1:]
            if is_port_allowed(port_part, config) and is_ip_address(ip_part) and is_allow_in_wb_list(ip_part, config) and is_allow_in_v4_v6(ip_part, config):
                lst = [IpInfo(ip_part, int(port_part))]
        return lst

    for fn in parse_ip, parse_cidr, parse_ip_port:
        parse_list = fn()
        if parse_list:
            return parse_list
    return []

# parse hostname, eg: example.com
def parse_ip_by_host_name(arg: str, config: Config):
    resolve_ips = []
    if is_hostname(arg):
        if config.ro_only_v4 ^ config.ro_only_v6:
            if config.ro_only_v4:
                resolve_ips.extend(get_resolve_ips(arg, config.ip_port, socket.AF_INET))
            elif config.ro_only_v6:
                resolve_ips.extend(get_resolve_ips(arg, config.ip_port, socket.AF_INET6))
        else:
            resolve_ips.extend(get_resolve_ips(arg, config.ip_port, socket.AF_INET))
            resolve_ips.extend(get_resolve_ips(arg, config.ip_port, socket.AF_INET6))
    ip_list = [IpInfo(ip, config.ip_port, hostname=arg) for ip in resolve_ips if is_allow_in_wb_list(ip, config)]
    return ip_list
