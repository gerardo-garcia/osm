
##
# Copyright 2016 Canonical Ltd.
# Copyright 2017-18 Telefonica
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
##

from charmhelpers.core.hookenv import (
    action_get,
    action_fail,
    action_set,
    status_set,
)
from charms.reactive import (
    clear_flag,
    set_flag,
    when,
    when_not,
)
import charms.sshproxy


@when('sshproxy.configured')
@when_not('vnfconfiguratorclient.installed')
def install_generic_proxy_charm():
    """Post-install actions.

    This function will run when two conditions are met:
    1. The 'sshproxy.configured' state is set
    2. The 'configurator.installed' state is not set

    This ensures that the workload status is set to active only when the SSH
    proxy is properly configured.
    """
    set_flag('generic.installed')
    status_set('active', 'Ready!')


@when('actions.touch')
def touch():
    err = ''
    try:
        filename = action_get('filename')
        cmd = ['touch {}'.format(filename)]
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.touch')

@when('actions.get-day1-configuration')
def getDay1Configuration():
    err = ''
    try:
        # The code below is only a placeholder that has to be modified
        # It retrieves the params, and creates a command that will be
        # executed via ssh to get the day-1 configuration from the
        # external source
        param1 = action_get('param1')
        param2 = action_get('param2')
        param3 = action_get('param3')
        cmd = ['command {} {} {}'.format(param1,param2,param3)]
        result, err = charms.sshproxy._run(cmd)
        #End of the command"
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.get-day1-configuration')

