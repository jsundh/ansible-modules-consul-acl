import json
from ansible.module_utils.common.dict_transformations import (
    camel_dict_to_snake_dict,
    snake_dict_to_camel_dict,
)
from ansible.module_utils.urls import fetch_url


class ConsulApi(object):
    def __init__(self, module):
        self.module = module
        self.url = module.params["url"]
        self.token = module.params["token"]

    def make_request(self, endpoint, method, data=None):
        if data is not None:
            data = json.dumps(data)

        endpoint_url = self.url + "/v1/" + endpoint
        headers = {"Content-Type": "application/json", "X-Consul-Token": self.token}

        response, info = fetch_url(
            self.module, endpoint_url, data=data, headers=headers, method=method
        )
        if response is None:
            self.module.fail_json(**info)

        status_code = info["status"]
        if status_code >= 400:
            self.module.fail_json(
                msg="API request failed",
                endpoint=endpoint_url,
                method=method,
                status=status_code,
                response=info["body"],
            )

        body = json.loads(response.read())
        if type(body) is bool:
            return body
        elif type(body) is list:
            return [camel_dict_to_snake_dict(e) for e in body]
        else:
            return camel_dict_to_snake_dict(body)
