# Nginx

> [!NOTE]
> 1. 仓库参考 openEuler/nginx master 分支，进行源码版本升级
> 2. nginx.spec 自定义新增构建 fancyindex 模块，用于美化文件索引。自带文件索引功能单一、界面简陋
>    - 模块源码文件: ngx-fancyindex-0.6.0.tar.xz
>    - GitHub 仓库: https://github.com/aperezdc/ngx-fancyindex
>    - 源码下载链接: https://github.com/aperezdc/ngx-fancyindex/releases/download/v0.6.0/ngx-fancyindex-0.6.0.tar.xz
> 3. 含一键构建脚本: auto_build.sh, 创建根证书/服务器证书脚本: auto_create_ca.py

## 源码构建

```shell
# 1. 
```