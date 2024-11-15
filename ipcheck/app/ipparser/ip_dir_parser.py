#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.ipparser.base_parser import BaseParser
from os import path
from ipcheck.app.ipparser.ip_file_parser import IpFileParser
from ipcheck.app.utils import find_txt_in_dir

class IpDirParser(BaseParser):
    '''
    从目录中的文本中解析ip
    '''

    def check_source_type(self) -> bool:
        return path.exists(self.source) and path.isdir(self.source)

    def parse(self) -> List[IpInfo]:
        ip_list = []
        if self.is_valid:
            sources = find_txt_in_dir(self.source)
            for source in sources:
                parser = IpFileParser(source)
                ip_list.extend(parser.parse())
        return ip_list

    def is_source_valid(self) -> bool:
        return True