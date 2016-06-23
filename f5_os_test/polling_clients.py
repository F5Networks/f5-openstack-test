# Copyright 2016 F5 Networks Inc.
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
'''This module contains a set of OS Client-specific Polling Managers.

   These managers are intended to map 1-1 to OS clients, and provide event
drive polling monitors for their methods.  Because clients and their methods
are idiosyncratic in OS there's little scope for a generalized (cross-client)
manager, and I'm cautious about excessively abstract method polling, e.g.
making each manager simply implement a decorator for all methods.

IF a client has methods that provide a uniform means of observing state changes
then we could probably effectively used such a decorator, but I'm not yet
familiar enough with OS to make that leap.
'''
from f5.bigip import BigIP
from glanceclient.v2.client import Client as GlanceClient
from heatclient.exc import HTTPNotFound
from heatclient.v1.client import Client as HeatClient
from keystoneclient.v2_0.client import Client as KeystoneClient
from neutronclient.common.exceptions import NotFound
from neutronclient.common.exceptions import StateInvalidClient
from neutronclient.v2_0.client import Client as NeutronClient
from pprint import pprint as pp
import pytest
import time


# flake8 hack
pp(BigIP)


class MaximumNumberOfAttemptsExceeded(Exception):
    pass


class PollingMixin(object):
    '''Use this mixin to poll for resource entering 'target' from other.'''
    def poll(self, observer, resource_id,
             status_reader, target_status='ACTIVE'):
        current_state = observer(resource_id)
        current_status = status_reader(current_state)
        attempts = 0
        while current_status != target_status:
            time.sleep(self.interval)
            current_state = observer(resource_id)
            current_status = status_reader(current_state)
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return current_state


class ClientManagerMixin(PollingMixin):
    '''Base class for polling manager common functionality.'''
    pass


class NeutronClientPollingManager(NeutronClient, ClientManagerMixin):
    '''Invokes Neutronclient methods and polls for target expected states.'''
    def __init__(self, **kwargs):
        pp("got here in the constructor")
        self.interval = kwargs.pop('interval', .4)
        self.max_attempts = kwargs.pop('max_attempts', 12)
        super(NeutronClientPollingManager, self).__init__(**kwargs)

    def _poll_call_with_exceptions(self, exceptional, call, *args, **kwargs):
        attempts = 0
        while attempts <= self.max_attempts:
            try:
                retval = call(*args)
            except exceptional:
                time.sleep(self.interval)
                attempts = attempts + 1
                if attempts > self.max_attempts:
                    raise MaximumNumberOfAttemptsExceeded
                continue
            break
        return retval

    # begin loadbalancer section
    def create_loadbalancer(self, lbconf):
        init_lb = super(NeutronClientPollingManager, self)\
            .create_loadbalancer(lbconf)
        lbid = init_lb['loadbalancer']['id']

        def lb_reader(loadbalancer):
            return loadbalancer['loadbalancer']['provisioning_status']
        return self.poll(super(NeutronClientPollingManager, self)
                         .show_loadbalancer, lbid, lb_reader)

    def _lb_delete_helper(self, lbid):
        try:
            super(NeutronClientPollingManager, self)\
                .delete_loadbalancer(lbid)
        except NotFound:
            return True
        return False

    def update_loadbalancer(self, lbid, lbconf):
        updated = self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self).update_loadbalancer,
            lbid, lbconf)
        return updated

    def delete_loadbalancer(self, lbid):
        attempts = 0
        while not self._lb_delete_helper(lbid):
            time.sleep(self.interval)
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return True

    def delete_all_loadbalancers(self):
        for lb in super(NeutronClientPollingManager, self)\
                .list_loadbalancers()['loadbalancers']:
            self.delete_loadbalancer(lb['id'])

    # begin listener section
    def create_listener(self, listener_conf):
        init_listener = self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self).create_listener,
            listener_conf)
        # The dict returned by show listener doesn't have a status.
        lids = [l['id'] for l in super(NeutronClientPollingManager, self)
                .list_listeners()['listeners']]
        attempts = 0
        while init_listener['listener']['id'] not in lids:
            time.sleep(self.interval)
            lids = [l['id'] for l in super(NeutronClientPollingManager, self)
                    .list_listeners()['listeners']]
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return init_listener

    def update_listener(self, listener_id, listener_conf):
        updated = self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self).update_listener,
            listener_id, listener_conf)
        return updated

    def delete_listener(self, listener_id):
        self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self).delete_listener,
            listener_id)
        lids = [l['id'] for l in super(NeutronClientPollingManager, self)
                .list_listeners()['listeners']]
        attempts = 0
        while listener_id in lids:
            time.sleep(self.interval)
            lids = [l['id'] for l in super(NeutronClientPollingManager, self)
                    .list_listeners()['listeners']]
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return True

    def delete_all_listeners(self):
        for listener in super(NeutronClientPollingManager, self)\
                .list_listeners()['listeners']:
            pp(listener['id'])
            self.delete_listener(listener['id'])

    # Begin lbaas pool section
    def create_lbaas_pool(self, pool_config):
        pool = self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self).create_lbaas_pool,
            pool_config)
        attempts = 0
        pool_id = pool['pool']['id']
        while pool_id not in\
                [p['id'] for p in super(NeutronClientPollingManager, self)
                    .list_lbaas_pools()['pools']]:
            time.sleep(self.interval)
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return pool

    def update_lbaas_pool(self, lbaas_pool_id, lbaas_pool_conf):
        updated = self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self).update_lbaas_pool,
            lbaas_pool_id, lbaas_pool_conf)
        return updated

    def delete_lbaas_pool(self, pool_id):
        self.delete_all_lbaas_pool_members(pool_id)
        self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self).delete_lbaas_pool,
            pool_id)
        attempts = 0
        while pool_id in\
                [p['id'] for p in super(NeutronClientPollingManager, self)
                    .list_lbaas_pools()['pools']]:
            time.sleep(self.interval)
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return True

    def delete_all_lbaas_pools(self):
        for pool in super(NeutronClientPollingManager, self)\
                .list_lbaas_pools()['pools']:
            try:
                self.delete_lbaas_pool(pool['id'])
            except NotFound:
                continue
        attempts = 0
        while super(NeutronClientPollingManager, self)\
                .list_lbaas_pools()['pools']:
            time.sleep(self.interval)
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return True

    # Begin member section
    def create_lbaas_member(self, pool_id, member_config):
        member = self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self).create_lbaas_member,
            pool_id, member_config)
        attempts = 0
        member_id = member['member']['id']
        while member_id not in [
                m['id'] for m in
                super(NeutronClientPollingManager, self)
                .list_lbaas_members(pool_id)['members']
                ]:
            time.sleep(self.interval)
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return member

    def update_lbaas_member(self, member_id, pool_id, member_conf):
        updated = self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self).update_lbaas_member,
            member_id, pool_id, member_conf)
        return updated

    def delete_lbaas_member(self, member_id, pool_id):
        self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self).delete_lbaas_member,
            member_id, pool_id)
        attempts = 0
        while member_id in [
                m['id'] for m in
                super(NeutronClientPollingManager, self)
                .list_lbaas_members(pool_id)['members']
                ]:
            time.sleep(self.interval)
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return True

    def delete_all_lbaas_pool_members(self, pool_id):
        for member in super(NeutronClientPollingManager, self)\
                .list_lbaas_members(pool_id)['members']:
            try:
                self.delete_lbaas_member(member['id'], pool_id)
            except NotFound:
                continue
        return True

    # Begin healthmonitor section
    def create_lbaas_healthmonitor(self, monitor_config):
        healthmonitor = self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self)
            .create_lbaas_healthmonitor,
            monitor_config)
        healthmonitor_id = healthmonitor['healthmonitor']['id']
        attempts = 0
        while healthmonitor_id not in [
                hm['id'] for hm in
                super(NeutronClientPollingManager, self)
                .list_lbaas_healthmonitors()['healthmonitors']
                ]:
            time.sleep(self.interval)
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return healthmonitor

    def update_lbaas_healthmonitor(self,
                                   lbaas_healthmonitor_id,
                                   lbaas_healthmonitor_conf):
        updated = self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self)
            .update_lbaas_healthmonitor,
            lbaas_healthmonitor_id, lbaas_healthmonitor_conf)
        return updated

    def delete_lbaas_healthmonitor(self, healthmonitor_id):
        self._poll_call_with_exceptions(
            StateInvalidClient,
            super(NeutronClientPollingManager, self)
            .delete_lbaas_healthmonitor,
            healthmonitor_id)
        attempts = 0
        while healthmonitor_id in [
                hm['id'] for hm in
                super(NeutronClientPollingManager, self)
                .list_lbaas_healthmonitors()['healthmonitors']
                ]:
            time.sleep(self.interval)
            attempts = attempts + 1
            if attempts > self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded
        return True

    def delete_all_lbaas_healthmonitors(self):
        for healthmonitor in\
                super(NeutronClientPollingManager, self)\
                .list_lbaas_healthmonitors()['healthmonitors']:
            try:
                self.delete_lbaas_healthmonitor(healthmonitor['id'])
            except NotFound:
                continue
        return True


class HeatClientPollingManager(HeatClient, ClientManagerMixin):
    '''Utilizes heat client to create/delete heat stacks.'''

    default_stack_config = {
        'files': {},
        'disable_rollback': True,
        'environment': {},
        'tags': None,
        'environment_files': None
    }

    def __init__(self, **kwargs):
        self.interval = kwargs.pop('interval', 10)
        self.max_attempts = kwargs.pop('max_attempts', 100)

        super(HeatClientPollingManager, self).__init__(**kwargs)

    def stack_status(self, stack):
        return stack.stack_status

    def create_stack(self, configuration, target_status='CREATE_COMPLETE'):
        configuration.update(self.default_stack_config)
        stack = self.stacks.create(**configuration)
        return self.poll(
            self.stacks.get,
            stack['stack']['id'],
            self.stack_status,
            target_status=target_status
        )

    def delete_stack(self, stack_id):
        self.stacks.delete(stack_id)
        try:
            self.poll(
                self.stacks.get,
                stack_id,
                self.stack_status,
                target_status='DELETE_COMPLETE'
            )
        except HTTPNotFound:
            raise
        except MaximumNumberOfAttemptsExceeded:
            raise


class KeystoneClientPollingManager(KeystoneClient, ClientManagerMixin):
    '''Manager for keystone client polling.'''

    def __init__(self, **kwargs):
        self.interval = kwargs.pop('interval', 2)
        self.max_attempts = kwargs.pop('max_attempts', 20)

        super(KeystoneClientPollingManager, self).__init__(**kwargs)


class GlanceClientPollingManager(GlanceClient, ClientManagerMixin):
    def __init__(self, **kwargs):
        self.interval = kwargs.pop('interval', 2)
        self.max_attempts = kwargs.pop('max_attempts', 20)

        super(GlanceClientPollingManager, self).__init__(**kwargs)


@pytest.fixture
def polling_neutronclient():
    '''Invokes Neutronclient methods and polls for target expected states.'''
    return NeutronClientPollingManager


@pytest.fixture
def heatclient_pollster():
    '''Access to HeatClient polling for create/delete/modify of heat stack.'''
    return HeatClientPollingManager


@pytest.fixture
def keystoneclient_pollster():
    '''Access to KeystoneClient pollster.'''
    return KeystoneClientPollingManager


@pytest.fixture
def glanceclient_pollster():
    '''Access to GlanceClient pollster for managing images.'''
    return GlanceClientPollingManager
