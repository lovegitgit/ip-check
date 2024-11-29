#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
from ipcheck.app.config import Config
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.ipparser.base_parser import BaseParser
from ipcheck.app.utils import is_ip_address, get_ip_version

class IpParser(BaseParser):
    '''
    解析ip 格式
    '''

    def check_source_type(self) -> bool:
        return is_ip_address(self.source)

    def parse(self) -> List[IpInfo]:
        ip_list = []
        if self.is_valid:
            ip_list.append(IpInfo(self.source, self.port))
        return ip_list

    def extra_check(self) -> bool:
        config = Config()
        if config.only_v4 == config.only_v6:
            return True
        elif config.only_v4:
            return get_ip_version(self.source) == 4
        elif config.only_v6:
            return get_ip_version(self.source) == 6