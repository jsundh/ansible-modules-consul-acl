# ansible-modules-consul-acl

Ansible modules for the [Consul ACL system](https://www.consul.io/docs/agent/acl-system.html):

-   `consul_acl_policy`
-   `consul_acl_token`

## Installation

Install using pip:

```
pip install ansible-modules-consul-acl
```

The modules have no external dependencies except Ansible.

## Usage

The documentation for each module is mostly complete - use `ansible-doc` to view it.

### Example

<!--prettier-ignore-->
```yaml
- name: Create ACL policy
  consul_acl_policy:
    name: example
    # Rules specified as an HCL string
    rules: |
      service "example" {
        policy = "write"
      }
    state: present
    url: https://localhost:8500
    token: a22c5e4f-0f48-4907-82db-843c6baf75be # Requires acl:write
  register: consul_acl_policy

- name: Create ACL token
  consul_acl_token:
    description: Example token
    # Policies specified as a list of PolicyLink objects: https://www.consul.io/api/acl/tokens.html#policies
    policies:
      - id: "{{ consul_acl_policy.id }}"
    local: true
    state: present
    url: https://localhost:8500
    token: a22c5e4f-0f48-4907-82db-843c6baf75be # Requires acl:write
  register: consul_acl_token
```

### Environment variables

Some of the environment variables for the [Consul CLI](https://www.consul.io/docs/commands/index.html#environment-variables) will be used if they are defined:

-   `CONSUL_HTTP_ADDR` for the `url` parameter. Prefix with `https://` instead of setting `CONSUL_HTTP_SSL=true`
-   `CONSUL_HTTP_TOKEN` for the `token` parameter
-   `CONSUL_CLIENT_CERT` for the `client_cert` parameter
-   `CONSUL_CLIENT_KEY` for the `client_key` parameter

## Testing locally

To run the functional tests, set the following environment variables
from the project root directory:

```sh
export ANSIBLE_LIBRARY="$PWD/ansible/modules/consul_acl"
export ANSIBLE_MODULE_UTILS="$PWD/ansible/module_utils"
```

Then run the test playbooks in a Python environment without `ansible-modules-consul-acl` installed.
