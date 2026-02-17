# Performance Report
### 1. Local Environment

| Scenario | Total Time | Avg Response Time | Throughput |
| :--- | :--- | :--- | :--- |
| **0** | 9.79s | 0.0049s | 204.36 ops/sec |
| **1** | 43.67s | 0.0022s | 458.00 ops/sec |
| **2** | 405.70s | 0.0020s | 492.97 ops/sec |

### 2. Google Cloud Small Machines  (2 vCPUs, 1 GB Memory)

| Scenario | Total Time | Avg Response Time | Throughput |
| :--- | :--- | :--- | :--- |
| **0** | 72.47s | 0.0362s | 27.60 ops/sec |
| **1** | 381.29s | 0.0191s | 52.45 ops/sec |
| **2** | 5860.79s | 0.0293s | 34.13 ops/sec |

![Evaluation Data](eval_data.png)
![Evaluation Data](eval_data_gcp.png)

We tested both local and cloud deployments of the system and noticed similar trends across scenarios for both deployments. The time taken increases with each scenario, and the average response time is measured by dividing the total time taken by the number of operations multiplied by the number of clients. This makes scenario 2 the sweet spot for average response time. A true average response time, which is difficult to measure in our system due to the multithreaded nature of the evaluation, should increase linearly in proportion with the total time taken. The server throughput results show that scenario 2 achieves the best throughput, we hypothesize that scenario 1 is limited by network resources (i.e. busy waiting), while scenario 3 has more difficulty keeping up with the number of connections.

It is worth mentioning that the cloud deployment is magnitudes slower than the local one. This is because the local machine has 16 cores + 32gb of ram while the cloud one is 2vCPUs and 2Gb of ram. Also network latency comes into play, the local machine has all services colocated on the same machine while the server ones are likely not. 
