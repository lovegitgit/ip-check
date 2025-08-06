#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import socket
from typing import Iterable
from ipcheck import IpcheckStage
from ipcheck.app.rtt_test_config import RttTestConfig
from ipcheck.app.ip_info import IpInfo
from ipcheck.app.statemachine import StateMachine
from ipcheck.app.utils import adjust_list_by_size, get_perfcounter, show_freshable_content, get_family_addr, sleep_secs
from concurrent.futures import ThreadPoolExecutor, as_completed


class RttTest:

    def __init__(self, ip_list: Iterable[IpInfo], config: RttTestConfig) -> None:
        self.ip_list = ip_list
        self.config = config

    def run(self) -> Iterable[IpInfo]:
        if not self.config.enabled:
            print('跳过RTT测试')
            return self.ip_list
        StateMachine().ipcheck_stage = IpcheckStage.RTT_TEST
        StateMachine().user_inject = False
        StateMachine.clear()
        print('准备测试rtt ... ...')
        print('rtt ping 间隔为: {}秒'.format(self.config.interval))
        if len(self.ip_list) > self.config.ip_limit_count:
            print('待测试ip 过多, 当前最大限制数量为{} 个, 压缩中... ...'.format(self.config.ip_limit_count))
            self.ip_list = adjust_list_by_size(self.ip_list, self.config.ip_limit_count)
        total_count = len(self.ip_list)
        print('正在测试ip rtt, 总数为{}'.format(total_count))
        test_count = 0
        pass_count = 0
        passed_ips = []
        thread_pool_executor = ThreadPoolExecutor(max_workers=self.config.thread_num, thread_name_prefix="valid_")
        all_task = [thread_pool_executor.submit(self.__test, ip_info) for ip_info in self.ip_list]
        for future in as_completed(all_task):
            ip_info: IpInfo = future.result()
            test_count += 1
            if ip_info.rtt != -1:
                StateMachine.cache(ip_info)
                print(ip_info.get_rtt_info())
                if ip_info.rtt <= self.config.max_rtt and ip_info.loss <= self.config.max_loss:
                    passed_ips.append(ip_info)
                    pass_count += 1
            content = '  当前进度为: {}/{}, {} pass'.format(test_count, total_count, pass_count)
            show_freshable_content(content)
        thread_pool_executor.shutdown(wait=True)
        print('rtt 结果为: 总数{}, {} pass'.format(total_count, pass_count))
        return passed_ips

    def __test(self, ip_info: IpInfo) -> IpInfo:
        if StateMachine().ipcheck_stage != IpcheckStage.RTT_TEST:
            return ip_info
        return tcpping(ip_info,
                        count=self.config.test_count,
                        interval=self.config.interval,
                        timeout=self.config.timeout,
                        max_loss=self.config.max_loss,
                        max_rtt=self.config.max_rtt,
                        fast_check=self.config.fast_check)

async def async_tcpping(
    ipinfo,
    count: int = 2,
    timeout: float = 5,
    interval: float = 3,
    max_loss: float = 100,
    max_rtt: float = 10000,
    fast_check: bool = False,
    print_err: bool = False
):
    statemachine = StateMachine()
    rtts = []
    packets_sent = 0
    packets_lost = 0

    host = ipinfo.ip
    port = ipinfo.port
    family, sockaddr = get_family_addr(host, port)
    if not family:
        return ipinfo

    loop = asyncio.get_running_loop()
    for i in range(count):
        if statemachine.ipcheck_stage != IpcheckStage.RTT_TEST:
            return ipinfo
        if i > 0:
            await asyncio.sleep(interval)
        s = socket.socket(family=family, type=socket.SOCK_STREAM)
        s.setblocking(False)
        try:
            start = get_perfcounter()
            await asyncio.wait_for(loop.sock_connect(s, sockaddr), timeout)
            rtt = (get_perfcounter() - start)
            rtts.append(rtt)
            packets_sent += 1
        except (asyncio.TimeoutError, socket.gaierror, OSError) as e:
            if print_err:
                print(e)
            packets_lost += 1
        finally:
            s.close()
        if fast_check:
            if (packets_lost / count) * 100 > max_loss or (sum(rtts) * 1000 / (count - packets_lost)) > max_rtt:
                return ipinfo
        if statemachine.ipcheck_stage != IpcheckStage.RTT_TEST:
            return ipinfo
    if packets_sent == 0:
        return ipinfo
    ipinfo.rtt = round(sum(rtts) * 1000 / packets_sent, 2)
    ipinfo.loss = round((packets_lost / count) * 100, 2)
    return ipinfo

def tcpping(
    ipinfo,
    count: int = 2,
    timeout: float = 5,
    interval: float = 3,
    max_loss: float = 100,
    max_rtt: float = 10000,
    fast_check: bool = False,
    print_err: bool = False
):
    statemachine = StateMachine()
    rtts = []
    packets_sent = 0
    packets_lost = 0

    host = ipinfo.ip
    port = ipinfo.port
    family, sockaddr = get_family_addr(host, port)
    if not family:
        return ipinfo

    for i in range(count):
        if statemachine.ipcheck_stage != IpcheckStage.RTT_TEST:
            return ipinfo
        if i > 0:
            sleep_secs(interval)
        s = socket.socket(family=family, type=socket.SOCK_STREAM)
        s.setblocking(False)
        s.settimeout(timeout)
        try:
            start = get_perfcounter()
            s.connect(sockaddr)
            rtt = (get_perfcounter() - start)
            rtts.append(rtt)
            packets_sent += 1
        except (socket.timeout, OSError) as e:
            if print_err:
                print(e)
            packets_lost += 1
        finally:
            s.close()
        if count == packets_lost:
            return ipinfo
        if fast_check:
            if (packets_lost / count) * 100 > max_loss or (sum(rtts) * 1000 / (count - packets_lost)) > max_rtt:
                return ipinfo
        if statemachine.ipcheck_stage != IpcheckStage.RTT_TEST:
            return ipinfo
    if packets_sent == 0:
        return ipinfo
    ipinfo.rtt = round(sum(rtts) * 1000 / packets_sent, 2)
    ipinfo.loss = round((packets_lost / count) * 100, 2)
    return ipinfo