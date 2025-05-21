#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ipcheck.app.utils import get_ip_version

class IpInfo:

    def __init__(self, ip,
                port=443,
                rtt=-1,
                loss=0,
                max_speed=-1,
                avg_speed=-1,
                loc=None,
                colo=None,
                country_city='NG-NG',
                org='NG',
                asn=0,
                network=None,
                hostname=None):
        self.ip = ip
        self.port = port
        self.rtt = rtt
        self.loss = loss
        self.max_speed = max_speed
        self.avg_speed = avg_speed
        self.loc = loc
        self.colo = colo
        self.country_city = country_city
        self.org = org
        self.asn=asn
        self.network=network
        self.hostname=hostname
        self.st_test_tag = ''

    def __str__(self) -> str:
        return '    {}:{}{} {}_{} {} loss: {}% rtt: {} ms, 下载速度为(max/avg): {}/{} kB/s'.format(self.ip_str, self.port, self.st_test_tag, self.loc, self.colo, self.geo_info, self.loss, self.rtt ,self.max_speed, self.avg_speed)

    def get_rtt_info(self) -> str:
        return '{}:{} {}_{} {} loss: {}% rtt: {} ms'.format(self.ip_str, self.port, self.loc, self.colo, self.geo_info, self.loss, self.rtt)

    def get_info(self) -> str:
        return '{}:{}{} {}_{} {} loss: {}% rtt: {} ms, 下载速度(max/avg)为: {}/{} kB/s'.format(self.ip_str, self.port, self.st_test_tag, self.loc, self.colo, self.geo_info, self.loss, self.rtt, self.max_speed, self.avg_speed)

    @property
    def geo_info_str(self) -> str:
        return '{} 归属: {} ASN: {} CIDR: {}'.format(self.ip_str, self.geo_info, self.asn, self.network)

    @property
    def geo_info(self) -> str:
        return '{}({})'.format(self.country_city, self.org)

    @property
    def ip_str(self) -> str:
        res = f'[{self.ip}]'if get_ip_version(self.ip) == 6 else self.ip
        if self.hostname:
            res = '{}({})'.format(self.hostname, res)
        return res

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, IpInfo):
            return __value.ip == self.ip and __value.port == self.port
        return False

    def __hash__(self) -> int:
        return hash((self.ip, self.port))