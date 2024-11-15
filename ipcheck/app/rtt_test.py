#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
from ipcheck.app.rtt_test_config import RttTestConfig
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.statemachine import StateMachine
from ipcheck.app.utils import adjust_list_by_size
from concurrent.futures import ThreadPoolExecutor, as_completed
from tcppinglib import async_tcpping
import asyncio


class RttTest:

    def __init__(self, ip_list: List[IpInfo], config: RttTestConfig) -> None:
        self.ip_list = ip_list
        self.config = config
        StateMachine.clear()

    def run(self) -> List[IpInfo]:
        if not self.config.enabled:
            print('跳过RTT测试')
            return self.ip_list
        print('准备测试rtt ... ...')
        print('rtt ping 间隔为: {}秒'.format(self.config.interval))
        if len(self.ip_list) > self.config.ip_limit_count:
            print('待测试ip 过多, 当前最大限制数量为{} 个, 压缩中... ...'.format(self.config.ip_limit_count))
            self.ip_list = adjust_list_by_size(self.ip_list, self.config.ip_limit_count)
        print('正在测试ip rtt, 总数为{}'.format(len(self.ip_list)))
        passed_ips = []
        thread_pool_executor = ThreadPoolExecutor(
            max_workers=self.config.thread_num, thread_name_prefix="valid_")
        all_task = [thread_pool_executor.submit(
            self.__test, ip_info) for ip_info in self.ip_list]
        for future in as_completed(all_task):
            ip_info = future.result()
            if ip_info:
                StateMachine.cache(ip_info)
                print(ip_info.get_rtt_info())
                if ip_info.rtt <= self.config.max_rtt and ip_info.loss <= self.config.max_loss:
                    passed_ips.append(ip_info)
        thread_pool_executor.shutdown(wait=True)
        print('rtt 结果为: 总数{}, {} pass'.format(len(self.ip_list), len(passed_ips)))
        return passed_ips

    def __test(self, ip_info : IpInfo) -> IpInfo:
        return asyncio.run(self.host_specs(ip_info))

    async def host_specs(self, ip_info: IpInfo) -> IpInfo:
        ip = ip_info.ip if not ip_info.ip.startswith('[') else ip_info.ip[1: -1]
        host = await async_tcpping(ip,
                                   port=ip_info.port,
                                   count=self.config.test_count,
                                   interval=self.config.interval,
                                   timeout=self.config.timeout)
        if host.is_alive:
            ip_info.rtt = round(host.avg_rtt, 2)
            ip_info.loss = round(host.packet_loss)
            return ip_info
        else:
            return None