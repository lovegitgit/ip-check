#!/usr/bin/env python3

from setuptools import setup, find_packages
import os


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='ip-check',
    version='2.1.0',
    description='Powerful cdn network speed test utils.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="nobitaqaq",
    author_email="xiaoleigs@gmail.com",
    keywords=["cdn", "speed test", "network speed"],
    packages=find_packages(include=['ipcheck', 'ipcheck.app', 'ipcheck.app.*']),
    entry_points={
        'console_scripts': [
            'ip-check = ipcheck.main:main',
            'ip-check-cfg = ipcheck.main:config_edit',
            'igeo-info = ipcheck.geoinfo:get_info',
            'igeo-dl = ipcheck.geoinfo:download_db',
            'igeo-cfg = ipcheck.geoinfo:config_edit',
            'ip-filter = ipcheck.geoinfo:filter_ips',
        ]
    },
    python_requires=">=3.8",
    install_requires=[
        'geoip2',
        'ipaddress~=1.0.23',
        'requests',
        'requests[socks]',
        'tcppinglib~=2.0.3',
        'tqdm',
        'urllib3~=1.26.15',
        'importlib-metadata',
    ],
)
