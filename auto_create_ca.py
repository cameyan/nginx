#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileName  : 036_根证书_服务器证书创建.py
Desc      : 创建自签名根证书，并基于此签发服务器证书(子级证书)
            1. 创建根私钥
            2. 通过根私钥创建 自签名根证书(公钥)
            3. 通过根证书创建 服务器私钥+服务器证书(公钥)
Author    : wjiang <cameyan@163.com>
CreateDate: 2026-05-26 16:23:20
UUID      : CB498D18-50FA-4572-A3B2-81048480339E
Changelog :
    - 2026-05-27: 完成根证书、服务器证书创建脚本

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
import shutil
import sys
import subprocess
import tempfile
import os
import re

from typing import List, Optional, Any
from pathlib import Path

import colorama
from colorama import Fore, Back, Style


def safe_str(s: str) -> str:
    """
    清理域名/IP字符串，使其更安全（如用作文件名）。
    1. 删除指定字符
    2. 替换指定字符为 '_'
    3. 将连续重复的任意字符压缩为一个

    Args:
        s: 待清理的字符串

    Returns:

    """
    # 删除字符
    # delete_chars = "* \t\\@#$%^&()[]{}"
    delete_chars = "* "
    # 替换字符
    replace_map = {'.': '_', ':': '_', '\\': '/'}
    # 合并
    trans_table = str.maketrans(
        {c: None for c in delete_chars} | {k: v for k, v in replace_map.items()}
    )
    # 清理+替换
    cleaned = s.translate(trans_table)

    # 压缩连续相同的字符（例如 __ 变成 _）
    return re.sub(r'(.)\1+', r'\1', cleaned)


def p_out(msg: Any, color=Fore.WHITE, style=Style.NORMAL, is_print: bool = True):
    """

    Args:
        msg:
        color:
        style:
        is_print:

    Returns:

    """
    formattr = f"{style}{color}{msg}{Style.RESET_ALL}"
    if is_print:
        print(formattr)
    else:
        return formattr


def create_root_ca(root_path: str,
                   root_key: str,
                   root_ca: str,
                   algo: str,
                   key_bits: int,
                   ca_bits: int,
                   ca_validity: int):
    """
    创建根私钥+根证书

    Args:
        root_path: 保存根证书和私钥的目录(默认: root_ca)
        root_key: 根私钥文件名
        root_ca: 根证书文件名
        algo: 根私钥加密算法(RSA | ED25519)
        key_bits: 私钥加密算法位数:
                    - RSA: 2048(默认), 3072, 4096
                    - ED25519: 无
        ca_bits: 证书哈希算法，若私钥加密算法为 RSA，则必须指定。若为 ED25519 则会被忽略。只需指定 位数
                   - RSA: -sha[256(默认), 384, 512]
                   - ED25519: 已内建哈希算法，自动忽略
        ca_validity: 根证书有效期(天)

    Returns:
        1. root_ca 目录已存在根公私钥，直接退出
        2. root_ca 目录不存在根公私钥，创建

    """
    # 检查根公私钥是否存在
    if Path(f"{root_path}/{root_key}").is_file() and Path(f"{root_path}/{root_ca}").is_file():
        print(f">>> {B}指定路径已存在: ")
        print(f"    {B}  - {G}根私钥: {C}{root_path}/{root_key}")
        print(f"    {B}  - {G}根证书: {C}{root_path}/{root_ca}")
        print(f">>> {Y}请确认以上根私钥根证书有效，并使用 ca 子命令签发证书~")

        sys.exit()

    else:
        print(f">>> {Y}目录 {B}{root_path}/{Y} 不存在或缺失根私钥和根证书。你可以:")
        print(f"    {B}  - {G}键入 {R}yes{G} 并回车，以同意创建新的根私钥和根证书")
        print(f"    {B}  - {G}键入其它并回车，表示不同意新建。你可将自己的根私钥和根证书放置在 {B}{root_path}/{G} 并重新运行命令")

        is_next = input(f">>> {Y}请确认(yes): {X}")

        if is_next == 'yes':
            # 确认新建根私钥和根证书

            # 1. 先删除原根目录
            shutil.rmtree(Path(root_path), ignore_errors=True)

            # 2. 创建
            os.mkdir(Path(root_path))

            # 3. 创建根私钥
            print(f">>> {C}正在创建根私钥...")

            cmd_01 = ["openssl", "genpkey", "-algorithm", algo, "-outform", "PEM", "-out", f"{root_path}/{root_key}", "-quiet"]
            # 若加密算法为 RSA，为其追加配置位数
            if algo == "RSA":
                cmd_01.extend(["-pkeyopt", f"rsa_keygen_bits:{key_bits}"])

            result_01 = subprocess.run(cmd_01)
            if result_01.returncode != 0:
                print(f"\n>>> {R}错误: 根私钥创建失败。正在退出...")
                sys.exit(-1)

            # 4. 创建自签名根证书
            print(f">>> {C}正在生成自签名根证书...")
            cmd_02 = ["openssl", "req", "-x509", "-new", "-nodes",
                      "-key", f"{root_path}/{root_key}", f"-sha{ca_bits}",
                      "-days", str(ca_validity), "-out", f"{root_path}/{root_ca}",
                      "-subj", "/C=CN/ST=ShanXi/L=Xian/O=CameyanLab/OU=cameyan/CN=CameyanLab Internal Root CA"]
            result_02 = subprocess.run(cmd_02)
            if result_02.returncode != 0:
                print(f">>> {R}错误，根证书创建失败。正在退出...")
                sys.exit(-1)

            print(f"")
            print(f">>> {C}恭喜，根私钥和根证书创建成功: ")
            print(f"    {C}  - {G}根私钥: {B}{root_path}/{root_key}")
            print(f"    {C}  - {G}根证书: {B}{root_path}/{root_ca}")
            print(f"")
            print(f">>> {Y}注意: ")
            print(f"    {W}  - 1. {R}请务必保存好根私钥 {root_path}/{root_key}")
            print(f"    {W}  - 2. {B}将根证书导入系统，由其签发的子级证书都将被信任")


        else:
            print(f"\n>>> {Y}操作已中止~")
            sys.exit(-2)


def sign_server_cert(
    root_key_path: str,
    root_ca_path: str,
    domains: Optional[List[str]],
    ips: Optional[List[str]],
    days: int,
    server_key_out: str,
    server_ca_out: str,
    key_algo: str,
    key_bits: int,
    hash_algo: str,
    country: str,
    state: str,
    locality: str,
    org: str,
    ou: str,
    cn: Optional[str]
) -> None:
    """
    通过 根私钥+根证书 签发 服务器私钥+服务器证书

    Args:
        root_key_path: 用于签发证书的根私钥路径(默认: root_ca/root_ca.key)
        root_ca_path: 用于签发证书的根证书路径(默认: root_ca/root_ca.pem)
        domains: 待签发证书的域名，可关联多个
        ips: 待签发证书的IP，可关联多个
        days: 证书有效期(默认: 365天)
        server_key_out: 服务器私钥输出名(默认: server_域名/IP.key)
        server_ca_out: 服务器证书输出名(默认: server_域名/IP.pem)
        key_algo: 服务器私钥算法(RSA - 默认 | ED25519)
        key_bits: 服务器私钥算法位数(仅对私钥RSA算法生效，2048 | 3072 | 4096 - 默认)
        hash_algo: 服务器证书Hash算法(仅对私钥RSA算法生效，-[sha256 | sha384 | sha512 - 默认])
        country: 服务器证书国家(C)
        state: 服务器证书省份(ST)
        locality: 服务器证书城市(L)
        org: 服务器证书组织(O)
        ou: 服务器证书部门(OU)
        cn: 服务器CN通用名(CN)

    Returns:
        服务器私钥、服务器证书
    """
    # 首先判断根私钥或证书是否存在和格式是否正确
    file_key = subprocess.run(["file", root_key_path], capture_output=True).stdout.decode("utf-8")
    file_ca = subprocess.run(["file", root_ca_path], capture_output=True).stdout.decode("utf-8")
    if not all([Path(root_key_path).is_file(), Path(root_ca_path).is_file(), "OpenSSH private key" in file_key, "PEM certificate" in file_ca]):
        print(f">>> {R}错误: 路径 {root_key_path}, {root_ca_path} 缺失根私钥和根证书或对应文件格式错误，正在退出...")
        sys.exit()

    # IP 或 域名必须有1个
    if not domains and not ips:
        print(f">>> {R}错误: 请至少提供一个域名或 IP")
        sys.exit(-1)
    # 取 域名或IP 列表第一个作为 通用名(CN)
    if cn is None:
        cn = (domains[0] if domains else ips[0])

    # 若未指定 服务器私钥 输出路径
    if not server_key_out:
        # 优先使用域名
        if domains:
            server_key_out = safe_str(f"server_{domains[0]}") + ".key"
        # 其次使用 IP
        elif ips:
            server_key_out = safe_str(f"server_{ips[0]}") + ".key"

    # 若未指定 服务器证书 输出路径
    if not server_ca_out:
        # 优先使用域名
        if domains:
            server_ca_out = safe_str(f"server_{domains[0]}") + ".pem"
        # 其次使用 IP
        elif ips:
            server_ca_out = safe_str(f"server_{ips[0]}") + ".pem"

    # 若服务器私钥+证书输出路径含 /，则包含目录，先创建它
    if '/' in server_key_out:
        subprocess.run(["mkdir", "-p"] + [server_key_out.rsplit('/', 1)[0]])
    if '/' in server_ca_out:
        subprocess.run(["mkdir", "-p"] + [server_ca_out.rsplit('/', 1)[0]])

    print(f">>> {B}前置条件检查成功，您的签发信息如下:")
    print(f"    {W}  - {G}根私钥: {C}{root_key_path}")
    print(f"    {W}  - {G}根证书: {C}{root_ca_path}")
    print(f"")
    print(f"    {W}  - {G}服务器私钥: {C}{server_key_out}")
    print(f"    {W}  - {G}服务器证书: {C}{server_ca_out}")
    print(f"    {W}  - {G}绑定域名  : {C}{domains}")
    print(f"    {W}  - {G}绑定IP    : {C}{ips}")
    print(f"    {W}  - {G}有效期    : {C}{days} 天")
    print(f"    {W}  - {G}证书主题  : {C}C = {country}, ST = {state}, L = {locality}, O = {org}, OU = {ou}, CN = {cn}")
    print(f"")
    print(f">>> {B}正在为您签发服务器私钥...")

    # ---- 1. 生成服务器私钥 ----
    key_cmd = ["openssl", "genpkey", "-algorithm", key_algo.upper(), "-out", server_key_out]
    if key_algo.upper() == "RSA":
        key_cmd += ["-pkeyopt", f"rsa_keygen_bits:{key_bits}"]
    subprocess.run(key_cmd, check=True, capture_output=True, text=True)

    print(f">>> {B}正在构建 SAN 配置...")

    # ---- 2. 构建 CSR 配置（只含 SAN） ----
    alt_lines = []
    for i, d in enumerate(domains or [], 1):
        alt_lines.append(f"DNS.{i} = {d}")
    for i, ip in enumerate(ips or [], 1):
        alt_lines.append(f"IP.{i} = {ip}")

    csr_config = f"""
[ req ]
default_bits       = 2048
prompt             = no
distinguished_name = dn
req_extensions     = req_ext

[ dn ]
C  = {country}
ST = {state}
L  = {locality}
O  = {org}
OU = {ou}
CN = {cn}

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
{chr(10).join(alt_lines)}
"""

    print(f">>> {B}正在添加扩展信息...")

    # ---- 3. 构建证书签发专用配置（添加必要扩展） ----
    sign_config = f"""
[ v3_server ]
basicConstraints       = critical, CA:FALSE
keyUsage               = critical, digitalSignature, keyEncipherment
extendedKeyUsage       = serverAuth
subjectAltName         = @alt_names

[ alt_names ]
{chr(10).join(alt_lines)}
"""

    print(f">>> {B}正在写入临时配置文件...")

    # 写入两个临时文件
    csr_fd, csr_path = tempfile.mkstemp(suffix=".csr")
    os.close(csr_fd)

    cfg_csr_fd, cfg_csr_path = tempfile.mkstemp(suffix=".cnf")
    with os.fdopen(cfg_csr_fd, 'w') as f:
        f.write(csr_config)

    cfg_sign_fd, cfg_sign_path = tempfile.mkstemp(suffix=".cnf")
    with os.fdopen(cfg_sign_fd, 'w') as f:
        f.write(sign_config)

    print(f">>> {B}正在生成 CSR 签名请求...")

    try:
        # ---- 4. 生成 CSR ----
        csr_cmd = [
            "openssl", "req", "-new",
            "-key", server_key_out,
            "-out", csr_path,
            "-config", cfg_csr_path
        ]
        subprocess.run(csr_cmd, check=True, capture_output=True, text=True)

        print(f">>> {B}正在使用根证书和CSR签发服务器证书...")

        # ---- 5. 用根证书签发 ----
        sign_cmd = [
            "openssl", "x509", "-req",
            "-in", csr_path,
            "-CA", root_ca_path,
            "-CAkey", root_key_path,
            "-CAcreateserial",
            "-out", server_ca_out,
            "-days", str(days),
            f"-{hash_algo}",
            "-extfile", cfg_sign_path,
            "-extensions", "v3_server"
        ]
        subprocess.run(sign_cmd, check=True, capture_output=True, text=True)

    except subprocess.CalledProcessError as e:
        # 打印 OpenSSL 错误以便排查
        print(f"\n{R}错误: OpenSSL 命令失败：{' '.join(e.cmd)}")
        print(f"{Y}{e.stderr}")
        raise

    finally:
        print(f">>> {B}证书申请成功，正在清理临时文件...")
        # 清理临时文件
        for f in [csr_path, cfg_csr_path, cfg_sign_path]:
            if os.path.exists(f):
                os.unlink(f)

    print(f"")
    print(f"{G}恭喜，您为 {domains}| {ips} 签发的证书创建成功~")
    print(f"")
    print(f"{B}证书部署指南 >>>")
    print(f"{G}  - 为默认站点创建私钥和证书目录:")
    print(f"{C}    mkdir -p /etc/pki/nginx/private")
    print(f"{G}  - 将服务器私钥和证书移动到默认站点:")
    print(f"{C}    cp -a -i {server_key_out} /etc/pki/nginx/private/")
    print(f"{C}    cp -a -i {server_ca_out} /etc/pki/nginx/")


def main():
    """
    命令行解析

    Returns:

    """
    parser = argparse.ArgumentParser(description="创建根私钥、根证书，签发服务器证书工具")

    # 创建子命令解析器
    subparsers = parser.add_subparsers(
        title="可用命令",
        dest="cmd"
    )

    # root-ca 子命令
    root_ca_parser = subparsers.add_parser('root-ca', help='创建根私钥和根证书')
    root_ca_parser.add_argument('--path', metavar='[path]', type=str, default='root_ca', help='存放根私钥根证书路径(默认: root_ca)')
    root_ca_parser.add_argument('--key-filename', metavar='[filename]', type=str, default='root_ca.key', help='根私钥文件名(默认: root_ca.key)')
    root_ca_parser.add_argument('--ca-filename', metavar='[filename]', type=str, default='root_ca.pem', help='根证书文件名(默认: root_ca.pem)')
    root_ca_parser.add_argument('--algo', metavar='[RSA|ED25519]', type=str, default='RSA', choices=['RSA', 'ED25519'], help='根私钥加密算法(默认: RSA)')
    root_ca_parser.add_argument('--key-bits', metavar='[2048|3072|4096]', type=int, choices=[2048, 3072, 4096], default=4096, help='根私钥加密算法位数(仅对RSA算法生效，默认: 4096)')
    root_ca_parser.add_argument('--ca-bits', metavar='[256|384|512]', type=int, choices=[256, 384, 512], default=512, help='根证书哈希算法(仅对RSA算法生效，默认: 512)')
    root_ca_parser.add_argument('--ca-days', metavar='[days]', type=int, default=3650, help='根证书有效期(默认: 3650天)')

    # ca 子命令
    ca_parser = subparsers.add_parser('ca', help='通过根证书签发服务器证书(公钥+私钥)')
    ca_parser.add_argument('--root-key-path', metavar='', type=str, default='root_ca/root_ca.key', help='根私钥路径(默认: root_ca/root_ca.key)')
    ca_parser.add_argument('--root-ca-path', metavar='', type=str, default='root_ca/root_ca.pem', help='根证书路径(默认: root_ca/root_ca.pem)')
    ca_parser.add_argument('--domains', nargs='*', help='待签发证书域名列表')
    ca_parser.add_argument('--ips', nargs='*', help='待签发证书IPv4地址列表')
    ca_parser.add_argument('--days', type=int, default=365, help='证书有效期(默认: 365天)')
    ca_parser.add_argument('--key-out', type=str, metavar='[key filename]', help='服务器私钥输出文件名(默认: server_domain-IP.key)')
    ca_parser.add_argument('--ca-out', type=str, metavar='[ca filename]', help='服务器证书输出文件名(默认: server_domain-IP.pem)')
    ca_parser.add_argument('--key-algo', type=str, default='RSA', choices=['RSA', 'ED25519'], help='服务器私钥算法(默认: RSA)')
    ca_parser.add_argument('--key-bits', type=int, default=4096, choices=[2048, 3072, 4096], help='服务器私钥算法位数(仅对RSA算法生效，默认: 4096')
    ca_parser.add_argument('--ca-algo', type=str, default='sha512', choices=['sha256', 'sha384', 'sha512'], help='服务器证书Hash算法，默认: sha512')
    ca_parser.add_argument('--country', type=str, default='CN', help='国家(C - CN)')
    ca_parser.add_argument('--state', type=str, default='ShanXi', help='省份(ST - ShanXi)')
    ca_parser.add_argument('--locality', type=str, default='Xian', help='城市(L - Xian)')
    ca_parser.add_argument('--org', type=str, default='CameyanLab', help='组织(O - CameyanLab)')
    ca_parser.add_argument('--ou', type=str, default='cameyan', help='部门(OU - cameyan)')
    ca_parser.add_argument('--cn', type=str, help='通用名称(CN，一般无需指定，自动使用域名或IP作为CN)')


    # 解析参数
    args = parser.parse_args()
    print(args)

    if args.cmd == 'root-ca':
        create_root_ca(root_path=args.path,
                       root_key=args.key_filename,
                       root_ca=args.ca_filename,
                       algo=args.algo,
                       key_bits=args.key_bits,
                       ca_bits=args.ca_bits,
                       ca_validity=args.ca_days)
    elif args.cmd == 'ca':
        sign_server_cert(root_key_path=args.root_key_path,
                         root_ca_path=args.root_ca_path,
                         domains=args.domains,
                         ips=args.ips,
                         days=args.days,
                         server_key_out=args.key_out,
                         server_ca_out=args.ca_out,
                         key_algo=args.key_algo,
                         key_bits=args.key_bits,
                         hash_algo=args.ca_algo,
                         country=args.country,
                         state=args.state,
                         locality=args.locality,
                         org=args.org,
                         ou=args.ou,
                         cn=args.cn)
    else:
        parser.print_help()


if __name__ == '__main__':
    # 初始化
    colorama.init(autoreset=True)
    # 为颜色定义别名
    R, G, Y, B, C, W, H, X = Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.CYAN, Fore.WHITE, Fore.BLACK, Style.RESET_ALL

    main()
