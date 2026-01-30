# Performance Report
| Scenario | Total Time | Avg Response Time | Throughput |
|----------|-----------|-------------------|-----------|
| 0 | 4.16s | 0.0021s | 480.96 ops/sec |
| 1 | 26.86s | 0.0013s | 744.65 ops/sec |
| 2 | 293.80s | 0.0015s | 680.74 ops/sec |

![Evaluation Data](eval_data.png)

As we can see the first scenario where we connect 1 buyer and 1 seller, the throughput is lower than the other scenarios because the limiting factor is how fast we can receive and send data. In the second scenario where we connect 10 buyers and 10 sellers, we see the best numbers in terms of response time and throughput as the server is being utilized more effectively. In the final scenario where we connect 100 buyers and 100 sellers, we observe a decrease in throughput and a slight increase in response time (0.2ms). This can be attributed to either measurement variance or database connection constraints. 