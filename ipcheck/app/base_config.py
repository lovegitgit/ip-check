#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ipcheck.app.common_config import CommonConfig

class BaseConfig(CommonConfig):

    def __init__(self, config) -> None:
        self.gen_cf_common_part(config)
        self.gen_cf_extra_part(config)

    def get_config_prefix(self) -> str:
        return None

    def gen_cf_common_part(self, config):
        key_prefix = self.get_config_prefix()
        if not key_prefix:
            return
        variables = vars(config)
        for k, _ in variables.items():
            if k.startswith(key_prefix):
                expr_str = 'self.{} = config.{}'.format(k[len(key_prefix):], k)
                exec(expr_str)

    def gen_cf_extra_part(self, config):
        pass