#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# All static method startwith parse_ will parse ip

import inspect
from os import path
import socket
import ipaddress
from types import BuiltinFunctionType
from typing import List
from ipcheck.app.config import Config
from ipcheck.app.utils import is_ip_network, get_net_version, is_valid_port, is_hostname, get_resolve_ips, is_ip_address
from ipcheck.app.ip_info import IpInfo

class IpParser:
    def __init__(self, ins: list) -> None:
        self.args = self.__parse_args_from_ins(ins)

    def parse(self):
        ip_list = []
        parse_method_names = [name for name, member in inspect.getmembers(self) if callable(member) and not name.startswith("__") and name.startswith("parse_")]
        parse_methods = [getattr(self, method) for method in parse_method_names]
        for arg in self.args:
            for fn in parse_methods:
                ips = fn(arg)
                if ips:
                    ip_list.extend(ips)
                    break
        return ip_list

    def __parse_args_from_ins(self, ins: List[str]):
        args = []
        for arg in ins:
            if path.exists(path.join(arg)) and path.isfile(path.join(arg)):
                with open(path.join(arg), 'r', encoding='utf-8') as f:
                    for line in f.readlines():
                        line = line.strip()
                        if line and not line.startswith('#'):
                            args.append(line)
            else:
                args.append(arg)
        return args

    # parse ip cidr, eg: 1.2.0.1/24, 1.2.0.1(1.2.0.1/32)
    # @staticmethod
    # def parse_ip_cidr(arg: str):
    #     ip_list = []
    #     if is_ip_network(arg) and not is_ip_address(arg):
    #         if Config().skip_all_filters:
    #             return ip_list
    #     if is_ip_network(arg):
    #         config = Config()
    #         net = ipaddress.ip_network(arg, strict=False)
    #         hosts = list(net.hosts())
    #         if ((config.only_v4 and config.only_v6) or
    #             (config.only_v4 and get_net_version(arg) == 4) or
    #             (config.only_v6 and get_net_version(arg) == 6)):
    #             ip_list = [IpInfo(str(ip), config.ip_port) for ip in hosts]
    #     return ip_list

    # parse ip:port,eg 1.2.3.4:443
    @staticmethod
    def parse_ip_port(arg: str):
        def is_allow_in_wb_list(ip_str: str):
            if config.white_list:
                for line in config.white_list:
                    if arg.startswith(line):
                        return True
            if config.block_list:
                blocked = False
                for line in config.block_list:
                    if arg.startswith(line):
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
            try:
                port = int(port_str)
            except:
                return False
            if config.prefer_ports:
                return port in config.prefer_ports
            return True

        def parse_ip():
            lst =[]
            if is_ip_address(arg) and is_allow_in_wb_list(arg) and is_allow_in_v4_v6(arg):
                lst = [IpInfo(arg, config.ip_port)]
            return lst

        def parse_cidr():
            lst = []
            if is_ip_network(arg) and is_allow_in_wb_list(arg) and is_allow_in_v4_v6(arg):
                # 针对igeo-info 仅返回一个ip
                if config.skip_all_filters:
                    lst = [IpInfo(arg.split('/')[0], config.ip_port)]
                else:
                    net = ipaddress.ip_network(arg, strict=False)
                    hosts = list(net.hosts())
                    lst = [IpInfo(str(ip), config.ip_port) for ip in hosts if is_allow_in_wb_list(str(ip))]
            return lst


        def parse_ip_port():
            lst = []
            parts = arg.split(':')
            if len(parts) == 2:
                ip_part = parts[0]
                port_part = parts[1]
                if is_port_allowed(port_part) and is_ip_address(ip_part) and is_allow_in_wb_list(ip_part) and is_allow_in_v4_v6(ip_part):
                    lst = [IpInfo(ip_part, int(port_part))]
            return lst

        ip_list = []
        arg = arg.replace('[', '').replace(']', '')
        config = Config()
        for fn in parse_ip, parse_cidr, parse_ip_port:
            parse_list = fn()
            if parse_list:
                ip_list.extend(parse_list)
                break
        return ip_list

    # parse hostname, eg: example.com
    @staticmethod
    def parse_host_name(arg: str):
        def is_allow_in_wb_list(ip_str: str):
            if config.white_list:
                for line in config.white_list:
                    if arg.startswith(line):
                        return True
            if config.block_list:
                blocked = False
                for line in config.block_list:
                    if arg.startswith(line):
                        blocked = True
                        break
                return not blocked
            return True

        config = Config()
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
        ip_list = [IpInfo(ip, config.ip_port) for ip in resolve_ips if is_allow_in_wb_list(ip)]
        return ip_list