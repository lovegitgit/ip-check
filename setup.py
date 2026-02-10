#!/usr/bin/env python3

from setuptools import setup, find_packages
import os


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='ip-check',
    version='2.3.7',
    description='Powerful cdn network speed test utils.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="nobitaqaq",
    author_email="xiaoleigs@gmail.com",
    keywords=["cdn", "speed test", "network speed"],
    packages=find_packages(include=['ipcheck', 'ipcheck.app', 'ipcheck.app.*']),
    include_package_data=True,
    package_data={
        'ipcheck': ['config-ex.ini'],
        'ipcheck': ['geo-ex.ini'],
    },
    entry_points={
        'console_scripts': [
            'ip-check = ipcheck.cli:ip_check',
            'ip-check-cfg = ipcheck.cli:ip_check_cfg',
            'igeo-info = ipcheck.cli:igeo_info',
            'igeo-dl = ipcheck.cli:igeo_dl',
            'igeo-cfg = ipcheck.cli:igeo_cfg',
            'ip-filter = ipcheck.cli:ip_filter',
        ]
    },
    python_requires=">=3.8",
    install_requires=[
        'geoip2',
        'ipaddress',
        'requests',
        'requests[socks]',
        'tqdm',
        'urllib3 >= 2.2.3',
        'importlib-metadata',
    ],
)
