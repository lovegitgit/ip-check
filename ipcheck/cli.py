#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import signal

from ipcheck import WorkMode, IpcheckStage
from ipcheck.app.statemachine import state_machine
from ipcheck.app.utils import get_perfcounter


def signal_handler(sig, frame):
    cur_ts = get_perfcounter()
    ts_diff = cur_ts - state_machine.last_user_inject_ts
    state_machine.last_user_inject_ts = cur_ts
    if ts_diff < 1.5:
        os._exit(0)
    if state_machine.work_mode == WorkMode.IP_CHECK:
        if state_machine.ipcheck_stage == IpcheckStage.UNKNOWN:
            os._exit(0)
        if not state_machine.stop_event.is_set():
            if IpcheckStage.UNKNOWN < state_machine.ipcheck_stage < IpcheckStage.TEST_EXIT:
                state_machine.ipcheck_stage += 1
                state_machine.stop_event.set()
        return
    state_machine.stop_event.set()
    os._exit(0)


def install_signal_handler():
    signal.signal(signal.SIGINT, signal_handler)


def ip_check():
    install_signal_handler()
    from ipcheck import ip_check as ip_check_mod
    return ip_check_mod.main()


def ip_check_cfg():
    install_signal_handler()
    from ipcheck import ip_check as ip_check_mod
    return ip_check_mod.config_edit()


def igeo_info():
    install_signal_handler()
    from ipcheck import geoinfo as geoinfo_mod
    return geoinfo_mod.get_info()


def igeo_dl():
    install_signal_handler()
    from ipcheck import geoinfo as geoinfo_mod
    return geoinfo_mod.download_db()


def igeo_cfg():
    install_signal_handler()
    from ipcheck import geoinfo as geoinfo_mod
    return geoinfo_mod.config_edit()


def ip_filter():
    install_signal_handler()
    from ipcheck import geoinfo as geoinfo_mod
    return geoinfo_mod.filter_ips()
