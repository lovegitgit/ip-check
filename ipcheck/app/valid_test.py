#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Iterable
from ipcheck import IpcheckStage
from ipcheck.app.statemachine import StateMachine
from ipcheck.app.valid_test_config import ValidTestConfig
from ipcheck.app.utils import adjust_list_by_size, show_freshable_content
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
from ipcheck.app.ip_info import IpInfo
urllib3.disable_warnings()

from ipcheck import USER_AGENTS
import random


class ValidTest:

    def __init__(self, ip_list: Iterable[IpInfo], config: ValidTestConfig) -> None:
        self.ip_list = ip_list
        self.config = config

    def run(self) -> Iterable[IpInfo]:
        if not self.config.enabled:
            print('跳过可用性测试')
            return self.ip_list
        StateMachine().ipcheck_stage = IpcheckStage.VALID_TEST
        StateMachine().user_inject = False
        StateMachine.clear()
        print('准备测试可用性 ... ...')
        if len(self.ip_list) > self.config.ip_limit_count:
            print('待测试ip 过多, 当前最大限制数量为{} 个, 压缩中... ...'.format(self.config.ip_limit_count))
            self.ip_list = adjust_list_by_size(self.ip_list, self.config.ip_limit_count)
        print('可用性域名为: {}'.format(self.config.host_name))
        print('是否使用user-agent: {}'.format(self.config.user_agent))
        total_count = len(self.ip_list)
        print('正在测试ip可用性, 总数为{}'.format(total_count))
        passed_ips = []
        thread_pool_executor = ThreadPoolExecutor(
            max_workers=self.config.thread_num, thread_name_prefix="valid_")
        all_task = [thread_pool_executor.submit(
            self.__test, ip_info) for ip_info in self.ip_list]
        test_count = 0
        pass_count = 0
        for future in as_completed(all_task):
            test_count += 1
            ret = future.result()
            if ret:
                pass_count += 1
                passed_ips.append(ret)
                StateMachine.cache(ret)
            content = '  当前进度为: {}/{}, {} pass'.format(test_count, total_count, pass_count)
            show_freshable_content(content)
        thread_pool_executor.shutdown(wait=True)
        print('可用性结果为: 总数{}, {} pass'.format(len(self.ip_list), len(passed_ips)))
        return passed_ips

    def __test(self, ip_info) -> None:
        if StateMachine().ipcheck_stage != IpcheckStage.VALID_TEST:
            return None
        check_key = self.config.check_key
        pool = urllib3.HTTPSConnectionPool(
                ip_info.ip, assert_hostname=self.config.host_name,
                server_hostname=self.config.host_name,
                port=ip_info.port, cert_reqs='CERT_NONE')
        res = None
        headers = {
            'Host': self.config.host_name,
        }
        if self.config.user_agent:
            headers.update({'User-Agent': random.choice(USER_AGENTS)})
        try:
            with pool.urlopen('GET', self.config.path,
                                               retries=urllib3.util.Retry(self.config.max_retry, backoff_factor=self.config.retry_factor),
                                               headers=headers,
                                               assert_same_host=False,
                                               timeout=self.config.timeout,
                                               preload_content=False,
                                               redirect=True) as r:
                if '/cdn-cgi/trace' == self.config.path:
                    req_dict = {}
                    for line in r.readlines():
                        line = line.decode('utf-8')
                        kv = line.strip().split('=')
                        req_dict.update({kv[0]: kv[1]})
                    if req_dict.get(check_key, None) == self.config.host_name:
                        loc = req_dict.get('loc', None)
                        colo = req_dict.get('colo', None)
                        ip_info.loc = loc
                        ip_info.colo = colo
                        res = ip_info
                elif r.status == 200:
                    res = ip_info
        except:
            pass
        return res
