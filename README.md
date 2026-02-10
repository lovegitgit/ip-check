# ip-check

高效的cdn 测速工具，用于ip 优选。

## Home Page

[Github](https://github.com/lovegitgit/ip-check)

## 安装与部署

```shell
pip install -U ip-check
# 按需修改ip-check 程序配置文件
ip-check-cfg
# 按需修改igeo-cfg GEO 数据库配置文件
igeo-cfg
# 下载mmdb 数据库
igeo-dl
```

note: 下载mmdb 数据库可能会失败，可以手动下载mmdb 数据库到`ip-check --version` 所输出的路径

## 使用方法

```shell
ip-check -h
usage: ip-check [-h] [-w WHITE_LIST [WHITE_LIST ...]] [-b BLOCK_LIST [BLOCK_LIST ...]] [-pl PREFER_LOCS [PREFER_LOCS ...]]
                [-po PREFER_ORGS [PREFER_ORGS ...]] [-bo BLOCK_ORGS [BLOCK_ORGS ...]] [-pp PREFER_PORTS [PREFER_PORTS ...]] [-lv MAX_VT_IP_COUNT]
                [-lr MAX_RT_IP_COUNT] [-ls MAX_ST_IP_COUNT] [-lb MAX_BT_IP_COUNT] [-p PORT] [-H HOST] [-dr] [-dv] [-ds] [-o OUTPUT] [-f] [-s SPEED]
                [-as AVG_SPEED] [-r RTT] [-l LOSS] [-c CONFIG] [-u URL] [-v] [-ns] [--dry_run] [-4] [-6] [-cs CR_SIZE] [-df] [--pure_mode]
                [--version] source [source ...]

ip-check 参数

positional arguments:
  source                测试源文件

optional arguments:
  -h, --help            show this help message and exit
  -w WHITE_LIST [WHITE_LIST ...], --white_list WHITE_LIST [WHITE_LIST ...]
                        偏好ip参数, 格式为: expr1 expr2, 如8 9 会筛选8和9开头的ip
  -b BLOCK_LIST [BLOCK_LIST ...], --block_list BLOCK_LIST [BLOCK_LIST ...]
                        屏蔽ip参数, 格式为: expr1 expr2, 如8 9 会过滤8和9开头的ip
  -pl PREFER_LOCS [PREFER_LOCS ...], --prefer_locs PREFER_LOCS [PREFER_LOCS ...]
                        偏好国家地区选择, 格式为: expr1 expr2, 如hongkong japan 会筛选HongKong 和Japan 地区的ip
  -po PREFER_ORGS [PREFER_ORGS ...], --prefer_orgs PREFER_ORGS [PREFER_ORGS ...]
                        偏好org 选择, 格式为: expr1 expr2, 如org1 org2 会筛选org1, org2 的服务商ip
  -bo BLOCK_ORGS [BLOCK_ORGS ...], --block_orgs BLOCK_ORGS [BLOCK_ORGS ...]
                        屏蔽org 选择, 格式为: expr1 expr2, 如org1 org2 会过滤org1, org2 的服务商ip
  -pp PREFER_PORTS [PREFER_PORTS ...], --prefer_ports PREFER_PORTS [PREFER_PORTS ...]
                        针对ip:port 格式的测试源筛选端口, 格式为: expr1 expr2, 如443 8443 会筛选出443 和8443 端口的ip
  -lv MAX_VT_IP_COUNT, --max_vt_ip_count MAX_VT_IP_COUNT
                        最大用来检测有效(valid) ip数量限制
  -lr MAX_RT_IP_COUNT, --max_rt_ip_count MAX_RT_IP_COUNT
                        最大用来检测rtt ip数量限制
  -ls MAX_ST_IP_COUNT, --max_st_ip_count MAX_ST_IP_COUNT
                        最大用来检测下载(speed) 速度的ip数量限制
  -lb MAX_BT_IP_COUNT, --max_bt_ip_count MAX_BT_IP_COUNT
                        最大better ip的ip数量限制
  -p PORT, --port PORT  用来检测的端口
  -H HOST, --host HOST  可用性域名
  -dr, --disable_rt     是否禁用RTT 测试
  -dv, --disable_vt     是否禁用可用性测试
  -ds, --disable_st     是否禁用速度测试
  -o OUTPUT, --output OUTPUT
                        输出文件
  -f, --fast_check      是否执行快速测试
  -s SPEED, --speed SPEED
                        期望ip的最低网速 (kB/s)
  -as AVG_SPEED, --avg_speed AVG_SPEED
                        期望ip的最低平均网速 (kB/s)
  -r RTT, --rtt RTT     期望的最大rtt (ms)
  -l LOSS, --loss LOSS  期望的最大丢包率
  -c CONFIG, --config CONFIG
                        配置文件
  -u URL, --url URL     测速地址
  -v, --verbose         显示调试信息
  -ns, --no_save        是否忽略保存测速结果文件
  --dry_run             是否跳过所有测试
  -4, --only_v4         仅测试ipv4
  -6, --only_v6         仅测试ipv6
  -cs CR_SIZE, --cr_size CR_SIZE
                        cidr 随机ip 数量限制
  -df, --disable_file_check
                        是否禁用可用性检测文件可用性
  --pure_mode           纯净模式, 不使用geo 数据库进行ip 信息补全, 仅记录ip
  --version             show program's version number and exit
```

## 配置文件

执行`ip-check-cfg` 会生成`config.ini`,  按照备注修改即可。

## 使用示例

```shell
# 文本参数，文本中内容支持ip、ip cidr、支持ipv6、支持ip:port 表达式
ip-check test.txt

# ip 参数，支持ip、ip cidr、支持ipv6、支持ip:port 表达式
ip-check 192.168.1.1/32
ip-check fe80::/ 10
ip-check 1.1.1.1:443

# 禁用可用性测试，某些情况可用性测试失效，可临时禁用。
ip-check test.txt -dv
# 禁用rtt 测试，某些情况rtt 测试失效，可临时禁用。
ip-check test.txt -dr

# ip 偏好，假设你偏好8和9 开头的ip
ip-check test.txt -w "8" "9"
# ip 偏好，假设你喜欢8.222和8.223 开头的ip
ip-check test.txt -w "8.222" "8.223"
# ip 厌恶，假设你不喜欢13和14 开头的ip
ip-check test.txt -b "13" "14"
# ip 厌恶，假设你不喜欢131.13和131.14 开头的ip
ip-check test.txt -b "131.13" "131.14"
# 按地区筛选ip
ip-check test.txt -pl "japan" "hongkong"
# ip:port 格式的测试源只测试端口为8443 的测试源
ip-check 7.8.9.10:443 7.8.9.10:8443 -pp 8443

# 指定测试端口，缺省为443
ip-check test.txt -p 8443

# 指定输出文件，默认为result 与源文件的拼接
ip-check test.txt -o better-ips.txt


# 限制参与可用性测试ip 的数量
ip-check test.txt -lv 100
# 限制参与rtt 测试ip 的数量
ip-check test.txt -lr 100
# 限制参与下载速度测试的ip 的数量
ip-check test.txt -ls 100

# 快速测试， 开启此选项后，当到达测试时长一半下载时间后，最高网速仍未达到期网网速的一半则退出此ip 下载测速
ip-check test.txt -f

# 指定期网网速，单位 kB/s
ip-check test.txt -s 20000

# 指定期望的最大rtt， 单位 ms
ip-check test.txt -r 500
```

以上所有可选选项可联合使用达到最终效果。

## Others

使用geo 信息需要自我下载`GeoLite2-City.mmdb` 和 `GeoLite2-ASN.mmdb`，可通过`igeo-dl` 输入url 下载。
url 可用来源：

https://github.com/P3TERX/GeoLite.mmdb

### igeo-info

查看ip 归属地信息的工具

```shell
igeo-info -h
usage: igeo-info [-h] sources [sources ...]

geo-info 获取ip(s) 的归属地信息

positional arguments:
  sources     待获取归属地信息的ip(s)

optional arguments:
  -h, --help  show this help message and exit
```

### igeo-dl

下载mmdb 数据库的工具

```shell
igeo-dl --help
usage: igeo-dl [-h] [-u URL] [-p PROXY]

igeo-dl 升级/下载geo 数据库

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     geo 数据库下载地址, 要求结尾包含GeoLite2-City.mmdb 或GeoLite2-ASN.mmdb
  -p PROXY, --proxy PROXY
                        下载时使用的代理
```

### igeo-cfg

`igeo-dl` 的配置文件，用于下载mmdb 数据库，建议去github 找寻。

```shell
igeo-cfg -h
usage: igeo-cfg [-h]

igeo-cfg 编辑geo config

optional arguments:
  -h, --help  show this help message and exit
```

### ip-filter

ip 筛选工具

```shell
usage: ip-filter [-h] [-w WHITE_LIST [WHITE_LIST ...]] [-b BLOCK_LIST [BLOCK_LIST ...]] [-pl PREFER_LOCS [PREFER_LOCS ...]]
                 [-po PREFER_ORGS [PREFER_ORGS ...]] [-bo BLOCK_ORGS [BLOCK_ORGS ...]] -o OUTPUT
                 sources [sources ...]

ip-filter: ip 筛选工具

positional arguments:
  sources               待筛选的ip(s)

optional arguments:
  -h, --help            show this help message and exit
  -w WHITE_LIST [WHITE_LIST ...], --white_list WHITE_LIST [WHITE_LIST ...]
                        偏好ip参数, 格式为: expr1 expr2, 如8 9 会筛选8和9开头的ip
  -b BLOCK_LIST [BLOCK_LIST ...], --block_list BLOCK_LIST [BLOCK_LIST ...]
                        屏蔽ip参数, 格式为: expr1 expr2, 如8 9 会过滤8和9开头的ip
  -pl PREFER_LOCS [PREFER_LOCS ...], --prefer_locs PREFER_LOCS [PREFER_LOCS ...]
                        偏好国家地区选择, 格式为: expr1 expr2, 如hongkong japan 会筛选HongKong 和Japan 地区的ip
  -po PREFER_ORGS [PREFER_ORGS ...], --prefer_orgs PREFER_ORGS [PREFER_ORGS ...]
                        偏好org 选择, 格式为: expr1 expr2, 如org1 org2 会筛选org1, org2 的服务商ip
  -bo BLOCK_ORGS [BLOCK_ORGS ...], --block_orgs BLOCK_ORGS [BLOCK_ORGS ...]
                        屏蔽org 选择, 格式为: expr1 expr2, 如org1 org2 会过滤org1, org2 的服务商ip
  -4, --only_v4         仅筛选ipv4
  -6, --only_v6         仅筛选ipv6
  -cs CR_SIZE, --cr_size CR_SIZE
                        cidr 随机抽样ip 数量限制
  -o OUTPUT, --output OUTPUT
                        输出文件
```

## License

[GNU General Public License, version 3](https://www.gnu.org/licenses/gpl-3.0.html)
