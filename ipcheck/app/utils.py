#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import functools
import ipaddress
import os
import random
from datetime import datetime
import shutil
import sys
from urllib.parse import urlparse
import requests
from tqdm import tqdm
import re
import socket
import asyncio
import time
import threading
import queue
import builtins
import unicodedata


class UniqueListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # 去重并保留顺序
        unique = list(dict.fromkeys(values))
        setattr(namespace, self.dest, unique)

def run_async_in_thread(coro):
    """在子线程中运行 asyncio 协程"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def is_ip_address(ip_str: str):
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip is not None
    except ValueError:
        return False

def parse_url(url: str):
    parsed_url = urlparse(url)
    return parsed_url.hostname, (parsed_url.path + ('?' + parsed_url.query if parsed_url.query else ''))

def is_ip_network(net_str: str):
    try:
        net = ipaddress.ip_network(net_str, strict=False)
        return net is not None
    except ValueError:
        return False


def get_ip_version(ip_str: str):
    ip = ipaddress.ip_address(ip_str)
    return ip.version

def get_net_version(net_str: str):
    net = ipaddress.ip_network(net_str, strict=False)
    return net.version

def is_hostname(name):
    pattern = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$"
    return re.match(pattern, name) is not None

async def async_hostname_lookup(hostname: str, port: int = 80, family=socket.AF_UNSPEC, print_err=False):
    """
    异步解析主机名，支持 A 和 AAAA 记录
    :param hostname: 要解析的域名
    :param port: 端口号
    :param family: 地址族，支持 socket.AF_INET, socket.AF_INET6, 或 socket.AF_UNSPEC（全部）
    :return: List of (family, address)
    """
    loop = asyncio.get_running_loop()
    results = []
    try:
        addr_info = await loop.getaddrinfo(
            host=hostname,
            port=port,
            family=family,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
            flags=socket.AI_ADDRCONFIG
        )
        results = [info[4][0] for info in addr_info]
    except (socket.gaierror, OSError):
        if print_err:
            console_print(f'resolve {hostname} error!')
    return results

def hostname_lookup(hostname: str, port: int = 80, family=socket.AF_UNSPEC, print_err=False):
    results = []
    try:
        addr_info = socket.getaddrinfo(
            host=hostname,
            port=port,
            family=family,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
            flags=socket.AI_ADDRCONFIG
        )
        results = [info[4][0] for info in addr_info]
    except (socket.gaierror, OSError):
        if print_err:
            console_print(f'resolve {hostname} error!')
    return results

def get_resolve_ips(hostname, port, family=socket.AF_UNSPEC):
    return hostname_lookup(hostname, port, family)

def is_valid_port(port_str):
    try:
        port = int(port_str)
        return 0 < port <= 65535
    except ValueError:
        return False


def find_txt_in_dir(dir):
    L = []
    if os.path.isdir(dir):
        for f in os.listdir(dir):
            file = os.path.join(dir, f)
            if os.path.isfile(file) and file.endswith('.txt'):
                L.append(file)
    return L

def floyd_sample(n: int, k: int):
    selected = {}
    result = set()
    if n <= k:
        return set(range(n))

    if k > n // 2:
        while len(result) < k:
            result.add(random.randint(0, n - 1))
    else:
        for i in range(n - k, n):
            r = random.randint(0, i)
            val = selected.get(r, r)
            selected[r] = selected.get(i, i)
            result.add(val)

    return result

# 通过指定目标list 大小, 从src_list 生成新的list
def adjust_list_by_size(src_list: list, target_size):
    if (target_size > len(src_list)):
        return src_list
    if target_size < 2 ** 32:
        return random.sample(src_list, target_size)
    else:
        total_size = len(src_list)
        indexes = floyd_sample(total_size, target_size)
        return [src_list[i] for i in indexes]


def gen_time_desc():
    current_time = datetime.now()
    # 格式化时间为字符串, 精确到秒
    return '{}: {}'.format('生成时间为', current_time.strftime("%Y-%m-%d %H:%M:%S"))


def singleton(cls):
    """
    将一个类作为单例
    来自 https://wiki.python.org/moin/PythonDecoratorLibrary#Singleton
    """

    cls.__new_original__ = cls.__new__

    @functools.wraps(cls.__new__)
    def singleton_new(cls, *args, **kw):
        it = cls.__dict__.get('__it__')
        if it is not None:
            return it

        if cls.__new_original__ is object.__new__:
            cls.__it__ = it = cls.__new_original__(cls)
        else:
            cls.__it__ = it = cls.__new_original__(cls, *args, **kw)
        it.__init_original__(*args, **kw)
        return it

    cls.__new__ = singleton_new
    cls.__init_original__ = cls.__init__
    cls.__init__ = object.__init__

    return cls

@singleton
class FreshablePrinter:
    def __init__(self, maxsize: int = 1):
        self._queue = queue.Queue(maxsize=maxsize)
        self._thread = None
        self._lock = threading.Lock()
        # 控制台 I/O 可能在同一调用栈内重入（例如 console_print -> stdout.write），使用可重入锁避免死锁。
        self._io_lock = threading.RLock()
        self._last_cols = 0
        self._line_open = False
        self._raw_stdout = sys.stdout

    def _worker(self):
        while True:
            content = self._queue.get()
            # 只保留并输出最新的一条，避免高并发下控制台输出积压
            while True:
                try:
                    content = self._queue.get_nowait()
                except queue.Empty:
                    break
            content = str(content)
            content_cols = _display_width(content)
            pad_len = max(0, self._last_cols - content_cols)
            # 回到行首重绘，打印后光标停在行尾。
            with self._io_lock:
                self._raw_stdout.write('\r' + content + (' ' * pad_len))
                self._raw_stdout.flush()
                self._last_cols = content_cols
                self._line_open = True

    def _ensure_started(self):
        if self._thread and self._thread.is_alive():
            return
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def _ensure_stdout_wrapper(self):
        if getattr(sys.stdout, '_freshaware_enabled', False):
            return
        with self._io_lock:
            if getattr(sys.stdout, '_freshaware_enabled', False):
                return
            self._raw_stdout = sys.stdout
            sys.stdout = _FreshAwareStdout(sys.stdout, self)

    def install(self):
        self._ensure_stdout_wrapper()

    def show(self, content: str):
        self._ensure_stdout_wrapper()
        self._ensure_started()
        try:
            self._queue.put_nowait(content)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(content)
            except queue.Full:
                pass

    def log(self, *args, **kwargs):
        self._ensure_stdout_wrapper()
        return self._raw_stdout_print(*args, **kwargs)

    def _raw_stdout_print(self, *args, **kwargs):
        kwargs.setdefault('file', sys.stdout)
        # 原子化整个 print，避免正文和换行被其他线程的 refresh 插入导致行内容错位。
        with self._io_lock:
            return builtins.print(*args, **kwargs)


freshable_printer = FreshablePrinter(maxsize=1)

def console_refresh(content: str):
    freshable_printer.show(content)

def console_print(*args, **kwargs):
    freshable_printer.log(*args, **kwargs)


class _FreshAwareStdout:
    def __init__(self, wrapped, printer):
        self._wrapped = wrapped
        self._printer = printer
        self._freshaware_enabled = True

    def write(self, data):
        if not data:
            return 0
        with self._printer._io_lock:
            # 如有刷新行未结束，普通输出前先擦除该行，避免把进度行固化为历史行。
            if self._printer._line_open and not data.startswith('\r'):
                self._wrapped.write('\r' + (' ' * self._printer._last_cols) + '\r')
                self._printer._line_open = False
                self._printer._last_cols = 0
            written = self._wrapped.write(data)
            if '\n' in data:
                self._printer._line_open = False
                self._printer._last_cols = 0
            return written

    def flush(self):
        return self._wrapped.flush()

    def __getattr__(self, item):
        return getattr(self._wrapped, item)


freshable_printer.install()

def write_file(content: str, path: str):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def copy_file(src: str, dst: str):
    try:
        shutil.copy2(src, dst)
    except Exception as e:
        raise RuntimeError(f'拷贝{src} 到{dst} 遇到错误: {e}')

def print_file_content(file_path: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for ct in f.readlines():
                console_print(ct, end='')
            console_print()
    except Exception as e:
        console_print(f'读取{file_path} 失败: {e}')

def download_file(url, path, proxy):
    # 发起请求并获取响应对象
    console_print('下载代理为: {}'.format(proxy))
    proxies = {}
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy
        }
    session = requests.Session()
    session.mount('https://', adapter=requests.adapters.HTTPAdapter(max_retries=5))
    try:
        with session.get(url, stream=True, timeout=10, proxies=proxies) as response:
            total_size = int(response.headers.get('content-length', 0))  # 获取文件总大小
            # 使用 tqdm 来显示进度条
            with open(path, 'wb') as file, tqdm(
                desc=path,
                total=total_size,
                unit='K',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                from ipcheck.app.statemachine import state_machine
                for data in response.iter_content(chunk_size=1024 * 16):
                    if state_machine.stop_event.is_set():
                        return False
                    # 写入文件并更新进度条
                    file.write(data)
                    bar.update(len(data))
                return True
    except Exception:
        return False

def get_json_from_net(url: str, proxy=None, verbose=True):
    from ipcheck.app.statemachine import state_machine
    res = {}
    if verbose:
        console_print('请求代理为: {}'.format(proxy))
    proxies = {}
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy
        }

    def fetch_json():
        nonlocal res
        session = requests.Session()
        session.mount('https://', adapter=requests.adapters.HTTPAdapter(max_retries=5))
        try:
            with session.get(url, stream=True, timeout=10, proxies=proxies) as r:
                res = r.json()
        except:
            pass
        finally:
            session.close()

    thread = threading.Thread(target=fetch_json, daemon=True)
    thread.start()

    # 在主线程中轮询，允许信号中断
    while thread.is_alive():
        if state_machine.stop_event.wait(0.1):
            return {}
        thread.join(timeout=0.1)

    return res

def get_perfcounter() -> float:
    return time.perf_counter()

def sleep_secs(secs: float):
    time.sleep(secs)

def get_family_addr(host, port):
    family = None
    sockaddr = None
    try:
        addr_info = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        family, _, _, _, sockaddr = addr_info[0]
    except:
        pass
    return family, sockaddr


def _display_width(text: str):
    width = 0
    for ch in text:
        if ch == '\t':
            width += 4
            continue
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return width
