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
FROM {{ registry_project_name }}/tempest:latest

RUN mkdir -p /home/buildbot/testrunner/test_results
WORKDIR /home/buildbot/testrunner
# Set openstack setup specific environment variables.
# The implication is that the resulting built container is run-specific!
ARG PUBLIC_ROUTER_ID
ENV PUBLIC_ROUTER_ID=$PUBLIC_ROUTER_ID
ARG PUBLIC_NETWORK_ID
ENV PUBLIC_NETWORK_ID=$PUBLIC_NETWORK_ID
ARG OS_AUTH_URL
ENV OS_AUTH_URL=$OS_AUTH_URL
ARG OS_AUTH_URL_V3
ENV OS_AUTH_URL_V3=$OS_AUTH_URL_V3
ARG OS_TENANT_ID
ENV OS_TENANT_ID=$OS_TENANT_ID
ARG ICONTROL_IPADDR
ENV ICONTROL_IPADDR=$ICONTROL_IPADDR
ARG CONTROLLER_IPADDR
ENV CONTROLLER_IPADDR=$CONTROLLER_IPADDR
ENV TEMPEST_CONFIG_DIR=/etc/tempest/
ENV TEMPEST_CONF=/etc/tempest/tempest.conf

# Install pytest test-runner framework.
RUN pip install --upgrade pip
RUN pip install pytest
COPY ./pytest-autolog ./pytest-autolog
RUN pip install ./pytest-autolog
COPY ./pytest-symbols ./pytest-symbols
RUN pip install ./pytest-symbols
COPY ./pytest-meta ./pytest-meta
RUN pip install ./pytest-meta

# cloning tempest and F5 neutron-lbaas. Sanaz, why do we point at Mitaka?
RUN git clone -b stable/mitaka https://github.com/F5Networks/neutron-lbaas.git 
# Are the following steps necessary Sanaz? Why? Or Why not?
RUN pip install -r neutron-lbaas/requirements.txt
RUN pip install -r neutron-lbaas/test-requirements.txt 

RUN git clone https://github.com/openstack/tempest.git
RUN pip install ./tempest 


# Are the following steps still necessary?
RUN git clone \
https://bldr-git.int.lineratesystems.com/openstack/f5-os-testrunner-configs.git

RUN mkdir -p /etc/tempest
RUN cp -R ./f5-os-testrunner-configs/tempest/lbaasv2/* /etc/tempest/

COPY ./tempest/set_tempest_config.sh \
/home/buildbot/testrunner/set_tempest_config.sh

RUN chmod +x ./set_tempest_config.sh
RUN /home/buildbot/testrunner/set_tempest_config.sh
RUN touch neutron-lbaas/neutron_lbaas/tests/tempest/v2/.pytest.rootdir
CMD ["/usr/local/bin/pytest", "-lv", "--exclude", "incomplete",\
     "no_regression", "--autolog-outputdir", "test_results",\
     "--autolog-session", "neutron-lbaas",\
     "--",\
     "neutron-lbaas/neutron_lbaas/tests/tempest/v2/api/test_health_monitors_non_admin.py::TestHealthMonitors"]
