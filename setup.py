#!/usr/bin/env python

# Copyright 2014 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import f5_os_test

from setuptools import setup


setup(
    name='f5-openstack-test',
    description='F5 Networks common testing packages for OpenStack',
    license='Apache License, Version 2.0',
    version=f5_os_test.__version__,
    author='F5 Networks',
    author_email='f5_common_python@f5.com',
    url='https://github.com/F5Networks/f5-openstack-test',
    keywords=['F5', 'openstack', 'test'],
    install_requires=['requests >= 2.9.1',
                      'pytest >= 2.9.1',
                      'pytest-cov >= 2.2.1',
                      'mock >= 1.3.0'],
    packages=['f5_os_test'],
    entry_points={
        'pytest11': ['poll_fix = f5_os_test.polling_clients',
                     'infra_fix = f5_os_test.infrastructure']
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
    ]
)
