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
#
#! /usr/bin/env sh

crudini --set $TEMPEST_CONF network public_router_id $PUBLIC_ROUTER_ID
crudini --set $TEMPEST_CONF network public_network_id $PUBLIC_NETWORK_ID
crudini --set $TEMPEST_CONF identity uri $OS_AUTH_URL
crudini --set $TEMPEST_CONF identity uri_v3 $OS_AUTH_URL_V3
crudini --set $TEMPEST_CONF auth admin_tenant_id $OS_TENANT_ID
crudini --set $TEMPEST_CONF f5_lbaasv2_driver icontrol_hostname $ICONTROL_IPADDR
crudini --set $TEMPEST_CONF f5_lbaasv2_driver icontrol_username admin
crudini --set $TEMPEST_CONF f5_lbaasv2_driver icontrol_password admin
crudini --set $TEMPEST_CONF f5_lbaasv2_driver transport_url rabbit://guest:guest@$CONTROLLER_IPADDR:5672/
