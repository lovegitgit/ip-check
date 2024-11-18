#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ipcheck.app.base_config import BaseConfig

CONFIG_PREFIX = 'st_'

class SpeedTestConfig(BaseConfig):

    def get_config_prefix(self) -> str:
        return CONFIG_PREFIX