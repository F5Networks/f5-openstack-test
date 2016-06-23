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

import pytest


def get_file_contents(file_path):
    file = open(file_path)
    file_contents = file.read()
    file.close()
    return file_contents


def cleanup_stack_if_exists(heat_client, template_name):
    stacks = heat_client.stacks.list()
    for stack in stacks:
        if stack.stack_name == template_name:
            heat_client.delete_stack(stack.id)


@pytest.fixture
def HeatStack(heatclientmanager, request):
    '''Fixture for creating/deleting a heat stack.'''
    def manage_stack(
            template_file,
            stack_name,
            parameters={},
            teardown=True,
            expect_fail=False
    ):
        def test_teardown():
            heatclientmanager.delete_stack(stack.id)

        template = get_file_contents(template_file)
        config = {}
        config['stack_name'] = stack_name
        config['template'] = template
        config['parameters'] = parameters
        # Call delete before create, in case previous teardown failed
        cleanup_stack_if_exists(heatclientmanager, stack_name)
        target_status = 'CREATE_COMPLETE'
        if expect_fail:
            target_status = 'CREATE_FAILED'
        stack = heatclientmanager.create_stack(
            config,
            target_status=target_status
        )
        if teardown:
            request.addfinalizer(test_teardown)
        return heatclientmanager, stack
    return manage_stack
