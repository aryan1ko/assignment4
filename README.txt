name: Aryan Kondapally
eid: avk639
comments: Minikube runs directly on the host (macOS, Docker Desktop driver), not
inside the multipass VM, so the Prometheus container can reach the application's
NodePort. The Service is NodePort on port 32767 and prometheus.yml scrapes
minikube:32767 ("minikube" is the name of the Minikube node container on the
minikube Docker network). The Deployment uses replicas: 1, because with more than
one replica the NodePort would spread the scrapes across Pods that each keep their
own counter, so the numbers in Prometheus would jump around.


Setup
-----
Install Docker
Install Minikube (on the host, NOT inside the multipass VM for this assignment)
Install kubectl


Start Minikube cluster on the host
----------------------------------
minikube start --container-runtime=docker

(Recent Minikube versions default to the containerd runtime. Without the
"--container-runtime=docker" flag there is no Docker daemon inside the Minikube node
and "minikube docker-env" cannot be used.)


Connect docker CLI on Host to Docker Daemon inside Minikube
------------------------------------------------------------
Linux/MacOS:
    eval $(minikube docker-env)

Windows (Powershell):
    minikube docker-env --shell powershell | Invoke-Expression

Verify:
    docker images

Run above steps from any terminal that you will use


Build container:
-----------------

docker build -t avk639-assignment4:latest .


Deploy application to Minikube:
-------------------------------
kubectl apply -f greetings.yaml


Try app endpoints:
------------------
    Linux:
        MINIKUBE_IP=$(minikube ip)
        URL=http://$MINIKUBE_IP:32767

    MacOS/Windows:
        Use either option 1 or option 2.
        Option 2 is better as the URL will not change even when you re-deploy the application.
        Option 1:
            minikube service greetings --url
            URL=<output from previous command>
            On Windows+Powershell
            $URL=<output from previous command>
        Option 2:
            Terminal 1:
                kubectl port-forward service/greetings 8081:80
            Terminal 2:
                URL="http://localhost:8081"

            On Windows+Powershell, set the variable like this:
            $URL = "http://localhost:8081"

    curl $URL
    curl $URL/greetings
    curl $URL/listcontents
    curl $URL/getk8sobjects


See Kubernetes resources:
-------------------------
kubectl get pods,services,configmaps,serviceaccounts,roles,rolebindings -l app=greetings


See Pod logs:
-------------
kubectl get pods -l app=greetings
kubectl logs <pod-name-from-above-output>


Delete application:
-------------------
kubectl delete -f greetings.yaml


Run Prometheus as a Docker container on the minikube network (Terminal 2):
--------------------------------------------------------------------------
docker run -d --name prometheus --network minikube -p 9090:9090 \
    -v ./prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

Run this from a terminal that is NOT connected to Minikube's Docker daemon, since
Prometheus has to run on the host's Docker daemon to join the "minikube" network.


Access Prometheus:
------------------
In a browser, open http://localhost:9090
    - Status -> Target health: the "greetings" target
      (http://minikube:32767/metrics) should be UP (green)
    - Query -> type custom_request_count_total and hit Execute
    - Switch to the Graph view and keep hitting the app endpoints; the counts per
      endpoint go up as a time series.

The counter is custom_request_count with an "endpoint" label, so there is one
series per endpoint:
    custom_request_count_total{endpoint="/"}
    custom_request_count_total{endpoint="/greetings"}
    custom_request_count_total{endpoint="/listcontents"}
    custom_request_count_total{endpoint="/getk8sobjects"}

(Prometheus client libraries add the "_total" suffix to counter names, which is why
the metric is queried as custom_request_count_total.)

The metrics can also be seen directly from the app:
    curl $URL/metrics | grep custom_request_count


Stop Prometheus:
----------------
docker rm -f prometheus
