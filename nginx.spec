%global  _hardened_build     1
%global  nginx_user          nginx

%undefine _strict_symbol_defs_build

%bcond_with geoip

%global with_gperftools 1

%global with_mailcap_mimetypes 0

%global with_aio 1

# ngx-fancyindex 源码版本
# https://github.com/aperezdc/ngx-fancyindex
%global fancy_version 0.6.0

%global __provides_exclude_from ^%{_usrsrc}/%{name}-%{version}-%{release}/.*$
%global __requires_exclude_from ^%{_usrsrc}/%{name}-%{version}-%{release}/.*$

Name:              nginx
Epoch:             1
Version:           1.31.0
Release:           2
Summary:           一个 HTTP 服务器、反向代理和邮件代理服务器
License:           BSD-2-Clause
URL:               http://nginx.org/

Source0:           https://nginx.org/download/nginx-%{version}.tar.gz
Source1:           https://github.com/aperezdc/ngx-fancyindex/releases/download/v0.6.0/ngx-fancyindex-%{fancy_version}.tar.xz
Source10:          nginx.service
Source11:          nginx.logrotate
Source12:          nginx.conf
Source13:          nginx-upgrade
Source14:          macros.nginxmods.in
Source15:          nginxmods.attr
Source100:         index.html
Source102:         nginx-logo.png
Source103:         404.html
Source104:         50x.html
Source200:         README.dynamic
Source210:         UPGRADE-NOTES-1.6-to-1.10

Patch0:            nginx-auto-cc-gcc.patch
Patch1:            nginx-1.12.1-logs-perm.patch
Patch2:            nginx-fix-pidfile.patch

BuildRequires:     gcc openssl-devel pcre2-devel zlib-devel systemd gperftools-devel
Requires:          nginx-filesystem = %{epoch}:%{version}-%{release} openssl
Requires:          nginx-all-modules = %{epoch}:%{version}-%{release}
%if 0%{?with_mailcap_mimetypes}
Requires:          nginx-mimetypes
%endif
Requires(pre):     nginx-filesystem
Requires(post):    systemd
Requires(preun):   systemd
Requires(postun):  systemd
Provides:          webserver
Provides:          nginx(abi) = %{version}
Recommends:        logrotate

%description
NGINX 是一款免费的、开源的、高性能的 HTTP 服务器和反向代理服务器，同时也是 IMAP/POP3 代理服务器。

%package all-modules
Summary:           Nginx 模块
BuildArch:         noarch

%if %{with geoip}
Requires:          nginx-mod-http-geoip = %{epoch}:%{version}-%{release}
%endif
Requires:          nginx-mod-http-image-filter = %{epoch}:%{version}-%{release}
Requires:          nginx-mod-http-perl = %{epoch}:%{version}-%{release}
Requires:          nginx-mod-http-xslt-filter = %{epoch}:%{version}-%{release}
Requires:          nginx-mod-mail = %{epoch}:%{version}-%{release}
Requires:          nginx-mod-stream = %{epoch}:%{version}-%{release}

%description all-modules
NGINX 是一款免费的、开源的、高性能的 HTTP 服务器和反向代理服务器，同时也是一个 IMAP/POP3 代理服务器。
该软件包包含了 Nginx 服务器的基本目录结构。

%package filesystem
Summary:           Nginx 服务器的文件系统
BuildArch:         noarch
Requires(pre):     shadow-utils

%description filesystem
NGINX 是一款免费的、开源的、高性能的 HTTP 服务器和反向代理服务器，同时也是一个 IMAP/POP3 代理服务器。
该软件包包含了 Nginx 服务器的基本目录结构。

%if %{with geoip}
%package mod-http-geoip
Summary:           Nginx 的 HTTP GeoIP 模块
BuildRequires:     GeoIP-devel
Requires:          nginx(abi) = %{version} GeoIP

%description mod-http-geoip
该包是 Nginx HTTP geoip 模块。
%endif

%package mod-http-image-filter
Summary:           Nginx HTTP 图像过滤模块
BuildRequires:     gd-devel
Requires:          nginx(abi) = %{version} gd

%description mod-http-image-filter
Nginx HTTP 图像过滤模块

%package mod-http-perl
Summary:           用于 Nginx 的 HTTP Perl 模块
BuildRequires:     perl-devel perl(ExtUtils::Embed)
Requires:          nginx(abi) = %{version}  perl(constant)
Requires:          perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))

%description mod-http-perl
用于 Nginx 的 HTTP Perl 模块

%package mod-http-xslt-filter
Summary:           Nginx 的 XSLT 模块
BuildRequires:     libxslt-devel
Requires:          nginx(abi) = %{version}

%description mod-http-xslt-filter
Nginx 的 XSLT 模块

%package mod-mail
Summary:           Nginx 的 mail 模块
Requires:          nginx(abi) = %{version}

%description mod-mail
Nginx 的 mail 模块

%package mod-stream
Summary:           Nginx 的 stream 模块
Requires:          nginx(abi) = %{version}

%description mod-stream
Nginx 的 stream 模块

%package mod-devel
Summary:           Nginx 模块开发
Requires:          nginx = %{epoch}:%{version}-%{release}
Requires:          make gcc gd-devel libxslt-devel openssl-devel
Requires:          pcre2-devel perl-devel perl(ExtUtils::Embed) zlib-devel
%if 0%{?with_gperftools}
Requires:          gperftools-devel
%endif
%if %{with geoip}
Requires:          GeoIP-devel
%endif

%description mod-devel
Nginx 模块开发

%package_help

%prep
%autosetup -n %{name}-%{version} -p1
cp %{SOURCE200} %{SOURCE210} %{SOURCE10} %{SOURCE12} .
cp -a ../%{name}-%{version} ../%{name}-%{version}-%{release}-src
mv ../%{name}-%{version}-%{release}-src .

# ===== 规范解压 fancyindex 模块到 BUILD 目录 =====
# 解压到当前目录（即 BUILD/nginx-1.30.0/ 下）
tar -xJf %{SOURCE1}
# 定义宏指向源码树内的模块路径
%global fancydir %{_builddir}/%{name}-%{version}/ngx-fancyindex-%{fancy_version}
# ==============================================

%build
export DESTDIR=%{buildroot}
nginx_ldopts="$RPM_LD_FLAGS -Wl,-E"
if ! ./configure \
    --prefix=%{_datadir}/nginx --sbin-path=%{_sbindir}/nginx --modules-path=%{_libdir}/nginx/modules \
    --conf-path=%{_sysconfdir}/nginx/nginx.conf --error-log-path=%{_localstatedir}/log/nginx/error.log \
    --http-log-path=%{_localstatedir}/log/nginx/access.log \
    --http-client-body-temp-path=%{_localstatedir}/lib/nginx/tmp/client_body \
    --http-fastcgi-temp-path=%{_localstatedir}/lib/nginx/tmp/fastcgi \
    --http-proxy-temp-path=%{_localstatedir}/lib/nginx/tmp/proxy \
    --http-scgi-temp-path=%{_localstatedir}/lib/nginx/tmp/scgi \
    --http-uwsgi-temp-path=%{_localstatedir}/lib/nginx/tmp/uwsgi \
    --pid-path=/run/nginx.pid --lock-path=/run/lock/subsys/nginx \
    --user=%{nginx_user} --group=%{nginx_user} \
    --add-module=%{fancydir} \
%if 0%{?with_aio}
    --with-file-aio \
%endif
    --with-ipv6 --with-http_ssl_module --with-http_v2_module --with-http_realip_module \
    --with-http_addition_module --with-http_xslt_module=dynamic --with-http_image_filter_module=dynamic \
%if %{with geoip}
    --with-http_geoip_module=dynamic \
%endif
    --with-http_sub_module --with-http_dav_module --with-http_flv_module --with-http_mp4_module \
    --with-http_gunzip_module --with-http_gzip_static_module --with-http_random_index_module \
    --with-http_secure_link_module --with-http_degradation_module --with-http_slice_module \
    --with-http_perl_module=dynamic --with-http_auth_request_module \
    --with-mail=dynamic --with-mail_ssl_module --with-openssl-opt=yes --with-pcre --with-pcre-jit --with-stream=dynamic \
    --with-stream_ssl_module --with-google_perftools_module --with-debug \
    --with-cc-opt="%{optflags} $(pcre2-config --cflags)" --with-ld-opt="$nginx_ldopts"; then
  : configure failed
  cat objs/autoconf.err
  exit 1
fi

%make_build

%install
%make_install INSTALLDIRS=vendor

find %{buildroot} -type f -empty -exec rm -f '{}' \;
find %{buildroot} -type f -name .packlist -exec rm -f '{}' \;
find %{buildroot} -type f -name perllocal.pod -exec rm -f '{}' \;
find %{buildroot} -type f -iname '*.so' -exec chmod 0755 '{}' \;

pushd %{buildroot}
install -p -D -m 0644 %{_builddir}/nginx-%{version}/nginx.service .%{_unitdir}/nginx.service
install -p -D -m 0644 %{SOURCE11} .%{_sysconfdir}/logrotate.d/nginx
install -p -d -m 0755 .%{_sysconfdir}/systemd/system/nginx.service.d
install -p -d -m 0755 .%{_unitdir}/nginx.service.d
install -p -d -m 0755 .%{_sysconfdir}/nginx/conf.d
install -p -d -m 0755 .%{_sysconfdir}/nginx/default.d
install -p -d -m 0700 .%{_localstatedir}/lib/nginx
install -p -d -m 0700 .%{_localstatedir}/lib/nginx/tmp
install -p -d -m 0700 .%{_localstatedir}/log/nginx
install -p -d -m 0755 .%{_datadir}/nginx/html
install -p -d -m 0755 .%{_datadir}/nginx/modules
install -p -d -m 0755 .%{_libdir}/nginx/modules
install -p -m 0644 %{_builddir}/nginx-%{version}/nginx.conf .%{_sysconfdir}/nginx
install -p -m 0644 %{SOURCE100} .%{_datadir}/nginx/html
install -p -m 0644 %{SOURCE102} .%{_datadir}/nginx/html
install -p -m 0644 %{SOURCE103} %{SOURCE104} .%{_datadir}/nginx/html

%if 0%{?with_mailcap_mimetypes}
rm -f .%{_sysconfdir}/nginx/mime.types
%endif

install -p -D -m 0644 %{_builddir}/nginx-%{version}/man/nginx.8 .%{_mandir}/man8/nginx.8
install -p -D -m 0755 %{SOURCE13} .%{_bindir}/nginx-upgrade
popd

for i in ftdetect indent syntax; do
    install -p -D -m644 contrib/vim/${i}/nginx.vim %{buildroot}%{_datadir}/vim/vimfiles/${i}/nginx.vim
done

%if %{with geoip}
echo 'load_module "%{_libdir}/nginx/modules/ngx_http_geoip_module.so";' \
    > %{buildroot}%{_datadir}/nginx/modules/mod-http-geoip.conf
%endif

pushd %{buildroot}
echo 'load_module "%{_libdir}/nginx/modules/ngx_http_image_filter_module.so";' \
    > .%{_datadir}/nginx/modules/mod-http-image-filter.conf
echo 'load_module "%{_libdir}/nginx/modules/ngx_http_perl_module.so";' \
    > .%{_datadir}/nginx/modules/mod-http-perl.conf
echo 'load_module "%{_libdir}/nginx/modules/ngx_http_xslt_filter_module.so";' \
    > .%{_datadir}/nginx/modules/mod-http-xslt-filter.conf
echo 'load_module "%{_libdir}/nginx/modules/ngx_mail_module.so";' \
    > .%{_datadir}/nginx/modules/mod-mail.conf
echo 'load_module "%{_libdir}/nginx/modules/ngx_stream_module.so";' \
    > .%{_datadir}/nginx/modules/mod-stream.conf
popd

mkdir -p %{buildroot}%{_usrsrc}
mv %{name}-%{version}-%{release}-src %{buildroot}%{_usrsrc}/%{name}-%{version}-%{release}

mkdir -p %{buildroot}%{_rpmmacrodir}
sed -e "s|@@NGINX_ABIVERSION@@|%{version}|g" \
    -e "s|@@NGINX_MODDIR@@|%{_libdir}\/nginx\/modules|g" \
    -e "s|@@NGINX_MODCONFDIR@@|%{_datadir}\/nginx\/modules|g" \
    -e "s|@@NGINX_SRCDIR@@|%{_usrsrc}\/%{name}-%{version}-%{release}|g" \
    %{SOURCE14} > %{buildroot}%{_rpmmacrodir}/macros.nginxmods
install -Dpm0644 %{SOURCE15} %{buildroot}%{_fileattrsdir}/nginxmods.attr

%pre filesystem
getent group %{nginx_user} > /dev/null || groupadd -r %{nginx_user}
getent passwd %{nginx_user} > /dev/null || useradd -r -d %{_localstatedir}/lib/nginx -g %{nginx_user} \
    -s /sbin/nologin -c "Nginx web server" %{nginx_user}
exit 0

%post
%systemd_post nginx.service

%if %{with geoip}
%post mod-http-geoip
if [ $1 -eq 1 ]; then
    systemctl reload nginx.service >/dev/null 2>&1 || :
fi
%endif

%post mod-http-image-filter
if [ $1 -eq 1 ]; then
    systemctl reload nginx.service >/dev/null 2>&1 || :
fi

%post mod-http-perl
if [ $1 -eq 1 ]; then
    systemctl reload nginx.service >/dev/null 2>&1 || :
fi

%post mod-http-xslt-filter
if [ $1 -eq 1 ]; then
    systemctl reload nginx.service >/dev/null 2>&1 || :
fi

%post mod-mail
if [ $1 -eq 1 ]; then
    systemctl reload nginx.service >/dev/null 2>&1 || :
fi

%post mod-stream
if [ $1 -eq 1 ]; then
    systemctl reload nginx.service >/dev/null 2>&1 || :
fi

%preun
%systemd_preun nginx.service

%postun
%systemd_postun nginx.service
if [ $1 -ge 1 ]; then
    /usr/bin/nginx-upgrade >/dev/null 2>&1 || :
fi

%files
%defattr(-,root,root)
%license LICENSE
%config(noreplace) %{_sysconfdir}/nginx/*
%config(noreplace) %{_sysconfdir}/logrotate.d/nginx
%exclude %{_sysconfdir}/nginx/conf.d
%exclude %{_sysconfdir}/nginx/default.d
%if 0%{?with_mailcap_mimetypes}
%exclude %{_sysconfdir}/nginx/mime.types
%endif
%{_bindir}/nginx-upgrade
%{_sbindir}/nginx
%dir %{_libdir}/nginx/modules
%dir %{_datadir}/nginx/modules
%attr(770,%{nginx_user},root) %dir %{_localstatedir}/lib/nginx
%attr(770,%{nginx_user},root) %dir %{_localstatedir}/lib/nginx/tmp
%{_unitdir}/nginx.service
%{_datadir}/nginx/html/*
%{_datadir}/vim/vimfiles/ftdetect/nginx.vim
%{_datadir}/vim/vimfiles/syntax/nginx.vim
%{_datadir}/vim/vimfiles/indent/nginx.vim
%attr(770,%{nginx_user},root) %dir %{_localstatedir}/log/nginx

%files all-modules

%files filesystem
%dir %{_sysconfdir}/nginx
%dir %{_sysconfdir}/nginx/{conf.d,default.d}
%dir %{_sysconfdir}/systemd/system/nginx.service.d
%dir %{_unitdir}/nginx.service.d
%dir %{_datadir}/nginx
%dir %{_datadir}/nginx/html

%if %{with geoip}
%files mod-http-geoip
%{_libdir}/nginx/modules/ngx_http_geoip_module.so
%{_datadir}/nginx/modules/mod-http-geoip.conf
%endif

%files mod-http-image-filter
%{_libdir}/nginx/modules/ngx_http_image_filter_module.so
%{_datadir}/nginx/modules/mod-http-image-filter.conf

%files mod-http-perl
%{_libdir}/nginx/modules/ngx_http_perl_module.so
%{_datadir}/nginx/modules/mod-http-perl.conf
%dir %{perl_vendorarch}/auto/nginx
%{perl_vendorarch}/nginx.pm
%{perl_vendorarch}/auto/nginx/nginx.so

%files mod-http-xslt-filter
%{_libdir}/nginx/modules/ngx_http_xslt_filter_module.so
%{_datadir}/nginx/modules/mod-http-xslt-filter.conf

%files mod-mail
%{_libdir}/nginx/modules/ngx_mail_module.so
%{_datadir}/nginx/modules/mod-mail.conf

%files mod-stream
%{_libdir}/nginx/modules/ngx_stream_module.so
%{_datadir}/nginx/modules/mod-stream.conf

%files mod-devel
%{_rpmmacrodir}/macros.nginxmods
%{_fileattrsdir}/nginxmods.attr
%{_usrsrc}/%{name}-%{version}-%{release}

%files help
%defattr(-,root,root)
%doc CHANGES README.md README.dynamic
%{_mandir}/man3/nginx.3pm*
%{_mandir}/man8/nginx.8*

%changelog
* Mon May 25 2026 wjiang <cameyan@163.com> - 1:1.31.0-2
- 1. upgrade fancyindex module to 0.6.0
  2. update nginx.conf

* Fri May 22 2026 wjiang <cameyan@163.com> - 1:1.31.0-1
- upgrade to 1.31.0 and lfs ngx-fancyindex

* Thu Apr 30 2026 wjiang <cameyan@163.com> - 1:1.30.0-1
- 初始化 Nginx 1.30.0
