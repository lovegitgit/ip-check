#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import importlib_metadata
from enum import Enum, auto


metadata = importlib_metadata.metadata("ip-check")
__version__ = metadata['version']


IP_CHECK_DEF_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config-ex.ini')
IP_CHECK_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.ini')

USER_AGENTS = [
    # === Windows / Chrome 系列 ===
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',

    # === Windows / Edge 系列 ===
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',

    # === Firefox 系列 ===
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0',

    # === macOS / Safari ===
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',

    # === Android / Chrome ===
    'Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Samsung Galaxy S22) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 11; Mi 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',

    # === iOS / Safari ===
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',

    # === Opera 浏览器 ===
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/95.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/95.0.0.0',

    # === Linux / Chrome ===
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',
]


# igeo constants
GEO2CITY_DB_NAME = 'GeoLite2-City.mmdb'
GEO2ASN_DB_NAME = 'GeoLite2-ASN.mmdb'
GEO2CITY_DB_PATH = os.path.join(os.path.dirname(__file__), GEO2CITY_DB_NAME)
GEO2ASN_DB_PATH = os.path.join(os.path.dirname(__file__), GEO2ASN_DB_NAME)
GEO_DEF_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'geo-ex.ini')
GEO_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'geo.ini')
GEO_VERSION_PATH = os.path.join(os.path.dirname(__file__), '.geo_version')


class WorkMode(Enum):
    IP_CHECK = auto()
    IP_CHECK_CFG = auto()
    IGEO_INFO = auto()
    IGEO_DL = auto()
    IGEO_CFG = auto()
    IP_FILTER = auto()
    DEFAULT = IP_CHECK

class IpcheckStage():
    UNKNOWN = 0
    VALID_TEST = 1
    RTT_TEST = 2
    SPEED_TEST = 3
    TEST_EXIT = 4