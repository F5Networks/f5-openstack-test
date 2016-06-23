# Copyright 2015-2016 F5 Networks Inc.
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

from f5.bigip import ManagementRoot
from pprint import pprint as pp
import pytest


@pytest.fixture
def bigip(symbols, scope="module"):
    '''bigip fixture'''
    return ManagementRoot(
        symbols.bigip_ip, symbols.bigip_username, symbols.bigip_password
    )


@pytest.fixture
def nclientmanager(symbols, polling_neutronclient):
    nclient_config = {
        'username':    symbols.tenant_username,
        'password':    symbols.tenant_password,
        'tenant_name': symbols.tenant_name,
        'auth_url':    symbols.auth_url}

    pnc = polling_neutronclient(**nclient_config)
    return pnc


@pytest.fixture
def setup_with_nclientmanager(request, nclientmanager):
    def finalize():
        pp('Entered setup/finalize.')
        nclientmanager.delete_all_lbaas_healthmonitors()
        nclientmanager.delete_all_lbaas_pools()
        nclientmanager.delete_all_listeners()
        nclientmanager.delete_all_loadbalancers()

    finalize()
    request.addfinalizer(finalize)
    return nclientmanager


@pytest.fixture
def setup_with_loadbalancer(setup_with_nclientmanager):
    nclientmanager = setup_with_nclientmanager
    subnets = nclientmanager.list_subnets()['subnets']
    for sn in subnets:
        if 'client-v4' in sn['name']:
            lbconf = {'vip_subnet_id': sn['id'],
                      'tenant_id':     sn['tenant_id'],
                      'name':          'testlb_01'}
    activelb =\
        nclientmanager.create_loadbalancer({'loadbalancer': lbconf})
    return nclientmanager, activelb


@pytest.fixture
def setup_with_listener(setup_with_loadbalancer):
    nclientmanager, activelb = setup_with_loadbalancer
    listener_config =\
        {'listener': {'name': 'test_listener',
                      'loadbalancer_id': activelb['loadbalancer']['id'],
                      'protocol': 'HTTP',
                      'protocol_port': 80}}
    listener = nclientmanager.create_listener(listener_config)
    return nclientmanager, listener


@pytest.fixture
def setup_with_pool(setup_with_listener):
    nclientmanager, activelistener = setup_with_listener
    pool_config = {'pool': {
                   'name': 'test_pool_anur23rgg',
                   'lb_algorithm': 'ROUND_ROBIN',
                   'listener_id': activelistener['listener']['id'],
                   'protocol': 'HTTP'}}
    pool = nclientmanager.create_lbaas_pool(pool_config)
    return nclientmanager, pool


@pytest.fixture
def setup_with_pool_member(setup_with_pool):
    nclientmanager, activepool = setup_with_pool
    pool_id = activepool['pool']['id']
    for sn in nclientmanager.list_subnets()['subnets']:
        if 'server-v4' in sn['name']:
            address = sn['allocation_pools'][0]['start']
            subnet_id = sn['id']
            break

    member_config = {'member': {
                     'subnet_id': subnet_id,
                     'address': address,
                     'protocol_port': 80}}
    member = nclientmanager.create_lbaas_member(pool_id, member_config)
    return nclientmanager, activepool, member


@pytest.fixture
def setup_with_healthmonitor(setup_with_pool_member):
    nclientmanager, activepool, activemember = setup_with_pool_member
    monitor_config = {'healthmonitor': {
                      'delay': 3,
                      'pool_id': activepool['pool']['id'],
                      'type': 'HTTP',
                      'timeout': 13,
                      'max_retries': 7}}
    healthmonitor = nclientmanager.create_lbaas_healthmonitor(monitor_config)
    return nclientmanager, healthmonitor, activepool, activemember


@pytest.fixture
def get_auth_token(keystoneclientmanager):
    token_id = keystoneclientmanager.auth_ref['token']['id']
    return token_id


@pytest.fixture
def heatclientmanager(heatclient_pollster, get_auth_token, symbols):
    '''Heat client manager fixture.'''
    config_dict = {
        'endpoint': symbols.heatclient_url,
        'token':    get_auth_token
    }
    return heatclient_pollster(**config_dict)


@pytest.fixture
def keystoneclientmanager(symbols, keystoneclient_pollster):
    '''Keystone client manager fixture.'''
    config_dict = {
        'auth_url':    symbols.auth_url,
        'tenant_name': symbols.os_tenant_name,
        'username':    symbols.os_username,
        'password':    symbols.os_password
    }
    return keystoneclient_pollster(**config_dict)


@pytest.fixture
def glanceclientmanager(glanceclient_pollster, get_auth_token, symbols):
    '''Glance client manager fixture.'''
    config_dict = {
        'endpoint': symbols.glanceclient_url,
        'token':    get_auth_token
    }
    return glanceclient_pollster(**config_dict)
