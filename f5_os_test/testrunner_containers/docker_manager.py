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
from os.path import join
import subprocess
import time

PDBLD_REGISTRY_PROJNAME = 'docker-registry.pdbld.f5net.com/f5-openstack-test'
def render_dockerfile(**kwargs):
    infname = join(kwargs['test_type'], 'project_docker.tmpl')
    outfname = join(kwargs['test_type'], kwargs['project'], 'Dockerfile')
    open(outfname, 'w').write(
        jinja2.Template(open(infname).read()).render(**kwargs)
    )

def build_container(test_type, project):
    '''Generate an image from the template and specification.'''
    registry_fullname = "{}/{}".format(PDBLD_REGISTRY_PROJNAME, test_type)
    project_dockerfile = join(test_type, project, 'Dockerfile')
    build_string = "docker build -t {} -f {} {}".format(registry_fullname,
                                                        project_dockerfile,
                                                        '.')
    subprocess.check_call(build_string.split())

def main():
    import sys
    render_dockerfile(test_type=sys.argv[1],
                      project=sys.argv[2],
                      branch=sys.argv[3],
                      registry_project_name=PDBLD_REGISTRY_PROJNAME)
    build_container(test_type=sys.argv[1], project=sys.argv[2])

if __name__ == '__main__':
    main()
