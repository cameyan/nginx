# 启用 Fedora 加固编译：PIE、栈保护、-D_FORTIFY_SOURCE 等安全编译选项
%global  _hardened_build     1
# 定义 nginx 运行用户/组的名称，供 configure 的 --user/--group 及 %%files 权限使用
%global  nginx_user          nginx

# 关闭链接器的严格符号检查：取消定义 _strict_symbol_defs_build 宏
# 参见：https://src.fedoraproject.org/rpms/redhat-rpm-config/c/078af19
%undefine _strict_symbol_defs_build

# 在 Fedora 上，或 EPEL 版本为 8
%if 0%{?fedora} || 0%{?epel} == 8
# 默认构建 GeoIP 模块
%bcond_without geoip
%else
# 默认禁用 GeoIP 模块
%bcond_with geoip
%endif

# RHEL 主版本 >= 8
# 在 RHEL 8 及以上版本应禁用 nginx 的 gperftools 支持。参见：https://bugzilla.redhat.com/show_bug.cgi?id=1931402
%if 0%{?rhel} >= 8
# 禁用 gperftools
%global with_gperftools 0
%else
# 条件：当前架构不是 s390/s390x/ppc64/ppc64le 时成立，gperftools 仅在部分架构上可用
%ifnarch s390 s390x ppc64 ppc64le
# 启用 gperftools
%global with_gperftools 1
%endif
%endif

# 启用异步文件 I/O（--with-file-aio）
%global with_aio 1

# Fedora 版本 > 40，或 RHEL 版本 > 9
%if 0%{?fedora} > 40 || 0%{?rhel} > 9
# 默认禁用 OpenSSL ENGINE
%bcond_with engine
%else
# 默认启用 OpenSSL ENGINE
%bcond_without engine
%endif

# Fedora 版本 > 22
%if 0%{?fedora} > 22
# 启用 mailcap 提供的 mime.types（即使用 nginx-mimetypes 包，不再自带 mime.types）
%global with_mailcap_mimetypes 1
%endif

# kTLS（内核 TLS）需要 OpenSSL 3.0：F36+ 和 EL9+ 默认提供，EPEL8 也可用
%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9 || 0%{?epel} >= 8
# 启用 kTLS
%global with_ktls 1
%endif

# 在 EL8 上针对 OpenSSL 3 构建（EPEL 版本为 8 时）
%if 0%{?epel} == 8
# 指定 OpenSSL 包版本后缀为 3，用于拼接 openssl3-devel / openssl3-libs 等包名
%global openssl_pkgversion 3
%endif

# 定义 nginx ABI 版本，这里直接等于软件版本号，用于 Provides: nginx(abi)
# 参见 nginx 官方关于动态模块打包的说明：https://www.nginx.com/blog/creating-installable-packages-dynamic-modules/
%global nginx_abiversion %{version}

# 动态模块 .so 的安装目录（如 /usr/lib64/nginx/modules）
%global nginx_moduledir %{_libdir}/nginx/modules
# 动态模块的 load_module 配置片段目录（如 /usr/share/nginx/modules）
%global nginx_moduleconfdir %{_datadir}/nginx/modules
# 安装到系统中的 nginx 源码目录，供外部模块编译时使用
%global nginx_srcdir %{_usrsrc}/%{name}-%{version}-%{release}

# 排除该源码目录，避免 RPM 自动扫描其内容产生错误的 Provides
%global __provides_exclude_from ^%{nginx_srcdir}/.*$
# 同样排除该目录，避免产生错误的 Requires
%global __requires_exclude_from ^%{nginx_srcdir}/.*$

# 第三方模块 ngx-fancyindex 的版本号
%global fancy_version 0.6.0

Name:              nginx
Epoch:             2
Version:           1.30.6
# %%{?dist} 会自动追加发行版标识（如 .fc43、.el9），禁用
Release:           1

Summary:           高性能 Web 服务器和反向代理服务器
License:           BSD-2-Clause
URL:               https://nginx.org

Source0:           https://nginx.org/download/nginx-%{version}.tar.gz
# 源码包的 PGP 签名文件，用于校验源码完整性
Source1:           https://nginx.org/download/nginx-%{version}.tar.gz.asc
# 上游开发者 Roman Arutyunyan 的 PGP 公钥，获取地址：https://nginx.org/en/pgp_keys.html
Source3:           https://nginx.org/keys/arut.key
# 上游开发者 Sergey Kandaurov 的 PGP 公钥
Source4:           https://nginx.org/keys/pluknet.key
# 上游开发者 Sergey Belov 的 PGP 公钥
Source5:           https://nginx.org/keys/sb.key
# 上游开发者 Konstantin Pavlov 的 PGP 公钥
Source6:           https://nginx.org/keys/thresh.key
# 默认的 systemd 服务单元文件
Source10:          nginx.service
# logrotate 日志轮转配置
Source11:          nginx.logrotate
# 默认主配置文件
Source12:          nginx.conf
# 零停机升级辅助脚本
Source13:          nginx-upgrade
# RPM 宏模板，安装后供外部 nginx 模块构建使用
Source15:          macros.nginxmods.in
# RPM 依赖生成器属性文件，用于扫描 .so 模块的依赖
Source16:          nginxmods.attr
# 加密私钥口令交互辅助脚本
Source17:          nginx-ssl-pass-dialog
# systemd 模板服务单元，用于启动 nginx 实例（nginx@NAME.service）
Source18:          nginx@.service
# systemd-sysusers 配置，用于创建 nginx 用户/组
Source19:          nginx.sysusers
# systemd-tmpfiles 配置，用于创建 /var 下的运行时目录（bootc 兼容）
Source20:          nginx.tmpfiles
# 第三方模块 ngx-fancyindex 的源码包
Source30:          https://github.com/aperezdc/ngx-fancyindex/releases/download/v%{fancy_version}/ngx-fancyindex-%{fancy_version}.tar.xz
# nginx 默认页使用的 logo 图片
Source102:         nginx-logo.png
# 说明动态模块用法的文档
Source200:         README.dynamic
# nginx 实例模式的配置模板
Source220:         instance.conf

# 移除上游构建脚本中的 -Werror。-Werror 与 -D_FORTIFY_SOURCE=2 冲突，会把警告变成错误导致构建失败
Patch0:            0001-remove-Werror-in-upstream-build-scripts.patch

# 修复 PID 文件竞态条件（见 rhbz#1869026）。该补丁未被上游接受，参见：https://trac.nginx.org/nginx/ticket/1897
Patch1:            0002-fix-PIDFile-handling.patch

# 为带口令的加密私钥增加 ssl_pass_phrase_dialog 辅助脚本支持
Patch2:            0003-Add-SSL-passphrase-dialog.patch

# 在 Fedora41+ 上默认禁用 OpenSSL ENGINE 支持
Patch3:            0004-Disable-ENGINE-support.patch

# 以 -O2 优化级别编译 Perl 模块
Patch4:            0005-Compile-perl-module-with-O2.patch

BuildRequires:     make
BuildRequires:     gcc
# Fedora > 42
%if 0%{?fedora} > 42
# 使用 openpgpverify 工具校验源码签名
BuildRequires:     openpgpverify
%else
# 使用 gnupg2（gpgverify 宏）校验源码签名
BuildRequires:     gnupg2
%endif
# 若启用 gperftools
%if 0%{?with_gperftools}
BuildRequires:     gperftools-devel
%endif
BuildRequires:     libxcrypt-devel
BuildRequires:     openssl%{?openssl_pkgversion}-devel
BuildRequires:     pcre2-devel
BuildRequires:     perl-podlators
# Fedora，或 RHEL>=10，或 EPEL>=9
%if 0%{?fedora} || 0%{?rhel} >= 10 || 0%{?epel} >= 9
BuildRequires:     zlib-ng-devel
%else
BuildRequires:     zlib-devel
%endif

# 运行时依赖
Requires:          nginx-filesystem = %{epoch}:%{version}-%{release}
Requires:          system-logos-httpd

# 提供虚拟能力 webserver，供其他包按能力依赖
Provides:          webserver
# 推荐安装 logrotate（非强制依赖）
Recommends:        logrotate
# 运行时依赖
Requires:          %{name}-core = %{epoch}:%{version}-%{release}

BuildRequires:     systemd
BuildRequires:     systemd-rpm-macros
# 若定义了 systemd_requires 宏则展开，加入相应的脚本依赖
%{?systemd_requires}

%description
Nginx 是一个用于 HTTP、SMTP、POP3 和 IMAP 协议的 Web 服务器和反向代理服务器，
其重点在于高并发、高性能和低内存占用。


%package core
Summary: nginx 最小核心
# 启用了 mailcap 的 mime.types
%if 0%{?with_mailcap_mimetypes}
Requires:          nginx-mimetypes
%endif
Requires:          openssl%{?openssl_pkgversion}-libs
Requires(pre):     nginx-filesystem
# 与 nginx（< 1:1.20.2-4）冲突，避免混装
Conflicts:         nginx < 1:1.20.2-4
# 声明 nginx 的 ABI 版本，供外部 nginx 模块依赖使用
Provides:          nginx(abi) = %{nginx_abiversion}

%description core
nginx 最小核心

%package all-modules
Summary:           一个元包，用于安装所有可用的 Nginx 模块
BuildArch:         noarch

# 启用了 GeoIP
%if %{with geoip}
Requires:          nginx-mod-http-geoip = %{epoch}:%{version}-%{release}
Requires:          nginx-mod-stream-geoip = %{epoch}:%{version}-%{release}
%endif
Requires:          nginx-mod-http-image-filter = %{epoch}:%{version}-%{release}
Requires:          nginx-mod-http-perl = %{epoch}:%{version}-%{release}
Requires:          nginx-mod-http-xslt-filter = %{epoch}:%{version}-%{release}
Requires:          nginx-mod-mail = %{epoch}:%{version}-%{release}
Requires:          nginx-mod-stream = %{epoch}:%{version}-%{release}

%description all-modules
安装所有可用 nginx 模块的元包

%package filesystem
Summary:           Nginx 服务器的基本目录结构布局
BuildArch:         noarch
# 若定义了 sysusers_requires_compat 宏则展开，加入 RHEL9 兼容的 sysusers 依赖
%{?sysusers_requires_compat}

%description filesystem
nginx-filesystem 软件包包含 Nginx 服务器的基本目录结构，包括各目录的正确权限设置

%if %{with geoip}
%package mod-http-geoip
Summary:           Nginx HTTP 地理位置模块(geoip)
BuildRequires:     GeoIP-devel
Requires:          nginx(abi) = %{nginx_abiversion}

%description mod-http-geoip
%{summary}

%package mod-stream-geoip
Summary:           Nginx 流媒体地理 IP 模块
BuildRequires:     GeoIP-devel
Requires:          nginx(abi) = %{nginx_abiversion}
Requires:          nginx-mod-stream = %{epoch}:%{version}-%{release}

%description mod-stream-geoip
%{summary}
%endif

%package mod-http-image-filter
Summary:           Nginx HTTP 图像过滤模块
BuildRequires:     gd-devel
Requires:          nginx(abi) = %{nginx_abiversion}
Requires:          gd

%description mod-http-image-filter
%{summary}

%package mod-http-perl
Summary:           Nginx HTTP Perl 模块
BuildRequires:     perl-devel
BuildRequires:     perl-generators
BuildRequires:     perl(ExtUtils::Embed)
Requires:          nginx(abi) = %{nginx_abiversion}
Requires:          perl(constant)

%description mod-http-perl
%{summary}

%package mod-http-xslt-filter
Summary:           Nginx XSLT 模块
BuildRequires:     libxslt-devel
Requires:          nginx(abi) = %{nginx_abiversion}

%description mod-http-xslt-filter
%{summary}

%package mod-mail
Summary:           Nginx 邮件模块
Requires:          nginx(abi) = %{nginx_abiversion}

%description mod-mail
%{summary}

%package mod-stream
Summary:           Nginx 流模块
Requires:          nginx(abi) = %{nginx_abiversion}

%description mod-stream
%{summary}

%package mod-devel
Summary:           NGinX 模块开发文件
Requires:          nginx = %{epoch}:%{version}-%{release}
Requires:          make
Requires:          gcc
Requires:          gd-devel
%if 0%{?with_gperftools}
Requires:          gperftools-devel
%endif
%if %{with geoip}
Requires:          GeoIP-devel
%endif
Requires:          libxslt-devel
Requires:          openssl%{?openssl_pkgversion}-devel
Requires:          pcre2-devel
Requires:          perl-devel
Requires:          perl(ExtUtils::Embed)
# Fedora，或 RHEL>=10，或 EPEL>=9
%if 0%{?fedora} || 0%{?rhel} >= 10 || 0%{?epel} >= 9
BuildRequires:     zlib-ng-devel
%else
BuildRequires:     zlib-devel
%endif

%description mod-devel
%{summary}


# %%prep 阶段：解压源码、校验签名、应用补丁、准备构建目录。
%prep
# 将上游所有 PGP 公钥（Source3/4/5/6）合并到一个 keyring 文件 nginx.gpg 中
cat %{S:3} %{S:4} %{S:5} %{S:6} > %{_builddir}/%{name}.gpg
# Fedora > 42
%if 0%{?fedora} > 42
# 使用 openpgpverify 校验源码包签名
%{openpgpverify} --keyring='%{_builddir}/%{name}.gpg' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%else
# 使用 gpgverify 校验源码包签名
%{gpgverify} --keyring='%{_builddir}/%{name}.gpg' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%endif
# 自动解压 Source0 并按顺序应用所有补丁
%autosetup -p1
# 把 README.dynamic、service 单元、nginx.conf、实例 service、instance.conf 复制到源码根目录
cp %{SOURCE200} %{SOURCE10} %{SOURCE12} %{SOURCE18} %{SOURCE220} .

# 定义了 openssl_pkgversion（即 EPEL8 使用 OpenSSL 3）
%if 0%{?openssl_pkgversion}
# 修改 nginx 的 OpenSSL 探测配置，把头文件路径和库路径指向 openssl3 的私有目录
sed \
  -e 's|\(ngx_feature_path=\)$|\1%{_includedir}/openssl%{openssl_pkgversion}|' \
  -e 's|\(ngx_feature_libs="\)|\1-L%{_libdir}/openssl%{openssl_pkgversion} |' \
  -i auto/lib/openssl/conf
%endif

# 用 sed 替换 nginx.conf 中 error_log/pid/access_log 的文件名，加入实例名占位符，并追加到 instance.conf
sed -e '/^error_log /s|error\.log|@INSTANCE@_error.log|' \
    -e '/^pid /s|nginx\.pid|nginx-@INSTANCE@.pid|' \
    -e '/^ *access_log/s|access\.log|@INSTANCE@_access.log|' \
    nginx.conf >> instance.conf
# 将 instance.conf 的时间戳对齐到 nginx.conf，避免构建产物时间戳异常
touch -r %{SOURCE12} instance.conf

# 准备要安装到系统中的源码副本（供外部模块编译）：递归复制源码树为带 release 号的目录
cp -a ../%{name}-%{version} ../%{name}-%{version}-%{release}-src
# 将复制后的源码目录移动到当前构建目录
mv ../%{name}-%{version}-%{release}-src .

# =============================================================== #
# 解压 ngx-fancyindex 的 .tar.xz 源码包
tar -xJf %{SOURCE30}
# 定义 fancyindex 模块源码目录路径，供 configure 的 --add-module 使用
%global fancydir %{_builddir}/%{name}-%{version}/ngx-fancyindex-%{fancy_version}
# =============================================================== #

# %%build 阶段：执行 configure 并编译
%build
# nginx 不使用标准 configure 脚本，它有自己的 configure；使用标准 autotools 选项会导致其报错退出
# ---------------------------------------------------------------------------
# 下列 configure 选项逐项说明：
#   --prefix=...                      安装前缀（运行时数据目录 /usr/share/nginx）
#   --sbin-path=...                   nginx 主程序安装路径
#   --modules-path=...                动态模块 .so 安装目录
#   --conf-path=...                   主配置文件路径
#   --error-log-path=...              错误日志默认路径
#   --http-log-path=...               HTTP 访问日志默认路径
#   --http-client-body-temp-path=...  客户端请求体临时文件目录
#   --http-proxy-temp-path=...        反向代理临时文件目录
#   --http-fastcgi-temp-path=...      FastCGI 临时文件目录
#   --http-uwsgi-temp-path=...        uWSGI 临时文件目录
#   --http-scgi-temp-path=...         SCGI 临时文件目录
#   --pid-path=...                    PID 文件路径
#   --lock-path=...                   锁文件路径
#   --user= / --group=                worker 进程运行用户/组
#   --with-compat                     生成与动态模块兼容的二进制（稳定 ABI）
#   --with-debug                      启用调试日志支持
#   --add-module=...                  编译第三方模块（fancyindex 目录美化）
#   --with-file-aio                   启用异步文件 I/O
#   --with-google_perftools_module    启用 gperftools 性能分析模块
#   --with-http_addition_module       响应内容追加/前置模块
#   --with-http_auth_request_module   子请求鉴权模块
#   --with-http_dav_module            WebDAV 模块
#   --with-http_degradation_module    内存不足时降级返回 444 的模块
#   --with-http_flv_module            FLV 伪流媒体模块
#   --with-http_geoip_module=dynamic  HTTP GeoIP 模块（动态编译）
#   --with-stream_geoip_module=dynamic stream 层 GeoIP 模块（动态编译）
#   --with-http_gunzip_module         为不支持 gzip 的客户端解压响应
#   --with-http_gzip_static_module    发送预压缩的 .gz 静态文件
#   --with-http_image_filter_module=dynamic 图片缩放/裁剪模块（动态编译）
#   --with-http_mp4_module            MP4 伪流媒体模块
#   --with-http_perl_module=dynamic   Perl 嵌入模块（动态编译）
#   --with-http_random_index_module   随机选择目录索引文件
#   --with-http_realip_module         从代理头恢复客户端真实 IP
#   --with-http_secure_link_module    安全链接（防盗链/签名 URL）
#   --with-http_slice_module          大文件分片请求模块
#   --with-http_ssl_module            HTTPS/TLS 支持
#   --with-http_stub_status_module    运行状态统计接口
#   --with-http_sub_module            响应内容替换模块
#   --with-http_v2_module             HTTP/2 支持
#   --with-http_v3_module             HTTP/3（QUIC）支持
#   --with-http_xslt_module=dynamic   XSLT 转换模块（动态编译）
#   --with-mail=dynamic               mail 代理模块（动态编译）
#   --with-mail_ssl_module            mail 代理的 SSL 支持
#   --with-openssl-opt=enable-ktls    启用内核 TLS（kTLS）加速
#   --without-engine                  禁用 OpenSSL ENGINE 支持
#   --with-pcre                       使用 PCRE 正则库
#   --with-pcre-jit                   启用 PCRE JIT 编译加速
#   --with-stream=dynamic             TCP/UDP 四层代理模块（动态编译）
#   --with-stream_realip_module       stream 层真实 IP 恢复
#   --with-stream_ssl_module          stream 层 SSL 支持
#   --with-stream_ssl_preread_module  stream 层 SNI 预读（按域名分流）
#   --with-threads                    启用线程池
#   --with-cc-opt=...                 传给编译器的额外参数（RPM 优化标志）
#   --with-ld-opt=...                 传给链接器的额外参数
# 若 configure 失败，则打印 autoconf.err 便于排查并退出。
# ---------------------------------------------------------------------------
if ! ./configure \
    --prefix=%{_datadir}/nginx \
    --sbin-path=%{_sbindir}/nginx \
    --modules-path=%{nginx_moduledir} \
    --conf-path=%{_sysconfdir}/nginx/nginx.conf \
    --error-log-path=%{_localstatedir}/log/nginx/error.log \
    --http-log-path=%{_localstatedir}/log/nginx/access.log \
    --http-client-body-temp-path=%{_localstatedir}/lib/nginx/tmp/client_body \
    --http-proxy-temp-path=%{_localstatedir}/lib/nginx/tmp/proxy \
    --http-fastcgi-temp-path=%{_localstatedir}/lib/nginx/tmp/fastcgi \
    --http-uwsgi-temp-path=%{_localstatedir}/lib/nginx/tmp/uwsgi \
    --http-scgi-temp-path=%{_localstatedir}/lib/nginx/tmp/scgi \
    --pid-path=/run/nginx.pid \
    --lock-path=/run/lock/subsys/nginx \
    --user=%{nginx_user} \
    --group=%{nginx_user} \
    --with-compat \
    --with-debug \
    --add-module=%{fancydir} \
%if 0%{?with_aio}
    --with-file-aio \
%endif
%if 0%{?with_gperftools}
    --with-google_perftools_module \
%endif
    --with-http_addition_module \
    --with-http_auth_request_module \
    --with-http_dav_module \
    --with-http_degradation_module \
    --with-http_flv_module \
%if %{with geoip}
    --with-http_geoip_module=dynamic \
    --with-stream_geoip_module=dynamic \
%endif
    --with-http_gunzip_module \
    --with-http_gzip_static_module \
    --with-http_image_filter_module=dynamic \
    --with-http_mp4_module \
    --with-http_perl_module=dynamic \
    --with-http_random_index_module \
    --with-http_realip_module \
    --with-http_secure_link_module \
    --with-http_slice_module \
    --with-http_ssl_module \
    --with-http_stub_status_module \
    --with-http_sub_module \
    --with-http_v2_module \
    --with-http_v3_module \
    --with-http_xslt_module=dynamic \
    --with-mail=dynamic \
    --with-mail_ssl_module \
%if 0%{?with_ktls}
    --with-openssl-opt=enable-ktls \
%endif
%if %{without engine}
    --without-engine \
%endif
    --with-pcre \
    --with-pcre-jit \
    --with-stream=dynamic \
    --with-stream_realip_module \
    --with-stream_ssl_module \
    --with-stream_ssl_preread_module \
    --with-threads \
    --with-cc-opt="%{optflags}" \
    --with-ld-opt="$RPM_LD_FLAGS"; then
# 空操作占位，表示 configure 失败
  : configure failed
# 输出 configure 生成的错误详情，便于定位
  cat objs/autoconf.err
# 以失败状态退出构建
  exit 1
fi

# 调用 make 进行编译（使用 RPM 并行构建宏）
%make_build


# %%install 阶段：把编译产物安装到 buildroot 虚拟根目录
%install
# 执行 make install；INSTALLDIRS=vendor 指定 Perl 模块安装到发行版目录
%make_install INSTALLDIRS=vendor

# 删除 Perl 的 .packlist 文件（不应打包）
find %{buildroot} -type f -name .packlist -exec rm -f '{}' \;
# 删除 perllocal.pod（Perl 本地安装记录，不应打包）
find %{buildroot} -type f -name perllocal.pod -exec rm -f '{}' \;
# 删除所有空文件
find %{buildroot} -type f -empty -exec rm -f '{}' \;
# 将 .so 动态库权限设为 0755（可执行）
find %{buildroot} -type f -iname '*.so' -exec chmod 0755 '{}' \;

# 安装默认 systemd 服务单元
install -p -D -m 0644 ./nginx.service \
    %{buildroot}%{_unitdir}/nginx.service
# 安装 systemd 模板服务单元（实例模式）
install -p -D -m 0644 ./nginx@.service \
    %{buildroot}%{_unitdir}/nginx@.service
# 安装 logrotate 配置
install -p -D -m 0644 %{SOURCE11} \
    %{buildroot}%{_sysconfdir}/logrotate.d/nginx

# 创建 /etc/systemd/system/nginx.service.d drop-in 目录
install -p -d -m 0755 %{buildroot}%{_sysconfdir}/systemd/system/nginx.service.d
# 创建 /usr/lib/systemd/system/nginx.service.d drop-in 目录
install -p -d -m 0755 %{buildroot}%{_unitdir}/nginx.service.d

# 创建 /etc/nginx/conf.d 目录
install -p -d -m 0755 %{buildroot}%{_sysconfdir}/nginx/conf.d
# 创建 /etc/nginx/default.d 目录
install -p -d -m 0755 %{buildroot}%{_sysconfdir}/nginx/default.d

# 创建 /var/lib/nginx 目录（权限 0700）。
install -p -d -m 0700 %{buildroot}%{_localstatedir}/lib/nginx
# 创建 /var/lib/nginx/tmp 临时目录（权限 0700）。
install -p -d -m 0700 %{buildroot}%{_localstatedir}/lib/nginx/tmp
# 创建 /var/log/nginx 日志目录（权限 0700）。
install -p -d -m 0700 %{buildroot}%{_localstatedir}/log/nginx

# 创建 /usr/share/nginx/html 默认站点目录。
install -p -d -m 0755 %{buildroot}%{_datadir}/nginx/html
# 创建动态模块配置片段目录。
install -p -d -m 0755 %{buildroot}%{nginx_moduleconfdir}
# 创建动态模块 .so 目录。
install -p -d -m 0755 %{buildroot}%{nginx_moduledir}

# 安装默认主配置文件 nginx.conf
install -p -m 0644 ./nginx.conf \
    %{buildroot}%{_sysconfdir}/nginx

# 删除上游自带的 index.html
rm -f %{buildroot}%{_datadir}/nginx/html/index.html
# 删除上游自带的 50x.html 错误页
rm -f %{buildroot}%{_datadir}/nginx/html/50x.html

# 将默认首页软链接到发行版统一的 testpage 页面
ln -s ../../testpage/index.html \
      %{buildroot}%{_datadir}/nginx/html/index.html
# 安装 nginx logo 图片
install -p -m 0644 %{SOURCE102} \
    %{buildroot}%{_datadir}/nginx/html
# 创建 poweredby.png 软链接指向 logo
ln -s nginx-logo.png %{buildroot}%{_datadir}/nginx/html/poweredby.png
# 创建 icons 目录
mkdir -p %{buildroot}%{_datadir}/nginx/html/icons

# 软链接到发行版 pixmaps 中的 poweredby.png，为发行版专属的 powered-by 图片创建软链接
ln -s ../../../pixmaps/poweredby.png \
      %{buildroot}%{_datadir}/nginx/html/icons/poweredby.png

# RHEL >= 9
%if 0%{?rhel} >= 9
# 软链接到发行版的无索引页面 logo
ln -s ../../pixmaps/system-noindex-logo.png \
      %{buildroot}%{_datadir}/nginx/html/system_noindex_logo.png
%endif

# 使用 mailcap 提供的 mime.types
%if 0%{?with_mailcap_mimetypes}
# 删除 nginx 自带的 mime.types（改由 nginx-mimetypes 包提供）
rm -f %{buildroot}%{_sysconfdir}/nginx/mime.types
%endif

# 安装 nginx 主程序 man 手册
install -p -D -m 0644 %{_builddir}/nginx-%{version}/objs/nginx.8 \
    %{buildroot}%{_mandir}/man8/nginx.8

# 安装零停机升级脚本 nginx-upgrade
install -p -D -m 0755 %{SOURCE13} %{buildroot}%{_bindir}/nginx-upgrade
# 用 pod2man 从脚本内嵌 POD 生成 nginx-upgrade 的 man 手册，日期取自脚本中的 "# Last updated:" 行
pod2man --section=8 --name=nginx-upgrade \
    --release="%{version}-%{release}" \
    --center="Nginx Zero-Downtime Upgrade Utility" \
    --date="$(sed -nE 's/# Last updated: (.+)/\1/p' %{SOURCE13})" \
    %{SOURCE13} > %{buildroot}%{_mandir}/man8/nginx-upgrade.8

# 遍历 vim 的四种插件类型
for i in ftdetect ftplugin indent syntax; do
# 安装对应的 vim 语法/缩进等插件文件
    install -p -D -m644 contrib/vim/${i}/nginx.vim \
        %{buildroot}%{_datadir}/vim/vimfiles/${i}/nginx.vim
done

# 启用了 GeoIP
%if %{with geoip}
# 生成 HTTP GeoIP 模块的 load_module 配置片段
echo 'load_module "%{nginx_moduledir}/ngx_http_geoip_module.so";' \
    > %{buildroot}%{nginx_moduleconfdir}/mod-http-geoip.conf
# 生成 stream GeoIP 模块的 load_module 配置片段（zz- 前缀保证加载顺序靠后）
echo 'load_module "%{nginx_moduledir}/ngx_stream_geoip_module.so";' \
    > %{buildroot}%{nginx_moduleconfdir}/zz-mod-stream-geoip.conf
%endif
# 生成图片过滤模块的 load_module 配置片段
echo 'load_module "%{nginx_moduledir}/ngx_http_image_filter_module.so";' \
    > %{buildroot}%{nginx_moduleconfdir}/mod-http-image-filter.conf
# 生成 Perl 模块的 load_module 配置片段
echo 'load_module "%{nginx_moduledir}/ngx_http_perl_module.so";' \
    > %{buildroot}%{nginx_moduleconfdir}/mod-http-perl.conf
# 生成 XSLT 过滤模块的 load_module 配置片段
echo 'load_module "%{nginx_moduledir}/ngx_http_xslt_filter_module.so";' \
    > %{buildroot}%{nginx_moduleconfdir}/mod-http-xslt-filter.conf
# 生成 mail 模块的 load_module 配置片段
echo 'load_module "%{nginx_moduledir}/ngx_mail_module.so";' \
    > %{buildroot}%{nginx_moduleconfdir}/mod-mail.conf
# 生成 stream 模块的 load_module 配置片段
echo 'load_module "%{nginx_moduledir}/ngx_stream_module.so";' \
    > %{buildroot}%{nginx_moduleconfdir}/mod-stream.conf

# 创建 /usr/src 目录
# 安装用于支持外部 nginx 模块构建的文件，安装源码文件
mkdir -p %{buildroot}%{_usrsrc}
# 把源码副本移动到 /usr/src/nginx-<version>-<release>
mv %{name}-%{version}-%{release}-src %{buildroot}%{nginx_srcdir}
# 创建 RPM 宏目录
# 安装 RPM 宏文件
mkdir -p %{buildroot}%{_rpmmacrodir}
# 用实际路径替换宏模板中的占位符，生成 macros.nginxmods
sed -e "s|@@NGINX_ABIVERSION@@|%{nginx_abiversion}|g" \
    -e "s|@@NGINX_MODDIR@@|%{nginx_moduledir}|g" \
    -e "s|@@NGINX_MODCONFDIR@@|%{nginx_moduleconfdir}|g" \
    -e "s|@@NGINX_SRCDIR@@|%{nginx_srcdir}|g" \
    %{SOURCE15} > %{buildroot}%{_rpmmacrodir}/macros.nginxmods
# 安装 nginxmods.attr，供 RPM 扫描模块依赖
# 安装依赖生成器
install -Dpm0644 %{SOURCE16} %{buildroot}%{_fileattrsdir}/nginxmods.attr

# 创建 libexec 目录
# 安装 SSL 口令交互脚本
mkdir -p %{buildroot}%{_libexecdir}
# 安装 nginx-ssl-pass-dialog 脚本
install -m755 %{SOURCE17} \
        %{buildroot}%{_libexecdir}/nginx-ssl-pass-dialog

# 安装 nginx.sysusers 到 sysusers 目录
# 安装 sysusers 配置
install -p -D -m 0644 %{SOURCE19} %{buildroot}%{_sysusersdir}/nginx.conf

# 创建 tmpfiles.d 目录
# 安装 tmpfiles.d 配置
mkdir -p %{buildroot}%{_tmpfilesdir}
# 安装 nginx.tmpfiles 到 tmpfiles.d 目录
install -m 644 -p %{SOURCE20} %{buildroot}%{_tmpfilesdir}/nginx.conf


# nginx-filesystem 子包的 %%pre 脚本（安装前执行）
%pre filesystem
# 使用 sysusers 兼容宏创建 nginx 用户/组（RHEL9 兼容方式）
%sysusers_create_compat %{SOURCE19}

# 主包的 %%post 脚本（安装后执行）
%post
# 执行 systemd 标准的安装后处理（daemon-reload、enable 等）
%systemd_post nginx.service

# 主包的 %%preun 脚本（卸载前执行）
%preun
# 执行 systemd 标准的卸载前处理（stop/disable 等）
%systemd_preun nginx.service

# 主包的 %%postun 脚本（卸载后执行）
%postun
# 执行 systemd 标准的卸载后处理（daemon-reload 等）
%systemd_postun nginx.service

# 文件触发器：当这些路径下的文件被安装/更新时执行下列脚本
# 当新的 nginx 二进制或模块被安装时，请求零停机升级。
# 此处仅 reload 不够，原因见：
# https://blog.nginx.org/blog/nginx-dynamic-modules-how-they-work#upgradeMod
%transfiletriggerin -- %{_sbindir}/nginx %{nginx_moduleconfdir} %{nginx_moduledir}
# 仅在实际安装（非卸载）时执行
if [ $1 -ge 1 ]; then
# 若不存在禁用标记文件，则执行 nginx-upgrade 做零停机升级；失败也不影响事务
    test -f %{_sysconfdir}/nginx/rpm-disable-upgrade || /usr/bin/nginx-upgrade >/dev/null 2>&1 || :
fi

# 打包文件清单
%files
%doc instance.conf
%{_datadir}/nginx/html/*
%{_bindir}/nginx-upgrade
%{_datadir}/vim/vimfiles/ftdetect/nginx.vim
%{_datadir}/vim/vimfiles/ftplugin/nginx.vim
%{_datadir}/vim/vimfiles/syntax/nginx.vim
%{_datadir}/vim/vimfiles/indent/nginx.vim
%{_mandir}/man3/nginx.3pm*
%{_mandir}/man8/nginx.8*
%{_mandir}/man8/nginx-upgrade.8*
%{_unitdir}/nginx.service
%{_unitdir}/nginx@.service
%{_libexecdir}/nginx-ssl-pass-dialog
%config(noreplace) %{_sysconfdir}/logrotate.d/nginx

%files core
%license LICENSE
%doc CHANGES README.md README.dynamic
%{_sbindir}/nginx
%config(noreplace) %{_sysconfdir}/nginx/fastcgi.conf
%config(noreplace) %{_sysconfdir}/nginx/fastcgi.conf.default
%config(noreplace) %{_sysconfdir}/nginx/fastcgi_params
%config(noreplace) %{_sysconfdir}/nginx/fastcgi_params.default
%config(noreplace) %{_sysconfdir}/nginx/koi-utf
%config(noreplace) %{_sysconfdir}/nginx/koi-win
%if ! 0%{?with_mailcap_mimetypes}
%config(noreplace) %{_sysconfdir}/nginx/mime.types
%endif
%config(noreplace) %{_sysconfdir}/nginx/mime.types.default
%config(noreplace) %{_sysconfdir}/nginx/nginx.conf
%config(noreplace) %{_sysconfdir}/nginx/nginx.conf.default
%config(noreplace) %{_sysconfdir}/nginx/scgi_params
%config(noreplace) %{_sysconfdir}/nginx/scgi_params.default
%config(noreplace) %{_sysconfdir}/nginx/uwsgi_params
%config(noreplace) %{_sysconfdir}/nginx/uwsgi_params.default
%config(noreplace) %{_sysconfdir}/nginx/win-utf
%attr(770,%{nginx_user},root) %dir %{_localstatedir}/lib/nginx
%attr(770,%{nginx_user},root) %dir %{_localstatedir}/lib/nginx/tmp
%{_tmpfilesdir}/nginx.conf
%ghost %attr(640,%{nginx_user},root) %{_localstatedir}/log/nginx/access.log
%ghost %attr(640,%{nginx_user},root) %{_localstatedir}/log/nginx/error.log
%dir %{nginx_moduledir}
%dir %{nginx_moduleconfdir}

%files all-modules

%files filesystem
%dir %{_datadir}/nginx
%dir %{_datadir}/nginx/html
%dir %{_sysconfdir}/nginx
%dir %{_sysconfdir}/nginx/conf.d
%dir %{_sysconfdir}/nginx/default.d
%dir %{_sysconfdir}/systemd/system/nginx.service.d
%dir %{_unitdir}/nginx.service.d
%attr(711,root,root) %dir %{_localstatedir}/log/nginx
%{_sysusersdir}/nginx.conf

%if %{with geoip}
%files mod-http-geoip
%{nginx_moduleconfdir}/mod-http-geoip.conf
%{nginx_moduledir}/ngx_http_geoip_module.so

%files mod-stream-geoip
%{nginx_moduleconfdir}/zz-mod-stream-geoip.conf
%{nginx_moduledir}/ngx_stream_geoip_module.so
%endif

%files mod-http-image-filter
%{nginx_moduleconfdir}/mod-http-image-filter.conf
%{nginx_moduledir}/ngx_http_image_filter_module.so

%files mod-http-perl
%{nginx_moduleconfdir}/mod-http-perl.conf
%{nginx_moduledir}/ngx_http_perl_module.so
%dir %{perl_vendorarch}/auto/nginx
%{perl_vendorarch}/nginx.pm
%{perl_vendorarch}/auto/nginx/nginx.so

%files mod-http-xslt-filter
%{nginx_moduleconfdir}/mod-http-xslt-filter.conf
%{nginx_moduledir}/ngx_http_xslt_filter_module.so

%files mod-mail
%{nginx_moduleconfdir}/mod-mail.conf
%{nginx_moduledir}/ngx_mail_module.so

%files mod-stream
%{nginx_moduleconfdir}/mod-stream.conf
%{nginx_moduledir}/ngx_stream_module.so

%files mod-devel
%{_rpmmacrodir}/macros.nginxmods
%{_fileattrsdir}/nginxmods.attr
%{nginx_srcdir}/

%changelog
* Thu Nov 12 2026 wjiang <cameyan@163.com> - 2:1.30.6-1
- 1. 基于 Fedora44 nginx-1.30.6-1 版本初始化 nginx 仓库
  2. 为 spec 全文补充中文注释，便于学习与适配
  3. 移除 rpmautospec 自动机制，改为手工维护 release 与 changelog 信息
  4. 移除原有的 changelog 冗余信息
