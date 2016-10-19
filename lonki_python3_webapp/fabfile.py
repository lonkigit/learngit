#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'lonki'

'''
Deployment toolkit.
'''

import os,re
from datetime import datetime

# 导入Fabric API:
from fabric.api import *

# 服务器登录用户名:
env.user = 'root'
# sudo用户为root:
env.sudo_user = 'root'
# 服务器地址，可以有多个，依次部署:
env.hosts = ['23.106.138.243:26765']
env.hosts

# 服务器MySQL用户名和口令:
db_user = 'root'
db_password = 'zhujie8721*'

_TAR_FILE = 'dist-lonki.tar.gz'
_REMOTE_TMP_TAR = '/tmp/%s' % _TAR_FILE
_REMOTE_BASE_DIR = '/srv/lonki'

def build():
    includes = ['static', 'templates', 'map', 'favicon.ico', '*.py']
    excludes = ['test', '.*', '*.pyc', '*.pyo']
    local('rm -f dist/%s' % _TAR_FILE)
    with lcd(os.path.join(os.path.abspath('.'), 'www')):
        cmd = ['tar', '--dereference', '-czvf', '../dist/%s' % _TAR_FILE]
        cmd.extend(['--exclude=\'%s\'' % ex for ex in excludes])
        cmd.extend(includes)
        local(' '.join(cmd))

def deploy():
    newdir = 'www-%s' % datetime.now().strftime('%y-%m-%d_%H.%M.%S')
    # 删除已有的tar文件:
    run('rm -f %s' %_REMOTE_TMP_TAR)
    # 上传新的tar文件:
    put('dist/%s' %_TAR_FILE,_REMOTE_TMP_TAR)
    # 创建新目录:
    with cd(_REMOTE_BASE_DIR):
        sudo('mkdir %s' %newdir)
    # 解压到新目录:
    with cd('%s/%s' % (_REMOTE_BASE_DIR,newdir)):
        sudo('tar -xzvf %s' % _REMOTE_TMP_TAR)

    # 重置软链接:
    with cd(_REMOTE_BASE_DIR):
        sudo('rm -f www')
        sudo('ln -s %s www' % newdir)
        sudo('chown root:root www')
        sudo('chown -R root:root %s' % newdir)

    # 重启Python服务和nginx服务器:
    with settings(warn_only=True):
        sudo('supervisorctl stop lonki')
        sudo('supervisorctl start lonki')
        sudo('/etc/init.d/nginx reload')

