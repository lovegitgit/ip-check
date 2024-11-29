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
        ip_list = []
        config = Config()
        fixed_arg = arg
        if arg.startswith('[') and arg.endswith(']'):
            fixed_arg = arg[1: -1]
        ip_str = port_str = None
        if is_ip_address(fixed_arg):
            ip_str = fixed_arg
            port_str = config.ip_port
        elif is_ip_network(arg):
            ip_str = arg
            port_str = config.ip_port
        elif ':' in arg:
            index = arg.rindex(':')
            ip_str = arg[:index]
            if ip_str.startswith('[') and ip_str.endswith(']'):
                ip_str = ip_str[1: -1]
            port_str = arg[index + 1:]
        if is_ip_network(ip_str):
            port = int(port_str) if is_valid_port(port_str) else config.ip_port
            # config.skip_all_filters 仅仅被igeo-info 设置
            # 针对igeo-info 读取纯cidr 我们只返回第一个ip
            if not is_ip_address(ip_str) and config.skip_all_filters:
                sub_index = ip_str.rindex('/')
                first_ip = ip_str[: sub_index]
                ip_list = [IpInfo(first_ip, port)]
            else:
                net = ipaddress.ip_network(ip_str, strict=False)
                hosts = list(net.hosts())
                if ((config.only_v4 and config.only_v6) or
                    (config.only_v4 and get_net_version(ip_str) == 4) or
                    (config.only_v6 and get_net_version(ip_str) == 6)):
                    ip_list = [IpInfo(str(ip), port) for ip in hosts]
        return ip_list

    # parse hostname, eg: example.com
    @staticmethod
    def parse_host_name(arg: str):
        ip_list = []
        if is_hostname(arg):
            config = Config()
            if (config.only_v4 and config.only_v6):
                ip_list.extend(IpInfo(ip, config.ip_port, hostname=arg) for ip in get_resolve_ips(arg, config.ip_port, socket.AF_INET))
                ip_list.extend(IpInfo(ip, config.ip_port, hostname=arg) for ip in get_resolve_ips(arg, config.ip_port, socket.AF_INET6))
            elif config.only_v4:
                ip_list.extend(IpInfo(ip, config.ip_port, hostname=arg) for ip in get_resolve_ips(arg, config.ip_port, socket.AF_INET))
            elif config.only_v6:
                ip_list.extend(IpInfo(ip, config.ip_port, hostname=arg) for ip in get_resolve_ips(arg, config.ip_port, socket.AF_INET6))
        return ip_list