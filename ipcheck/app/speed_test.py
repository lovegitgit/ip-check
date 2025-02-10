#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
from ipcheck.app.speed_test_config import SpeedTestConfig
from ipcheck.app.statemachine import StateMachine
from ipcheck.app.utils import adjust_list_by_size, show_freshable_content
import threading
import urllib3
from ipcheck.app.ip_info import IpInfo
import time
import random
from ipcheck import USER_AGENTS

urllib3.disable_warnings()


class SpeedTest:

    def __init__(self, ip_list: List[IpInfo], config: SpeedTestConfig) -> None:
        self.ip_list = ip_list
        self.config = config

    def run(self) -> List[IpInfo]:
        if not self.config.enabled:
            print('跳过速度测试')
            return self.ip_list
        StateMachine.clear()
        print('准备测试下载速度 ... ...')
        print('是否使用user-agent: {}'.format(self.config.user_agent))
        if len(self.ip_list) > self.config.ip_limit_count:
            print('待测试ip 过多, 当前最大限制数量为{} 个, 压缩中... ...'.format(self.config.ip_limit_count))
            self.ip_list = adjust_list_by_size(self.ip_list, self.config.ip_limit_count)
        print('正在测试ip 下载速度, 总数为{}'.format(len(self.ip_list)))
        total_num = len(self.ip_list)
        passed_ips = []
        for i in range(total_num):
            test_ip_info = self.ip_list[i]
            print('正在测速第{}/{}个ip: {}:{} {}_{} rtt {} ms'.format(i + 1,
                                                             total_num,
                                                             test_ip_info.ip_str,
                                                             test_ip_info.port,
                                                             test_ip_info.loc,
                                                             test_ip_info.colo,
                                                             test_ip_info.rtt))
            max_speed, avg_speed = self.__test(test_ip_info)
            test_ip_info.max_speed = max_speed
            test_ip_info.avg_speed = avg_speed
            StateMachine.cache(test_ip_info)
            print('{}:{} loss {}% rtt {} ms 下载速度(max/avg)为 {}/{} kB/s'.format(test_ip_info.ip_str,
                                                                                test_ip_info.port,
                                                                                test_ip_info.loss,
                                                                                test_ip_info.rtt,
                                                                                max_speed,
                                                                                avg_speed))
            if max_speed > self.config.download_speed and avg_speed > self.config.avg_download_speed:
                passed_ips.append(test_ip_info)
            if self.config.bt_ip_limit > 0 and len(passed_ips) >= self.config.bt_ip_limit:
                break
        return passed_ips


    def __test(self, ip_info : IpInfo):
        size = 0
        download_exit = False
        stop_signal = False
        max_speed = 0
        avg_speed = 0

        def download():
            nonlocal download_exit
            pool = urllib3.HTTPSConnectionPool(
                ip_info.ip,
                assert_hostname=self.config.host_name,
                server_hostname=self.config.host_name,
                port=ip_info.port,
                cert_reqs='CERT_NONE')
            headers = {
                'Host': self.config.host_name,
            }
            if self.config.user_agent:
                headers.update({'User-Agent': random.choice(USER_AGENTS)})
            try:
                r = pool.urlopen('GET', self.config.file_path,
                                 redirect=True,
                                 headers=headers,
                                 assert_same_host=False,
                                 timeout=self.config.timeout,
                                 preload_content=False,
                                 retries=urllib3.util.Retry(self.config.max_retry, backoff_factor=self.config.retry_factor))
                nonlocal size
                for chunk in r.stream():
                    size += len(chunk)
                    if stop_signal:
                        break
                r.release_conn()
            except:
                pass
            download_exit = True

        def cal_speed():
            nonlocal size, stop_signal, max_speed, avg_speed
            original_start = time.time()
            real_start = original_start
            start = original_start
            old_size = size
            while not download_exit:
                time.sleep(0.1)
                end = time.time()
                if end - start > 0.9:
                    cur_size = size
                    if cur_size == 0:
                        real_start = end
                        if end - original_start > self.config.download_time * 0.5:
                            stop_signal = True
                            break
                        continue
                    speed_now = int((cur_size - old_size) / ((end - start) * 1024))
                    avg_speed = int(cur_size / ((end - real_start) * 1024))
                    content = '  当前下载速度(cur/avg)为: {}/{} kB/s'.format(speed_now, avg_speed)
                    show_freshable_content(content)
                    if speed_now > max_speed:
                        max_speed = speed_now
                    start = end
                    old_size = cur_size
                # 快速测速逻辑
                if self.config.fast_check:
                    if end - real_start > self.config.download_time * 0.5:
                        if max_speed < self.config.download_speed * 0.5 or avg_speed < self.config.avg_download_speed * 0.77:
                            stop_signal = True
                            break
                if end - real_start > self.config.download_time:
                    stop_signal = True
                    break
            check_start = time.time()
            while not download_exit:
                time.sleep(0.1)
                check_now = time.time()
                if check_now - check_start > 1:
                    break

        t1 = threading.Thread(target=download, daemon=True)
        t2 = threading.Thread(target=cal_speed)
        t1.start()
        t2.start()
        # t1.join()
        t2.join()
        return (max_speed, avg_speed)
