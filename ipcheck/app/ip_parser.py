#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from concurrent.futures import ThreadPoolExecutor
from os import path
import random
import socket
import ipaddress
from typing import List
from ipcheck.app.config import Config
from ipcheck.app.geo_utils import get_geo_info
from ipcheck.app.utils import is_ip_network, get_net_version, is_valid_port, is_hostname, get_resolve_ips, is_ip_address
from ipcheck.app.ip_info import IpInfo


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

class IpParser:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.args = self.__parse_sources()

    def parse(self):
        ip_list = []
        host_name_args = []
        # 先用ip 表达式解析
        for arg in self.args:
            ips = parse_ip_by_ip_expr(arg, self.config)
            if ips:
                ip_list.extend(ips)
            else:
                host_name_args.append(arg)
        # 接着适用域名解析
        if host_name_args:
            with ThreadPoolExecutor(max_workers=16) as executor:
                results = list(executor.map(lambda arg: parse_ip_by_host_name(arg, self.config), host_name_args))
                for result in results:
                    if result:
                        ip_list.extend(result)
        ip_list = list(dict.fromkeys(ip_list))
        ip_list = get_geo_info(ip_list)
        if self.config.skip_all_filters:
            return ip_list
        if self.config.prefer_orgs:
            ip_list = filter_ip_list_by_orgs(ip_list, self.config.prefer_orgs)
        if self.config.block_orgs:
            ip_list = filter_ip_list_by_block_orgs(ip_list, self.config.block_orgs)
        if self.config.prefer_locs:
            ip_list = filter_ip_list_by_locs(ip_list, self.config.prefer_locs)
        return ip_list

    def __parse_sources(self):
        args = []
        for arg in self.config.ip_source:
            if path.exists(path.join(arg)) and path.isfile(path.join(arg)):
                with open(path.join(arg), 'r', encoding='utf-8') as f:
                    for line in f.readlines():
                        line = line.strip()
                        if line and not line.startswith('#'):
                            args.append(line)
            else:
                args.append(arg)
        return args

def parse_ip_by_ip_expr(arg: str, config: Config):
    def is_allow_in_wb_list(ip_str: str):
        if config.white_list:
            for line in config.white_list:
                if ip_str.startswith(line):
                    return True
            return False
        if config.block_list:
            blocked = False
            for line in config.block_list:
                if ip_str.startswith(line):
                    blocked = True
                    break
            return not blocked
        return True

    def is_allow_in_v4_v6(ip_str: str):
        if config.only_v4 ^ config.only_v6:
            if config.only_v4:
                return get_net_version(ip_str) == 4
            elif config.only_v6:
                return get_net_version(ip_str) == 6
        else:
            return True

    def is_port_allowed(port_str: int):
        if not is_valid_port(port_str):
            return False
        if not config.prefer_ports:
            return True
        port = int(port_str)
        return port in config.prefer_ports

    def parse_ip():
        lst =[]
        ip_str = arg
        if ip_str.startswith('[') and ip_str.endswith(']'):
            ip_str = arg[1: -1]
        if is_ip_address(ip_str) and is_allow_in_wb_list(ip_str) and is_allow_in_v4_v6(ip_str):
            lst = [IpInfo(ip_str, config.ip_port)]
        return lst

    def parse_cidr():
        lst = []
        if is_ip_network(arg) and is_allow_in_wb_list(arg) and is_allow_in_v4_v6(arg):
            # 针对igeo-info 仅返回一个ip
            if config.skip_all_filters:
                lst = [IpInfo(arg.split('/')[0], config.ip_port)]
            else:
                net = ipaddress.ip_network(arg, strict=False)
                # 避免cidr 过大导致的运行时间过久
                num_hosts = net.num_addresses - 2
                sample_size = min(config.cidr_sample_ip_num, num_hosts)
                random_hosts = set()
                while len(random_hosts) < sample_size:
                    random_ip = ipaddress.ip_address(net.network_address + 1 + random.randint(0, num_hosts - 1))
                    random_hosts.add(random_ip)
                lst = [IpInfo(str(ip), config.ip_port) for ip in random_hosts if is_allow_in_wb_list(str(ip))]
        return lst

    def parse_ip_port():
        lst = []
        if ':' in arg:
            index = arg.rindex(':')
            ip_part = arg[:index]
            if ip_part.startswith('[') and ip_part.endswith(']'):
                ip_part = ip_part[1: -1]
            port_part = arg[index + 1:]
            if is_port_allowed(port_part) and is_ip_address(ip_part) and is_allow_in_wb_list(ip_part) and is_allow_in_v4_v6(ip_part):
                lst = [IpInfo(ip_part, int(port_part))]
        return lst

    ip_list = []
    for fn in parse_ip, parse_cidr, parse_ip_port:
        parse_list = fn()
        if parse_list:
            ip_list.extend(parse_list)
            break
    return ip_list

# parse hostname, eg: example.com
def parse_ip_by_host_name(arg: str, config: Config):
    def is_allow_in_wb_list(ip_str: str):
        if config.white_list:
            for line in config.white_list:
                if ip_str.startswith(line):
                    return True
            return False
        if config.block_list:
            blocked = False
            for line in config.block_list:
                if ip_str.startswith(line):
                    blocked = True
                    break
            return not blocked
        return True

    resolve_ips = []
    if is_hostname(arg):
        if config.only_v4 ^ config.only_v6:
            if config.only_v4:
                resolve_ips.extend(get_resolve_ips(arg, config.ip_port, socket.AF_INET))
            elif config.only_v6:
                resolve_ips.extend(get_resolve_ips(arg, config.ip_port, socket.AF_INET6))
        else:
            resolve_ips.extend(get_resolve_ips(arg, config.ip_port, socket.AF_INET))
            resolve_ips.extend(get_resolve_ips(arg, config.ip_port, socket.AF_INET6))
    ip_list = [IpInfo(ip, config.ip_port, hostname=arg) for ip in resolve_ips if is_allow_in_wb_list(ip)]
    return ip_list