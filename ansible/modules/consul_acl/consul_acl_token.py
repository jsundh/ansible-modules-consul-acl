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
module: consul_acl_token

short_description: Manage Consul ACL tokens

version_added: "N/A"

description:
  - "Create, update and delete tokens for the new Consul ACL system."
  - "Official API documentation: https://www.consul.io/api/acl/tokens.html"

options:
  accessor_id:
    description:
     - The accessor ID of either an existing token to update or a non-existing to create.
     - If not specified, Consul will generate an UUID when creating a token.
    type: str
    required: false
  secret_id:
    description:
     - The secret ID of the token.
     - If not specified, Consul will generate an UUID when creating a token.
    type: str
    required: false
  description:
    description:
      - Free form human readable description of the token.
    type: str
    default: ""
  policies:
    description:
      - The list of policies that should be applied to the token.
      - Each element should be an object with an "id" and/or "name" field for an existing policy.
      - Required when C(state=present).
    type: list
    element: dict
    required: false
  local:
    description:
      - If true, the token will be local to the current datacenter.
    type: bool
    default: false
  match_description:
    description:
      - If true, the module will attempt to match an existing token based on description by listing all tokens.
      - Allows matching existing tokens without saving the accessor ID.
      - Only use this if you are sure that the token descriptions are sufficiently unique.
    type: bool
    default: false
  state:
    description:
        - If C(present), a token will be created or updated.
        - If C(absent), the token will be removed if it exists.
        - If C(cloned), the given token accessor ID will be cloned.
    type: str
    default: present
    choices: [ present, absent, cloned ]
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
"""

RETURN = """
operation:
  description: Operation performed - either 'create', 'update', 'delete' or 'none'
  returned: always
  type: str
  sample: create
accessor_id:
  description: The accessor ID of the token
  returned: when state != 'absent'
  type: str
  sample: 6a524d8b-b8d5-4e81-82b3-625aeefb40f6
secret_id:
  description: The secret ID of the token
  returned: when state != 'absent'
  type: str
  sample: 45a3bd52-07c7-47a4-52fd-0745e0cfe967
hash:
  description: The token content hash
  returned: when state == 'present'
  type: str
  sample: RV0EhBF/LkDrzjrI+4AMm1MqlX6X/J2JgW4S9uBkBu0=
description:
  description: Free form human readable description of the token
  returned: when state != 'absent'
  type: str
  sample: An example token
policies:
  description: The list of policy links connected to the token
  returned: when state != 'absent'
  type: list
"""

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.consul_acl import ConsulApi
from itertools import chain


class ConsulAclToken(object):
    def __init__(self, module, api):
        self.module = module
        self.api = api

    def get_token(self, accessor_id):
        return self.api.make_request(
            "acl/token/" + accessor_id, "GET", ignore_error=403
        )

    def find_token(self, description, policies):
        policy_filter = ""
        for link in policies:
            if "id" in link:
                policy_filter = "?policy=" + link["id"]
                break

        tokens = self.api.make_request("acl/tokens" + policy_filter, "GET")
        for token in tokens:
            if token["description"] == description:
                return self.get_token(token["accessor_id"])

        return None

    def create_token(self, **kwargs):
        created = self.api.make_request("acl/token", "PUT", kwargs)

        return dict(changed=True, operation="create", **created)

    def update_token(self, current, **kwargs):
        if current.get("policies") is None:
            current["policies"] = []

        if not has_token_changed(current, kwargs):
            return dict(changed=False, operation="none", **current)

        accessor_id = current["accessor_id"]
        updated = self.api.make_request("acl/token/" + accessor_id, "PUT", data=kwargs)

        return dict(changed=True, operation="update", **updated)

    def delete_token(self, accessor_id):
        succeeded = self.api.make_request("acl/token/" + accessor_id, "DELETE")
        if not succeeded:
            self.module.fail_json(msg="Token deletion failed")

        return dict(changed=True, operation="delete", accessor_id=accessor_id)

    def clone_token(self, accessor_id):
        cloned = self.api.make_request("acl/token/{}/clone".format(accessor_id), "PUT")

        return dict(changed=True, operation="clone", **cloned)


def is_policies_param_valid(policies):
    allowed_keys = set(("id", "name"))
    for link in policies:
        link_keys = set(link.keys())
        if len(allowed_keys & link_keys) == 0:
            return False
        if len(link_keys - allowed_keys) > 0:
            return False

    return True


def has_token_changed(current, updated):
    for k, v in updated.items():
        # Ignore empty secret_id
        if v is None and k.lower() == "secret_id".lower():
            continue
        if k == "policies":
            continue
        elif current.get(k) != v:
            return True

    # Compare policy links
    # TODO: Handle policies changing names
    current_names = set()
    current_ids = set()
    difference = 0
    for link in current["policies"]:
        current_names.add(link["name"])
        current_ids.add(link["id"])
        difference += 1

    for link in updated["policies"]:
        if link.get("id") in current_ids:
            difference -= 1
        elif link.get("name") in current_names:
            difference -= 1
        else:
            return True

    return difference != 0


def main():
    arg_spec = dict(
        accessor_id=dict(type="str", default=None),
        policies=dict(type="list", elements="dict", default=None),
        description=dict(type="str", default=""),
        local=dict(type="bool", default=False),
        match_description=dict(type="bool", default=False),
        state=dict(
            type="str", choices=["present", "absent", "cloned"], default="present"
        ),
        url=dict(type="str", default=os.environ.get("CONSUL_HTTP_ADDR")),
        token=dict(type="str", default=os.environ.get("CONSUL_HTTP_TOKEN")),
        validate_certs=dict(type="bool", default=True),
        client_cert=dict(type="path", default=os.environ.get("CONSUL_CLIENT_CERT")),
        client_key=dict(type="path", default=os.environ.get("CONSUL_CLIENT_KEY")),
        secret_id=dict(type="str", default=None),
    )

    module = AnsibleModule(argument_spec=arg_spec, supports_check_mode=False)

    accessor_id = module.params["accessor_id"]
    policies = module.params["policies"] or []
    description = module.params["description"]
    local = module.params["local"]
    match_description = module.params["match_description"]
    state = module.params["state"]
    url = module.params["url"]
    token = module.params["token"]
    secret_id = module.params["secret_id"]

    if not url:
        module.fail_json(msg="url must be set")
    if not token:
        module.fail_json(msg="token must be set")
    if state == "present" and not is_policies_param_valid(policies):
        module.fail_json(msg="policies must set when state == 'present'")
    if state == "cloned" and not accessor_id:
        module.fail_json(msg="accessor_id must be set when state == 'cloned'")
    if match_description and not description:
        module.fail_json(msg="description cannot be empty when matching by description")

    api = ConsulApi(module)
    consul_acl = ConsulAclToken(module, api)

    if match_description and not accessor_id:
        current_token = consul_acl.find_token(description, policies)
    elif accessor_id:
        current_token = consul_acl.get_token(accessor_id)
    else:
        current_token = None

    kwargs = dict(policies=policies, description=description, local=local, secret_id=secret_id)
    if state == "present" and current_token:
        result = consul_acl.update_token(current_token, **kwargs)
    elif state == "present":
        result = consul_acl.create_token(accessor_id=accessor_id, **kwargs)
    elif state == "cloned":
        result = consul_acl.clone_token(accessor_id)
    elif state == "absent" and accessor_id:
        result = consul_acl.delete_token(accessor_id)
    else:
        result = dict(changed=False, operation="none")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
