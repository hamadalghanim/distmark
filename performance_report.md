# Performance Report

## 1. All replicas run normally (no failures)

### 1.1 - 1 seller, 1 buyer
**Summary:**
* **Elapsed:** 149.62s
* **Total ops:** 2000 (0 errors)
* **Throughput:** 13.4 ops/sec
* **Buyer Avg Response Time:** 70.04 ms
* **Seller Avg Response Time:** 149.62 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer DELETE /cart/items/{id} | 75 | 102.8 | 0 |
| buyer GET /cart | 106 | 64.3 | 0 |
| buyer GET /categories | 84 | 67.6 | 0 |
| buyer GET /items/search | 76 | 40.0 | 0 |
| buyer GET /items/{id} | 85 | 67.1 | 0 |
| buyer GET /purchases | 69 | 81.0 | 0 |
| buyer GET /seller/{id}/rating | 89 | 68.7 | 0 |
| buyer POST /account/login | 1 | 66.1 | 0 |
| buyer POST /account/logout | 1 | 64.1 | 0 |
| buyer POST /account/register | 1 | 78.4 | 0 |
| buyer POST /cart/clear | 77 | 60.7 | 0 |
| buyer POST /cart/items | 90 | 75.8 | 0 |
| buyer POST /cart/save | 91 | 87.2 | 0 |
| buyer POST /feedback | 79 | 61.7 | 0 |
| buyer POST /purchase | 76 | 64.1 | 0 |
| seller GET /categories | 164 | 57.9 | 0 |
| seller GET /items | 175 | 56.8 | 0 |
| seller GET /seller/rating | 169 | 50.3 | 0 |
| seller POST /account/login | 1 | 263.9 | 0 |
| seller POST /account/logout | 1 | 232.5 | 0 |
| seller POST /account/register | 1 | 584.0 | 0 |
| seller POST /items | 138 | 241.7 | 0 |
| seller PUT /items/price | 170 | 249.8 | 0 |
| seller PUT /items/quantity | 181 | 247.4 | 0 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| seller/s0_u0 | 1000 | 149.6 | 0 |
| buyer/s0_u0 | 1000 | 70.0 | 0 |

---

### 1.2 - 10 sellers, 10 buyers
**Summary:**
* **Elapsed:** 309.02s
* **Total ops:** 20000 (0 errors)
* **Throughput:** 64.7 ops/sec
* **Buyer Avg Response Time:** 131.23 ms
* **Seller Avg Response Time:** 305.45 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer DELETE /cart/items/{id} | 856 | 173.5 | 0 |
| buyer GET /cart | 815 | 108.1 | 0 |
| buyer GET /categories | 820 | 104.1 | 0 |
| buyer GET /items/search | 820 | 92.6 | 0 |
| buyer GET /items/{id} | 845 | 115.6 | 0 |
| buyer GET /purchases | 869 | 91.4 | 0 |
| buyer GET /seller/{id}/rating | 862 | 109.0 | 0 |
| buyer POST /account/login | 10 | 118.8 | 0 |
| buyer POST /account/logout | 10 | 316.3 | 0 |
| buyer POST /account/register | 10 | 113.9 | 0 |
| buyer POST /cart/clear | 831 | 171.6 | 0 |
| buyer POST /cart/items | 817 | 151.4 | 0 |
| buyer POST /cart/save | 788 | 199.0 | 0 |
| buyer POST /feedback | 795 | 125.3 | 0 |
| buyer POST /purchase | 852 | 135.1 | 0 |
| seller GET /categories | 1714 | 193.6 | 0 |
| seller GET /items | 1609 | 207.6 | 0 |
| seller GET /seller/rating | 1659 | 201.5 | 0 |
| seller POST /account/login | 10 | 668.9 | 0 |
| seller POST /account/logout | 10 | 268.7 | 0 |
| seller POST /account/register | 10 | 327.3 | 0 |
| seller POST /items | 1674 | 412.8 | 0 |
| seller PUT /items/price | 1651 | 406.9 | 0 |
| seller PUT /items/quantity | 1663 | 408.2 | 0 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| seller/s0_u0 | 1000 | 309.0 | 0 |
| seller/s0_u7 | 1000 | 307.9 | 0 |
| seller/s0_u8 | 1000 | 306.7 | 0 |
| seller/s0_u3 | 1000 | 305.8 | 0 |
| seller/s0_u6 | 1000 | 305.3 | 0 |

---

### 1.3 - 100 sellers, 100 buyers
**Summary:**
* **Elapsed:** 4748.99s
* **Total ops:** 199914 (86 errors)
* **Throughput:** 42.1 ops/sec
* **Buyer Avg Response Time:** 4731.08 ms
* **Seller Avg Response Time:** 2961.69 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer DELETE /cart/items/{id} | 8291 | 4961.8 | 0 |
| buyer GET /cart | 8243 | 4659.3 | 0 |
| buyer GET /categories | 8225 | 4650.3 | 0 |
| buyer GET /items/search | 8294 | 4563.8 | 0 |
| buyer GET /items/{id} | 8254 | 4607.7 | 0 |
| buyer GET /purchases | 8376 | 4604.6 | 0 |
| buyer GET /seller/{id}/rating | 8336 | 4652.6 | 0 |
| buyer POST /account/login | 100 | 1300.9 | 0 |
| buyer POST /account/logout | 100 | 4526.8 | 0 |
| buyer POST /account/register | 100 | 676.1 | 0 |
| buyer POST /cart/clear | 8281 | 4953.6 | 20 |
| buyer POST /cart/items | 8283 | 4963.4 | 21 |
| buyer POST /cart/save | 8339 | 4948.7 | 22 |
| buyer POST /feedback | 8320 | 4660.0 | 14 |
| buyer POST /purchase | 8372 | 4640.5 | 9 |
| seller GET /categories | 16868 | 2849.4 | 0 |
| seller GET /items | 16549 | 2861.4 | 0 |
| seller GET /seller/rating | 16623 | 2846.2 | 0 |
| seller POST /account/login | 100 | 5500.6 | 0 |
| seller POST /account/logout | 100 | 3083.5 | 0 |
| seller POST /account/register | 100 | 2769.6 | 0 |
| seller POST /items | 16632 | 3080.4 | 0 |
| seller PUT /items/price | 16591 | 3063.0 | 0 |
| seller PUT /items/quantity | 16437 | 3057.3 | 0 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer/s1_u45 | 1000 | 4748.7 | 0 |
| buyer/s1_u85 | 1000 | 4747.2 | 0 |
| buyer/s1_u94 | 1000 | 4747.1 | 0 |
| buyer/s1_u32 | 1000 | 4746.7 | 0 |
| buyer/s1_u43 | 1000 | 4746.7 | 0 |

---

## 2. One seller failure and one buyer failure

### 2.1 - 1 seller, 1 buyer
**Summary:**
* **Elapsed:** 186.37s
* **Total ops:** 1029 (40 errors)
* **Throughput:** 5.5 ops/sec
* **Buyer Avg Response Time:** 67.98 ms
* **Seller Avg Response Time:** 141.61 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer DELETE /cart/items/{id} | 0 | 0.0 | 2 |
| buyer GET /cart | 4 | 51.6 | 2 |
| buyer GET /categories | 5 | 65.9 | 6 |
| buyer GET /items/search | 3 | 39.3 | 2 |
| buyer GET /items/{id} | 3 | 102.8 | 5 |
| buyer GET /purchases | 3 | 52.2 | 1 |
| buyer GET /seller/{id}/rating | 3 | 58.4 | 3 |
| buyer POST /account/login | 1 | 68.2 | 0 |
| buyer POST /account/logout | 0 | 0.0 | 1 |
| buyer POST /account/register | 1 | 179.3 | 0 |
| buyer POST /cart/items | 2 | 63.1 | 7 |
| buyer POST /cart/save | 0 | 0.0 | 4 |
| buyer POST /feedback | 0 | 0.0 | 5 |
| buyer POST /purchase | 4 | 75.9 | 2 |
| seller GET /categories | 167 | 48.5 | 0 |
| seller GET /items | 172 | 58.0 | 0 |
| seller GET /seller/rating | 165 | 49.4 | 0 |
| seller POST /account/login | 1 | 311.4 | 0 |
| seller POST /account/logout | 1 | 270.1 | 0 |
| seller POST /account/register | 1 | 476.0 | 0 |
| seller POST /items | 165 | 240.1 | 0 |
| seller PUT /items/price | 169 | 229.7 | 0 |
| seller PUT /items/quantity | 159 | 225.7 | 0 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| seller/s0_u0 | 1000 | 141.6 | 0 |
| buyer/s0_u0 | 29 | 68.0 | 40 |

---

### 2.2 - 10 sellers, 10 buyers
**Summary:**
* **Elapsed:** 287.40s
* **Total ops:** 10000 (20 errors)
* **Throughput:** 34.8 ops/sec
* **Buyer Avg Response Time:** N/A (all failed)
* **Seller Avg Response Time:** 283.07 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer POST /account/login | 0 | 0.0 | 10 |
| buyer POST /account/register | 0 | 0.0 | 10 |
| seller GET /categories | 1717 | 179.6 | 0 |
| seller GET /items | 1644 | 193.8 | 0 |
| seller GET /seller/rating | 1657 | 176.7 | 0 |
| seller POST /account/login | 10 | 496.9 | 0 |
| seller POST /account/logout | 10 | 315.0 | 0 |
| seller POST /account/register | 10 | 392.1 | 0 |
| seller POST /items | 1663 | 386.9 | 0 |
| seller PUT /items/price | 1682 | 382.4 | 0 |
| seller PUT /items/quantity | 1607 | 381.0 | 0 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| seller/s0_u0 | 1000 | 287.2 | 0 |
| seller/s0_u8 | 1000 | 284.7 | 0 |
| seller/s0_u6 | 1000 | 284.6 | 0 |
| seller/s0_u2 | 1000 | 284.5 | 0 |
| seller/s0_u3 | 1000 | 284.4 | 0 |

---

### 2.3 - 100 sellers, 100 buyers
**Summary:**
* **Elapsed:** 7.19s
* **Total ops:** 58 (342 errors)
* **Throughput:** 8.1 ops/sec
* **Buyer Avg Response Time:** N/A (all failed)
* **Seller Avg Response Time:** 1549.90 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer POST /account/login | 0 | 0.0 | 100 |
| buyer POST /account/register | 0 | 0.0 | 100 |
| seller POST /account/login | 0 | 0.0 | 100 |
| seller POST /account/register | 58 | 1549.9 | 42 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| seller/s1_u62 | 1 | 2958.9 | 1 |
| seller/s1_u64 | 1 | 2953.0 | 1 |
| seller/s1_u30 | 1 | 2884.7 | 1 |
| seller/s1_u66 | 1 | 2837.8 | 1 |
| seller/s1_u33 | 1 | 2765.4 | 1 |

---

## 3. One seller failure (follower failure)

### 3.1 - 1 seller, 1 buyer
**Summary:**
* **Elapsed:** 144.23s
* **Total ops:** 2000 (0 errors)
* **Throughput:** 13.9 ops/sec
* **Buyer Avg Response Time:** 55.55 ms
* **Seller Avg Response Time:** 144.12 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer DELETE /cart/items/{id} | 97 | 58.3 | 0 |
| buyer GET /cart | 76 | 51.3 | 0 |
| buyer GET /categories | 80 | 62.8 | 0 |
| buyer GET /items/search | 79 | 39.3 | 0 |
| buyer GET /items/{id} | 86 | 54.0 | 0 |
| buyer GET /purchases | 99 | 49.1 | 0 |
| buyer GET /seller/{id}/rating | 78 | 52.4 | 0 |
| buyer POST /account/login | 1 | 73.3 | 0 |
| buyer POST /account/logout | 1 | 69.6 | 0 |
| buyer POST /account/register | 1 | 107.2 | 0 |
| buyer POST /cart/clear | 92 | 58.5 | 0 |
| buyer POST /cart/items | 71 | 61.7 | 0 |
| buyer POST /cart/save | 68 | 58.8 | 0 |
| buyer POST /feedback | 98 | 59.3 | 0 |
| buyer POST /purchase | 73 | 61.0 | 0 |
| seller GET /categories | 173 | 49.9 | 0 |
| seller GET /items | 179 | 56.5 | 0 |
| seller GET /seller/rating | 162 | 50.6 | 0 |
| seller POST /account/login | 1 | 235.9 | 0 |
| seller POST /account/logout | 1 | 269.7 | 0 |
| seller POST /account/register | 1 | 263.4 | 0 |
| seller POST /items | 146 | 244.1 | 0 |
| seller PUT /items/price | 177 | 244.9 | 0 |
| seller PUT /items/quantity | 160 | 233.9 | 0 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| seller/s0_u0 | 1000 | 144.1 | 0 |
| buyer/s0_u0 | 1000 | 55.6 | 0 |

---

### 3.2 - 10 sellers, 10 buyers
**Summary:**
* **Elapsed:** 305.37s
* **Total ops:** 20000 (0 errors)
* **Throughput:** 65.5 ops/sec
* **Buyer Avg Response Time:** 95.34 ms
* **Seller Avg Response Time:** 300.74 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer DELETE /cart/items/{id} | 865 | 114.5 | 0 |
| buyer GET /cart | 816 | 86.7 | 0 |
| buyer GET /categories | 850 | 75.1 | 0 |
| buyer GET /items/search | 831 | 65.8 | 0 |
| buyer GET /items/{id} | 828 | 77.2 | 0 |
| buyer GET /purchases | 817 | 83.3 | 0 |
| buyer GET /seller/{id}/rating | 871 | 84.3 | 0 |
| buyer POST /account/login | 10 | 123.6 | 0 |
| buyer POST /account/logout | 10 | 333.5 | 0 |
| buyer POST /account/register | 10 | 108.7 | 0 |
| buyer POST /cart/clear | 761 | 118.3 | 0 |
| buyer POST /cart/items | 835 | 122.7 | 0 |
| buyer POST /cart/save | 826 | 120.9 | 0 |
| buyer POST /feedback | 861 | 95.3 | 0 |
| buyer POST /purchase | 809 | 98.4 | 0 |
| seller GET /categories | 1622 | 192.6 | 0 |
| seller GET /items | 1646 | 204.6 | 0 |
| seller GET /seller/rating | 1605 | 196.0 | 0 |
| seller POST /account/login | 10 | 508.3 | 0 |
| seller POST /account/logout | 10 | 350.2 | 0 |
| seller POST /account/register | 10 | 475.4 | 0 |
| seller POST /items | 1690 | 404.5 | 0 |
| seller PUT /items/price | 1721 | 393.8 | 0 |
| seller PUT /items/quantity | 1686 | 396.8 | 0 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| seller/s1_u5 | 1000 | 304.9 | 0 |
| seller/s1_u4 | 1000 | 302.4 | 0 |
| seller/s1_u2 | 1000 | 301.5 | 0 |
| seller/s1_u1 | 1000 | 301.4 | 0 |
| seller/s1_u0 | 1000 | 301.2 | 0 |

---

### 3.3 - 100 sellers, 100 buyers
**Summary:**
* **Elapsed:** 432.04s
* **Total ops:** 8782 (7679 errors)
* **Throughput:** 20.3 ops/sec
* **Buyer Avg Response Time:** 787.97 ms
* **Seller Avg Response Time:** 1596.20 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer DELETE /cart/items/{id} | 719 | 790.0 | 629 |
| buyer GET /cart | 764 | 783.8 | 591 |
| buyer GET /categories | 683 | 785.7 | 615 |
| buyer GET /items/search | 706 | 774.2 | 644 |
| buyer GET /items/{id} | 725 | 769.6 | 613 |
| buyer GET /purchases | 689 | 774.5 | 648 |
| buyer GET /seller/{id}/rating | 732 | 774.7 | 619 |
| buyer POST /account/login | 100 | 1246.0 | 0 |
| buyer POST /account/logout | 0 | 0.0 | 100 |
| buyer POST /account/register | 100 | 606.5 | 0 |
| buyer POST /cart/clear | 652 | 800.7 | 624 |
| buyer POST /cart/items | 725 | 794.9 | 566 |
| buyer POST /cart/save | 701 | 792.0 | 632 |
| buyer POST /feedback | 685 | 788.1 | 627 |
| buyer POST /purchase | 744 | 789.9 | 628 |
| seller POST /account/login | 0 | 0.0 | 100 |
| seller POST /account/register | 57 | 1596.2 | 43 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| seller/s2_u56 | 1 | 2937.5 | 1 |
| seller/s2_u51 | 1 | 2932.9 | 1 |
| seller/s2_u57 | 1 | 2927.2 | 1 |
| seller/s2_u54 | 1 | 2920.0 | 1 |
| seller/s2_u38 | 1 | 2709.0 | 1 |

---

## 4. One seller failure (leader failure)

### 4.1 - 1 seller, 1 buyer
**Summary:**
* **Elapsed:** 150.25s
* **Total ops:** 2000 (0 errors)
* **Throughput:** 13.3 ops/sec
* **Buyer Avg Response Time:** 68.02 ms
* **Seller Avg Response Time:** 149.51 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer DELETE /cart/items/{id} | 86 | 79.8 | 0 |
| buyer GET /cart | 78 | 64.7 | 0 |
| buyer GET /categories | 82 | 67.5 | 0 |
| buyer GET /items/search | 88 | 79.1 | 0 |
| buyer GET /items/{id} | 81 | 55.9 | 0 |
| buyer GET /purchases | 86 | 50.0 | 0 |
| buyer GET /seller/{id}/rating | 70 | 52.1 | 0 |
| buyer POST /account/login | 1 | 60.5 | 0 |
| buyer POST /account/logout | 1 | 61.5 | 0 |
| buyer POST /account/register | 1 | 64.7 | 0 |
| buyer POST /cart/clear | 88 | 68.5 | 0 |
| buyer POST /cart/items | 72 | 73.2 | 0 |
| buyer POST /cart/save | 82 | 73.2 | 0 |
| buyer POST /feedback | 97 | 71.2 | 0 |
| buyer POST /purchase | 87 | 77.5 | 0 |
| seller GET /categories | 157 | 63.3 | 0 |
| seller GET /items | 173 | 75.7 | 0 |
| seller GET /seller/rating | 190 | 62.6 | 0 |
| seller POST /account/login | 1 | 320.8 | 0 |
| seller POST /account/logout | 1 | 236.3 | 0 |
| seller POST /account/register | 1 | 130.9 | 0 |
| seller POST /items | 169 | 251.3 | 0 |
| seller PUT /items/price | 153 | 238.5 | 0 |
| seller PUT /items/quantity | 155 | 225.4 | 0 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| seller/s0_u0 | 1000 | 149.5 | 0 |
| buyer/s0_u0 | 1000 | 68.0 | 0 |

---

### 4.2 - 10 sellers, 10 buyers
**Summary:**
* **Elapsed:** 398.53s
* **Total ops:** 19985 (15 errors)
* **Throughput:** 50.1 ops/sec
* **Buyer Avg Response Time:** 385.90 ms
* **Seller Avg Response Time:** 284.20 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer DELETE /cart/items/{id} | 844 | 526.9 | 0 |
| buyer GET /cart | 797 | 306.7 | 0 |
| buyer GET /categories | 872 | 296.5 | 0 |
| buyer GET /items/search | 773 | 248.3 | 0 |
| buyer GET /items/{id} | 843 | 291.7 | 0 |
| buyer GET /purchases | 820 | 287.3 | 0 |
| buyer GET /seller/{id}/rating | 828 | 280.8 | 0 |
| buyer POST /account/login | 10 | 143.8 | 0 |
| buyer POST /account/logout | 10 | 512.8 | 0 |
| buyer POST /account/register | 10 | 115.3 | 0 |
| buyer POST /cart/clear | 856 | 581.1 | 3 |
| buyer POST /cart/items | 859 | 549.3 | 4 |
| buyer POST /cart/save | 780 | 567.6 | 6 |
| buyer POST /feedback | 844 | 339.9 | 2 |
| buyer POST /purchase | 839 | 349.2 | 0 |
| seller GET /categories | 1632 | 179.0 | 0 |
| seller GET /items | 1675 | 188.8 | 0 |
| seller GET /seller/rating | 1724 | 183.5 | 0 |
| seller POST /account/login | 10 | 548.6 | 0 |
| seller POST /account/logout | 10 | 297.2 | 0 |
| seller POST /account/register | 10 | 407.4 | 0 |
| seller POST /items | 1625 | 391.2 | 0 |
| seller PUT /items/price | 1666 | 380.9 | 0 |
| seller PUT /items/quantity | 1648 | 385.0 | 0 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer/s1_u9 | 999 | 393.6 | 1 |
| buyer/s1_u6 | 999 | 392.5 | 1 |
| buyer/s1_u3 | 997 | 390.1 | 3 |
| buyer/s1_u2 | 999 | 389.1 | 1 |
| buyer/s1_u5 | 997 | 388.9 | 3 |

---

### 4.3 - 100 sellers, 100 buyers
**Summary:**
* **Elapsed:** 699.20s
* **Total ops:** 15044 (326 errors)
* **Throughput:** 21.5 ops/sec
* **Buyer Avg Response Time:** 677.52 ms
* **Seller Avg Response Time:** 1586.20 ms

| ENDPOINT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer DELETE /cart/items/{id} | 1231 | 929.0 | 2 |
| buyer GET /cart | 1236 | 583.5 | 3 |
| buyer GET /categories | 1270 | 571.1 | 1 |
| buyer GET /items/search | 1239 | 504.3 | 3 |
| buyer GET /items/{id} | 1220 | 575.6 | 3 |
| buyer GET /purchases | 1246 | 554.6 | 0 |
| buyer GET /seller/{id}/rating | 1243 | 569.5 | 1 |
| buyer POST /account/login | 15 | 1282.0 | 85 |
| buyer POST /account/logout | 15 | 810.1 | 0 |
| buyer POST /account/register | 99 | 1085.0 | 1 |
| buyer POST /cart/clear | 1198 | 846.5 | 28 |
| buyer POST /cart/items | 1205 | 859.8 | 27 |
| buyer POST /cart/save | 1203 | 859.5 | 32 |
| buyer POST /feedback | 1217 | 616.0 | 0 |
| buyer POST /purchase | 1343 | 640.8 | 4 |
| seller POST /account/login | 0 | 0.0 | 100 |
| seller POST /account/register | 64 | 1586.2 | 36 |

**TOP 5 SLOWEST CLIENTS (avg ms)**
| CLIENT | CALLS | AVG ms | ERR |
| :--- | :--- | :--- | :--- |
| buyer/s2_u91 | 1 | 2981.0 | 1 |
| seller/s2_u46 | 1 | 2966.9 | 1 |
| seller/s2_u70 | 1 | 2934.6 | 1 |
| seller/s2_u83 | 1 | 2925.2 | 1 |
| seller/s2_u98 | 1 | 2889.6 | 1 |

### Analysis

All testing was done on the google cloud deployment of the system. Overall, our rotating sequencer implementation works great for small to medium loads on the system, it does not scale well with larger loads. For the purposes of a timely evaluation, servers are set to time out sooner, this caused multiple benchmark failures when working with 100 buyers/sellers. There are some key observations to be made for certain scenarios: for all 3 scenarios in section 2 the buyers immediately time out because the sequencer cannot function without all servers available. Specifically in 2.3 sellers repeatedly time out because of the high load. 3.3 was cancelled early as the buyer queue was taking too long resulting in many time outs, sellers were already timing out by default due to the load. We can observe that as we add more buyers and sellers into the mix, contention increases significantly and throughput drops. Follower failure scenarios had a much higher amount of errors compared to leader failure scenarios. Leader failure scenarios also maintain higher throughput than follower failure scenarios. There is an outlier in 3.2's buyer response time being much lower than in other scenarios. This can be explained by failures returning errors quickly in this case but it is no indication of higher performance. There are multiple examples in the results where under the smaller loads, buyers have better latency than the sellers but under high loads this situation is reversed, showing that the more complicated operations of buyers take a bigger performance hit frmo high contention than the sellers' operations.
