#!/usr/bin/env python
# Copyright (c) 2015 Scality
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import distutils.spawn
import setuptools
import subprocess


def get_version():
    def has_git():
        return distutils.spawn.find_executable('git') is not None

    def is_git_clone():
        cmd = ['git', 'rev-parse', '--show-toplevel']

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return proc.wait() == 0

    if hasattr(subprocess, 'check_output'):
        check_output = subprocess.check_output
    else:
        def check_output(*args, **kwargs):
            proc = subprocess.Popen(stdout=subprocess.PIPE, *args, **kwargs)
            output, _ = proc.communicate()
            rc = proc.poll()
            if rc != 0:
                raise subprocess.CalledProcessError(
                    rc, kwargs.get('args', args[0]), output=output)
            return output

    def get_git_version():
        prefix = 'scality-sproxyd-client-'
        cmd = ['git', 'describe', '--tags', '--dirty', '--always',
               '--match', '%s*' % prefix]

        result = check_output(cmd).strip()
        assert result.startswith(prefix)

        return result[len(prefix):]

    if has_git() and is_git_clone():
        return get_git_version()
    else:
        return '999'


setuptools.setup(
    name='scality-glance-store',
    version='0.0.0',
    description='Scality Ring backend for OpenStack Glance',
    url='http://www.scality.com/',
    author='Scality Openstack Engineering Team',
    author_email='openstack-eng@scality.com',
    license='Apache License (2.0)',
    packages=['scality_glance_store'],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7'],
    install_requires=['glance_store>=0.1.10', 'oslo.config>=1.2.0',
                      'oslo.utils>=1.0.0', 'scality-sproxyd-client'],
    entry_points={
        'glance_store.drivers': [
            'scality=scality_glance_store.store:Store',
            'glance.store.scality.Store=scality_glance_store.store:Store'
        ],
    },
)
