#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
from typing import List
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.ipparser.base_parser import BaseParser
from ipcheck.app.utils import is_hostname, get_resolve_ips

class HostnameParser(BaseParser):
    '''
    解析ip 格式
    '''

    def check_source_type(self) -> bool:
        return is_hostname(self.source)

    def parse(self) -> List[IpInfo]:
        ip_list = []
        if self.is_valid:
            ip_list.extend(IpInfo(ip, self.port, hostname=self.source) for ip in get_resolve_ips(self.source, self.port, socket.AF_INET))
            ip_list.extend(IpInfo(ip, self.port, hostname=self.source) for ip in get_resolve_ips(self.source, self.port, socket.AF_INET6))
        return ip_list
