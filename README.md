# Nginx

---

> [!NOTE]
> 1. 仓库参考 openEuler/nginx master 分支，进行源码版本升级
> 2. nginx.spec 自定义新增构建 fancyindex 模块，用于美化文件索引。自带文件索引功能单一、界面简陋
>    - 模块源码文件: ngx-fancyindex-0.6.0.tar.xz
>    - GitHub 仓库: https://github.com/aperezdc/ngx-fancyindex
>    - 源码下载链接: https://github.com/aperezdc/ngx-fancyindex/releases/download/v0.6.0/ngx-fancyindex-0.6.0.tar.xz
> 3. 含一键构建脚本: auto_build.sh, 创建根证书/服务器证书脚本: auto_create_ca.py

## 源码构建

---

1. 克隆仓库
   ```shell
   git clone https://gitcode.com/fwo/nginx.git
   ```
2. 使用自动构建脚本进行构建(可使用 -h|--help 参数查看帮助)
   ```shell
   bash auto_build.sh -b
   ```
3. 安装生成的 .rpm 包即可

## 证书部署和站点配置

---

### 证书部署

1. 通过脚本 `auto_create_ca.py` 创建根证书，或基于已有根证书创建服务器证书。好处是，系统只需导入根证书，由该根证书签发的子级证书均受信任，详情参考:
   ```shell
   python3 auto_create_ca.py -h
   ```
2. 创建根证书示例(默认值):
   ```shell
   python3 auto_create_ca.py root-ca --path root_ca --key-filename root_ca.key --ca-filename root_ca.pem --algo RSA --key-bits 4096 --ca-bits 512 --ca-days 3650
   
   # 根证书路径: root_ca/root_ca.key  root_ca/root_ca.pem
   ```
3. 基于刚刚创建的根证书为 IP 服务器创建服务器证书，自动会生成 server_I_P.pem/key 格式:
   ```shell
   python3 auto_create_ca.py ca --root-key-path root_ca/root_ca.key --root-ca-path root_ca/root_ca.pem --ips 76.53.189.212 --days 365 --key-algo RSA --key-bits 4096 --ca-algo sha512 --country CN --state ShanXi --locality Xian --org CameyanLab --ou cameyan
   
   # 服务器证书路径: server_76_53_189_212.key server_76_53_189_212.pem
   ```
4. 为默认站点创建私钥和证书目录: `mkdir -p /etc/pki/nginx/private`
5. 将服务器私钥和证书移动到默认站点:
   ```shell
   cp -a -i server_76_53_189_212.key /etc/pki/nginx/private/
   cp -a -i server_76_53_189_212.pem /etc/pki/nginx/
   ```
6. 注意 `nginx.conf` 的证书配置字段 `ssl_certificate|ssl_certificate_key` 值必须和上面放置的服务器证书和私钥位置完全一致:
   ```shell
   # /etc/nginx/nginx.conf
   
   ssl_certificate "/etc/pki/nginx/server_76_53_189_212.pem";
   ssl_certificate_key "/etc/pki/nginx/private/server_76_53_189_212.key";
   ```
7. 将上述创建的根证书 `root_ca/root_ca.pem` 加入系统证书信任库:
   ```shell
   # Linux
   # 1. 将根证书放在指定目录
   cp -a root_ca/root_ca.pem /etc/pki/ca-trust/source/anchors/
   # 2. 更新系统证书
   /usr/bin/update-ca-trust
   
   # Windows
   # 1. 将根证书后缀改为 .crt 格式: root_ca/root_ca.crt
   # 2. Windows 平台双击该证书，将其安装到 `受信任的跟证书颁发机构`
   ```
8. 至此，证书部署完毕

### 站点配置

1. 关闭 Linux 环境的 selinux 严格模式，将 `/etc/selinux/config` 文件内的 `SELINUX` 字段修改为: `SELINUX=permissive`
2. 检测 nginx.conf 配置文件语法是否正确: `nginx -t`
3. 开启相关端口:
   ```shell
   firewall-cmd --zone=public --add-port=443/tcp --permanent
   firewall-cmd --zone=public --add-port=80/tcp --permanent
   firewall-cmd --reload
   ```
4. 启动 nginx 服务，并设置自启动: `systemctl start nginx && systemctl enable nginx`
5. 若浏览器可以成功访问，则说明站点配置成功: `https://IP`

## ngx-fancyindex 模块补充说明

---

### 构建

> [!NOTE]
> - ngx-fancyindex 模块功能必须通过修改 nginx.spec 文件，将其编译进二进制包中，才有此功能
> - 该自定义模块无法通过实时配置去获取其功能
> - 当前 nginx.spec 已集成该模块，直接构建 nginx 软件包即可

ngx-fancyindex 模块构建说明:

1. 修改 `nginx.spec` 文件内的 `%global fancy_version 0.6.0` 模块版本
2. 在 %build 阶段的 `./configure` 内新增构建参数 `--add-module=%{fancydir}`，使其指向解压后的 ngx-fancyindex 目录(当前已自动解压并设置目录)

### 文件索引配置和自定义主题

1. ngx-fancyindex 索引功能通过 nginx 配置文件 `/etc/nginx/nginx.conf` 设置，参考仓库内 `nginx.conf` 文件
2. 站点根目录 `/usr/share/nginx/html/` 创建主题存放目录 `theme`: `mkdir theme && cd theme`
3. 克隆或下载自己二开后的模块主题仓库: `git clone https://gitcode.com/fwo/Nginx-Fancyindex-Theme`
4. 创建文件索引目录: `mkdir download`。因为文件索引目录设置在站点根目录的 `download/` 目录，见 nginx.conf 配置字段 `server/location`
5. 注意 `nginx.conf` 配置文件中的 `fancyindex_header|fancyindex_footer` 字段内容必须和主题目录内的 `header.html|footer.html` 对应，如:
   ```nginx
   # 页面头
   fancyindex_header "/theme/Nginx-Fancyindex-Theme/Nginx-Fancyindex/header.html";
   # 页面尾
   fancyindex_footer "/theme/Nginx-Fancyindex-Theme/Nginx-Fancyindex/footer.html"; 
   ```
6. 主题仓库 `Nginx-Fancyindex-Theme` 也有具体说明，可参考
