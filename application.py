from flask import Flask, request, Response
import os
import json

from kubernetes import client, config
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)


# Prometheus counter for the number of times each endpoint is called.
# The endpoint name is added as a label so each endpoint gets its own time series.
custom_request_count = Counter(
    "custom_request_count",
    "Number of times an application endpoint has been called",
    ["endpoint"],
)


@app.route("/")
def hello():
    custom_request_count.labels(endpoint="/").inc()
    return "Hello World!"


@app.route("/greetings")
def greetings():
    custom_request_count.labels(endpoint="/greetings").inc()
    greeting = os.getenv("GREETING")
    return greeting


@app.route("/listcontents")
def listcontents():
    custom_request_count.labels(endpoint="/listcontents").inc()
    contents = os.listdir("/hostfolder")
    fp = open("/hostfolder/filenames.txt","r")
    lines = fp.readlines()
    return lines


@app.route("/getk8sobjects")
def get_cluster_details():
    custom_request_count.labels(endpoint="/getk8sobjects").inc()
    config.load_incluster_config()

    # Requirement 1.2
    # Read NAMESPACE env var
    namespace = os.getenv("NAMESPACE")

    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace)

    output = {}

    pod_names = []
    for pod in pods.items:
        pod_names.append(pod.metadata.name)
    output["pods"] = pod_names

    cfg_map_names = []
    configmaps = v1.list_namespaced_config_map(namespace)
    for configmap in configmaps.items:
        cfg_map_names.append(configmap.metadata.name)
    output["configmaps"] = cfg_map_names

    sa_names = []
    serviceaccounts = v1.list_namespaced_service_account(namespace)
    for serviceaccount in serviceaccounts.items:
        sa_names.append(serviceaccount.metadata.name)
    output["serviceaccounts"] = sa_names

    rbac_api = client.RbacAuthorizationV1Api()

    # Requirement 1.3
    # Use rbac_api to get roles
    role_names = []
    roles = rbac_api.list_namespaced_role(namespace)
    for role in roles.items:
        role_names.append(role.metadata.name)
    output["roles"] = role_names

    # Requirement 1.4
    # Use rbac_api to get rolebindings
    rolebinding_names = []
    rolebindings = rbac_api.list_namespaced_role_binding(namespace)
    for rolebinding in rolebindings.items:
        rolebinding_names.append(rolebinding.metadata.name)
    output["rolebindings"] = rolebinding_names

    obj_to_return = json.dumps(output)
    return obj_to_return


@app.route("/metrics")
def metrics():
    # Endpoint that Prometheus scrapes to pull the metrics from this app.
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
