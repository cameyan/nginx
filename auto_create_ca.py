#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileName  : auto_create_ca.py
Desc      : nginx 仓库自动创建自签名根证书(用于配置网站证书)
Author    : wjiang <cameyan@163.com>
CreateDate: 2026-05-22 10:28:25
UUID      : 6BB4BF18-8ED9-4371-B1B1-C6492BC7EF3D
Changelog :
    - 2026-05-22: ...

版权 (C) 2026 wjiang <cameyan@163.com>
保留所有商业权利。本版权声明及下述许可条款 **仅适用于本文件**，
不自动延伸至包含本文件的项目中的其他文件或组件。

许可条款（“署名‑非商业‑相同方式共享 1.0”文件级公共许可，简称 NC‑SA‑1.0）

1. 许可授予
   版权持有人特此允许任何个人或非商业实体，为个人学习、研究、娱乐等
   非商业目的，使用、复制、修改和分发本文件，无需书面申请，也无需支付费用。

2. 署名与修改声明（必须遵守）
   a) 任何分发（无论原始或修改版）必须完整保留本版权声明及许可条款。
   b) 若您对本文件做了任何修改，必须在修改后的文件醒目位置以清晰字样标明：
      “本文件由 [原文件名称] 修改而来”，并注明修改日期和修改者信息。
   c) 不得以任何方式移除或隐藏原始作者的署名、版权声明或许可条款。

3. 开源与相同方式共享（Copyleft）
   a) 任何分发修改版的行为，必须同时以相同的许可条款（NC‑SA‑1.0）
      免费公开其完整的修改后文件内容（包括所有修改）。
   b) 修改后的文件必须以可获取的形式提供（例如公开代码仓库、随分发一同
      提供），不得设置访问密码、付费墙或其他技术限制。
   c) **禁止将修改后的文件转变为专有产品，不得以自己的名义主张原始
      版权或限制后续使用。**

4. 非商业使用限制
   a) 您不得将本文件（或其修改版）用于任何商业目的或获利活动，
      包括但不限于：销售、出租、嵌入商业产品、商业 SaaS 服务、
      商业培训材料、商业咨询工具，或由商业实体雇员在执行职责时使用。
   b) 任何直接或间接产生收入、经济补偿、商业竞争优势的行为，
      均视为商业目的。

5. 商业授权（必须书面）
   如果您希望将本文件或其衍生品用于商业目的，无论是否盈利，
   **必须事先获得版权持有人的明确书面授权**。
   版权持有人保留独立决定是否授予商业许可的权利，
   并可要求另行签署商业许可协议并支付相关费用。
   商业授权申请请联系：wjiang <cameyan@163.com>

6. 免责声明
   本文件“按原样”提供，不包含任何明示或暗示的担保。在任何情况下，
   版权持有人不对因使用本文件而产生的任何直接或间接损害承担责任。

本文件的许可条款以本文件头所载内容为准；项目其他文件（如有）可能适用不同许可，
请参阅各文件自身的声明或项目根目录的 LICENSE 文件。
"""


import argparse
import subprocess
from pathlib import Path


def create_root_ca(
        ip: str,
        domain: str,
        key_filename: str,
        pem_filename: str,
        day: int = 365) -> None:
    """
    创建自签名根证书

    Args:
        ip: IPv4 地址
        domain: 域名(二者选其一)
        key_filename: 生成的私钥文件名
        pem_filename: 生成的公钥文件名(证书)
        day: 证书有效期

    Returns:
        创建的自签名证书 *.key  *.pem

    """
    print(ip, domain, day, key_filename, pem_filename)

    # 创建证书配置文件
    san_filename = "san.cnf"

    # ip 和 domain 必选且互斥，为None的字段则注释
    ip_01, ip_02 = (f"# CN = {ip}", f"# IP.1 = {ip}") if ip is None else (f"CN = {ip}", f"IP.1 = {ip}")
    domain_01, domain_02 = (f"# CN = {domain}", f"# DNS.1 = {domain}") if domain is None else (f"CN = {domain}", f"DNS.1 = {domain}")

    # 创建自签名证书的配置文件
    san_context = f"""# {san_filename}

[req]
# 算法长度
default_bits = 4096
# 是否交互式
prompt = no
# 算法位数
default_md = sha256
# 版本 v3
x509_extensions = v3_req
distinguished_name = dn

[dn]
C = CN
ST = shanxi
L = xian
O = company
OU = dept
# 此处为特定 IP 签发
{ip_01}
# 为域名签发
{domain_01}

[v3_req]
subjectAltName = @alt_names

[alt_names]
# 如果是为特定 IP 签发
{ip_02}
# 如果是为域名签发
{domain_02}
"""
    with open(san_filename, "w", encoding='utf-8') as fw:
        fw.write(san_context)
    
    # 调用 openssl 命令创建证书
    command = f"openssl req -new -x509 -nodes -days {day} -keyout {key_filename} -out {pem_filename} -config {san_filename}"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # 判断命令执行结果
    if result.returncode == 0:
        print(f"创建成功: 公钥: {pem_filename} | 私钥: {key_filename}")
    else:
        print(f"创建失败, 请检查...")
        subprocess.run(['rm', '-f', key_filename, pem_filename])
    
    subprocess.run(['rm', '-f', san_filename])


def main():
    parser = argparse.ArgumentParser(
        description="创建 Nginx 自签名证书"
    )

    parser.add_argument('--day', type=int, metavar='day', default=365, help='证书有效期(默认: 365天)')

    # 互斥参数
    parser_mutex_group = parser.add_mutually_exclusive_group(required=True)
    parser_mutex_group.add_argument('--ip', metavar='<ipv4>', type=str, help='IPv4 地址*')
    parser_mutex_group.add_argument('--domain', metavar='<domain>', type=str, help='域名*')

    parser.add_argument('--key', type=str, metavar='<key filename>', default='server.key', help='私钥文件名(默认: server.key)')
    parser.add_argument('--pem', type=str, metavar='<pem filename>', default='server.pem', help='公钥文件名(默认: server.pem)')


    args = parser.parse_args()

    if args:
        create_root_ca(
            ip=args.ip,
            domain=args.domain,
            key_filename=args.key,
            pem_filename=args.pem,
            day=args.day)


if __name__ == '__main__':
    main()

