#!/usr/bin/python

# GNU General Public License v3.0+ 
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: routeros_ip_pool
version_added: "2.9"
author: "Stoil Stoiov (@stoilstoilov)"
short_description: Manage entries in IP address pools on Mikrotik RouterOS 
description:
  - The module provides basic management actions on IP address pools entries in 
  Mikrotik RouterOS. Address lists can be used to describes groups of network 
  addresses and ranges under a named address list.
options:
  ranges:
    description:
      - Ranges of IP addresses
    required: true
  name:
    description:
      - Name for the IP address pool
    required: true
  state:
    description:
      - Desired state - to create the entry, remove it, enable or disable it.
    default: present  
"""

EXAMPLES = """
tasks:
  - name: Add an IP address entry to an address list
    routeros_ip_pool:
      ranges: 192.168.88.10-192.168.88.100
      name: dhcp-pool
  
  - name: Enable an address list entry
    routeros_ip_pool:
      ranges: 192.168.88.10-192.168.88.100
      name: dhcp-pool
      state: enabled
  
  - name: Disable an address list entry
    routeros_ip_pool:
      ranges: 192.168.88.10-192.168.88.100
      name: dhcp-pool
      state: disabled

  - name: Remove an address list entry
    routeros_ip_pool:
      ranges: 192.168.88.10-192.168.88.100
      name: dhcp-pool
      state: absent
"""

RETURN = """
stdout:
  description: The command line respones
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: [['...', '...'], ['...'], ['...']]
failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
"""

import re
import time

from ansible.module_utils.network.routeros.routeros import run_commands
from ansible.module_utils.network.routeros.routeros import routeros_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.six import string_types


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item


def main():
    # Entry point for module execution
    
    # Module arguments definition
    module_args = dict(
        ranges=dict(type='str', required=True),
        name=dict(type='str', required=True),        
        state=dict(default='present', choices=['present', 'absent', 'enabled', 'disabled']),
    )    
  
    # Module initialization

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # Prepare command line statements

    set_ip_command = ""
    responses = []

    # Context line is the common part of the command line for a specific configurational context in the CLI
    ctx_line = "/ip pool "

    # Lookup line is the query used to lookup and find configuration entries
    lookup_line = 'where name="' + module.params['name'] + '"'
    
    # Result dictionary. Initialized with changed=False. 
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # Get the desired state
    state = module.params['state']

    # Check if entry exists
    count_command = ctx_line + ' print count-only ' + lookup_line
    entry_exist = list(to_lines(run_commands(module, count_command)))
    entry_exist = int(entry_exist[-1][-1])

    # Execute configuration for desired state
    if entry_exist > 0:
      if state == "present":
        result.update({'changed': False, 'message': 'No change required.'})
      elif state == "absent":
        set_ip_command = ctx_line + "remove [find " + lookup_line + "]"
      elif state == "disabled":
        set_ip_command = ctx_line + "disable [find " + lookup_line + "]"
      elif state == "enabled":
        set_ip_command = ctx_line + "enable [find " + lookup_line + "]"

    if entry_exist == 0:
      if state == "present":
        set_ip_command = ctx_line + "add ranges=" + module.params['ranges'] + " name=" + module.params['name']
      else:
        result.update({'changed': False, 'message': 'Entry not found.'})              

    if set_ip_command:
      responses = run_commands(module, set_ip_command)      
      if "failure:" not in responses[-1]:
          result.update({'changed': True})

    result.update({        
        'command': set_ip_command,
        'state': state,
        'count_command': count_command,
        'entries': entry_exist,
        'stdout': responses,        
        'stdout_lines': list(to_lines(responses))
    })

    module.exit_json(**result)

if __name__ == '__main__':
    main()