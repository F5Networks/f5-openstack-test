#! /usr/bin/env python
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

'''library to create and use containers an environment with a local registry
and a container orchestration environment'''

import jinja2
import logging
import os
from os.path import join
import subprocess
import sys
import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

CTXT = os.path.abspath(os.curdir)
REG_ID = 'docker-registry.pdbld.f5net.com/f5-openstack-test'
TIMESTAMP = time.time()
def render_dockerfile(**kwargs):
    infname = join(kwargs['test_type'], 'project_docker.tmpl')
    outdir = join(kwargs['test_type'], kwargs['project'])
    outfname = join(outdir, 'Dockerfile')
    logging.debug('outfname: {}'.format(outfname))
    open(outfname, 'w').write(
        jinja2.Template(open(infname).read()).render(**kwargs)
    )

def _publish_testrunner_container(registry_fullname):
    pubstring = "docker push {}".format(registry_fullname)
    logger.debug(pubstring)
    subprocess.check_call(pubstring.split())

def _build_testrunner_container(project_dockerfile):
    '''Generate an image from the template and specification.'''
    local_tag = "{:.0f}_testrunner".format(TIMESTAMP)
    build_string = ("docker build "
                    "--build-arg PUBLIC_ROUTER_ID={PUBLIC_ROUTER_ID} "
                    "--build-arg PUBLIC_NETWORK_ID={PUBLIC_NETWORK_ID} "
                    "--build-arg OS_AUTH_URL={OS_AUTH_URL} "
                    "--build-arg OS_AUTH_URL_V3={OS_AUTH_URL_V3} "
                    "--build-arg OS_TENANT_ID={OS_TENANT_ID} "
                    "--build-arg ICONTROL_IPADDR={ICONTROL_IPADDR} "
                    "--build-arg CONTROLLER_IPADDR={CONTROLLER_IPADDR} "
                    "-t {LOCALTAG} "
                    "-f {project_dockerfile} "
                    ".".format(LOCALTAG=local_tag,
                               project_dockerfile=project_dockerfile,
                               **os.environ)
                   )
    logger.debug(build_string)
    subprocess.check_call(build_string.split())
    image_query = "docker images -q {}".format(local_tag)
    return subprocess.check_output(image_query.split()), local_tag

def build_and_publish(test_type, project, branch, subjectcode_id):
    project_dockerfile = join(CTXT, test_type, project, 'Dockerfile')
    logger.debug(project_dockerfile)
    image_id, local_tag = _build_testrunner_container(project_dockerfile)
    user = subprocess.check_output('whoami'.split()).strip()
    registry_fullname = "{reg}/{ttype}/{proj}/{brnch}/{githsh}/{user}/{image}"\
        .format(reg=REG_ID,
                ttype=test_type,
                proj=project,
                brnch=branch,
                githsh=subjectcode_id,
                user=user,
                image=image_id)
    logger.debug('registry_fullname: {}'.format(registry_fullname))
    tag_command = "docker tag {LOCAL} {FULL}".format(LOCAL=local_tag,
                                                     FULL=registry_fullname)
    subprocess.check_call(tag_command.split())
    _publish_testrunner_container(registry_fullname)


def main():
    render_dockerfile(test_type=sys.argv[1],
                      project=sys.argv[2],
                      branch=sys.argv[3],
                      registry_project_name=REG_ID,
                      timestamp=TIMESTAMP)
    build_and_publish(test_type=sys.argv[1],
                      project=sys.argv[2],
                      branch=sys.argv[3],
                      subjectcode_id=sys.argv[4])

if __name__ == '__main__':
    main()
