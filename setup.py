import setuptools

long_description = open("README.md", "r").read().strip()

setuptools.setup(
    name="ansible-modules-consul-acl",
    version="0.2.0",
    description="Ansible modules for the Consul ACL system",
    long_description=long_description,
    author="Jakob Sundh",
    author_email="jsundh@users.noreply.github.com",
    url="https://github.com/jsundh/ansible-modules-consul-acl",
    packages=["ansible/modules/consul_acl"],
    install_requires=["ansible>=2.4.0"],
    license="GNU GPL v3",
)
