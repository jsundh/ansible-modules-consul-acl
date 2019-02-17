# ansible-modules-consul-acl

Ansible modules for the [Consul ACL system](https://www.consul.io/docs/agent/acl-system.html).

## Installation

Install using pip:

```
pip install ansible-modules-consul-acl
```

The modules have no external dependencies except Ansible.

## Usage

The documentation for each module is mostly complete, although it is currently not generated anywhere:

-   [consul_acl_policy](ansible/modules/consul_acl/consul_acl_policy.py)
-   [consul_acl_token](ansible/modules/consul_acl/consul_acl_token.py)

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
