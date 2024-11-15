#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.config import Config

class BaseParser:

    def __init__(self, source: str) -> None:
        self.source = source
        self.port = Config().ip_port
        self.extra_init()

    @property
    def is_valid(self) -> bool:
        return self.check_source_type() and self.is_source_valid() and self.extra_check()

    def parse(self) -> List[IpInfo]:
        return []

    def check_source_type(self) -> bool:
        return False

    def is_source_valid(self) -> bool:
        if Config().skip_all_filters:
            return True
        if Config().white_list:
            for expr_str in Config().white_list:
                if self.source.startswith(expr_str):
                    return True
            return False
        if Config().block_list:
            for expr_str in Config().block_list:
                if self.source.startswith(expr_str):
                    return False
            return True
        return True

    # 额外判断项目
    def extra_check(self) -> bool:
        return True

    def extra_init(self):
        pass