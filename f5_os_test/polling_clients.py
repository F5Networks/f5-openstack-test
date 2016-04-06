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
import pytest
import time


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
            if attempts > self.attempts:
                raise MaximumNumberOfAttemptsExceeded
        return current_state


class NeutronClientPollingManager(PollingMixin):
    '''Invokes Neutronclient methods and polls for target expected states.'''
    def __init__(self, neutronclient, **kwargs):
        print("got here in the constructor")
        self.interval = kwargs.pop('interval', .4)
        self.attempts = kwargs.pop('attempts', 12)
        if kwargs:
            raise TypeError("Unexpected **kwargs: %r" % kwargs)
        self.client = neutronclient

    def create_loadbalancer(self, lbconf):
        init_lb = self.client.create_loadbalancer(lbconf)
        lbid = init_lb['loadbalancer']['id']

        def lb_reader(loadbalancer):
            return loadbalancer['loadbalancer']['provisioning_status']
        return self.poll(self.client.show_loadbalancer, lbid, lb_reader)

    def __getattr__(self, name):
        if hasattr(self.client, name):
            return getattr(self.client, name)


@pytest.fixture
def polling_neutronclient():
    '''Invokes Neutronclient methods and polls for target expected states.'''
    return NeutronClientPollingManager
