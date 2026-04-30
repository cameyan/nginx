#########################################################
# 1. 签发 自签名根证书 的脚本
# 2. 键入待部署环境的 IPv4 地址: ipv4
# 3. 若待部署环境有域名，则取消注释并使用: domain
#########################################################

# 为 IPv4 / 域名 签发
ipv4="1.1.1.1"
domain="www.example.com"

# 创建证书配置文件
san_filename="san.cnf"

# 生成的公钥、私钥文件
key_filename="server.key"
pem_filename="server.pem"

# 证书有效期
ca_validity="365"

san_context="# ${san_filename}

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
CN = ${ipv4}
# 为域名签发
# CN = ${domain}

[v3_req]
subjectAltName = @alt_names

[alt_names]
# 如果是为特定 IP 签发
IP.1 = ${ipv4}
# 如果是为域名签发
# DNS.1 = ${domain}
"

echo "${san_context}" > "${san_filename}"

echo "正在创建自签名证书..."

if openssl req -new -x509 -nodes -days "${ca_validity}" -keyout "${key_filename}" -out "${pem_filename}" -config "${san_filename}"
then
    echo "创建成功: 公钥: ${pem_filename} | 私钥: ${key_filename}"
else
    echo "创建失败, 请检查..."
    rm -f "${pem_filename}" "${key_filename}"
fi

rm -f "${san_filename}"
