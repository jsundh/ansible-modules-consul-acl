#!/usr/bin/python

# Copyright: (c) 2019, Jakob Sundh <jsundh@users.noreply.github.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: consul_acl_policy

short_description: Manage Consul ACL policies

version_added: "N/A"

description:
  - "Create, update and delete policies for the new Consul ACL system."
  - "Official API documentation: https://www.consul.io/api/acl/policies.html"

options:
  id:
    description:
      - The policy ID.
      - If not provided, the name will be used to match an existing policy.
    type: str
  name:
    description:
      - Name of the ACL policy.
      - Required when C(state=present).
    type: str
  description:
    description:
      - Free form human readable description of the policy.
    type: str
    default: ""
  rules:
    description:
      - "Policy rules following the HCL rule specification: https://www.consul.io/docs/agent/acl-rules.html#rule-specification."
      - Required when C(state=present).
    type: str
  state:
    description:
        - If C(present), the policy will be created or updated.
        - If C(absent), the policy will be removed if it exists.
    type: str
    default: present
    choices: [ present, absent ]
  url:
    description:
      - URL for Consul.
    type: str
    required: true
    default: the environment variable CONSUL_HTTP_ADDR
  token:
    description:
      - ACL token to use for requests.
    type: str
    required: true
    default: the environment variable CONSUL_HTTP_TOKEN
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated.
      - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    type: bool
    default: yes
  client_cert:
    description:
      - PEM formatted certificate chain file to be used for SSL client authentication.
      - This file can also include the key as well, and if the key is included, I(client_key) is not required
    type: path
    default: the environment variable CONSUL_CLIENT_CERT
  client_key:
    description:
      - PEM formatted file that contains your private key to be used for SSL client authentication.
      - If I(client_cert) contains both the certificate and key, this option is not required.
    type: path
    default: the environment variable CONSUL_CLIENT_KEY

author:
    - Jakob Sundh (@jsundh)
"""

EXAMPLES = """
- name: Create policy
  consul_acl_policy:
    name: example
    description: An example policy
    rules: |
      kv_prefix "example" {
        policy = "write"
      }
    state: present
    url: http://localhost:8500
    token: "consul-management-token"
  register: consul_acl_policy

- name: Update policy by ID
  consul_acl_policy:
    name: example
    id: "{{ consul_acl_policy.id }}"
    description: An updated example policy
    rules: |
      kv_prefix "example" {
        policy = "read"
      }
    state: present
    url: http://localhost:8500
    token: "consul-management-token"

- name: Remove policy by name
  consul_acl_policy:
    name: example
    state: absent
    url: http://localhost:8500
    token: "consul-management-token"
"""

RETURN = """
operation:
  description: Operation performed - either 'create', 'update', 'delete' or 'none'
  returned: always
  type: str
  sample: create
id:
  description: The ID of the policy
  returned: when operation != 'none'
  type: str
  sample: 6a524d8b-b8d5-4e81-82b3-625aeefb40f6
hash:
  description: The policy content hash
  returned: when state == 'present'
  type: str
  sample: RV0EhBF/LkDrzjrI+4AMm1MqlX6X/J2JgW4S9uBkBu0=
"""

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.consul_acl import ConsulApi


class ConsulAclPolicy(object):
    def __init__(self, module, api):
        self.module = module
        self.api = api

    def find_existing_policy(self, name):
        policies = self.api.make_request("acl/policies", "GET")
        for policy in policies:
            if policy["name"] == name:
                return policy["id"]

        return None

    def create_policy(self, **kwargs):
        created = self.api.make_request("acl/policy", "PUT", data=kwargs)

        return dict(changed=True, operation="create", **created)

    def update_policy(self, policy_id, **kwargs):
        current = self.api.make_request("acl/policy/" + policy_id, "GET")

        if not has_policy_changed(current, kwargs):
            return dict(changed=False, operation="none", **current)

        updated = self.api.make_request("acl/policy/" + policy_id, "PUT", data=kwargs)
        return dict(changed=True, operation="update", **updated)

    def delete_policy(self, policy_id):
        succeeded = self.api.make_request("acl/policy/" + policy_id, "DELETE")
        if not succeeded:
            self.module.fail_json(msg="Policy deletion failed")

        return dict(changed=True, operation="delete", id=policy_id)


def has_policy_changed(current, updated):
    for k, v in updated.items():
        # Empty list default for datacenters
        if current.get(k, []) != v:
            return True

    return False


def main():
    argument_spec = dict(
        id=dict(type="str", default=None),
        name=dict(type="str", default=None),
        rules=dict(type="str", default=None),
        description=dict(type="str", default=""),
        datacenters=dict(type="list", elements="str", default=None),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        url=dict(type="str", default=os.environ.get("CONSUL_HTTP_ADDR")),
        token=dict(type="str", default=os.environ.get("CONSUL_HTTP_TOKEN")),
        validate_certs=dict(type="bool", default=True),
        client_cert=dict(type="path", default=os.environ.get("CONSUL_CLIENT_CERT")),
        client_key=dict(type="path", default=os.environ.get("CONSUL_CLIENT_KEY")),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    name = module.params["name"]
    policy_id = module.params["id"]
    rules = module.params["rules"]
    description = module.params["description"]
    datacenters = module.params["datacenters"] or []
    state = module.params["state"]
    url = module.params["url"]
    token = module.params["token"]

    if not url:
        module.fail_json(msg="url must be set")
    if not token:
        module.fail_json(msg="token must be set")
    if state == "present" and not name:
        module.fail_json(msg="name must be set when state == 'present'")
    if state == "present" and not rules:
        module.fail_json(msg="rules must be set when state == 'present'")

    api = ConsulApi(module)
    consul_acl = ConsulAclPolicy(module, api)

    if not policy_id:
        policy_id = consul_acl.find_existing_policy(name)

    kwargs = dict(
        name=name, rules=rules, description=description, datacenters=datacenters
    )
    if state == "present" and policy_id:
        result = consul_acl.update_policy(policy_id, **kwargs)
    elif state == "present":
        result = consul_acl.create_policy(**kwargs)
    elif state == "absent" and policy_id:
        result = consul_acl.delete_policy(policy_id)
    else:
        result = dict(changed=False, operation="none")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
