# Model Comparison — Extraction Quality Benchmark

Compared 3 model(s) on the same dataset (20 documents) so accuracy differences reflect the model, not the data.

## Overall

| Model | Backend | Field Acc | Fuzzy Acc | Avg Latency | Total Cost |
|---|---|---|---|---|---|
| **qwen3-vl-32b-lmstudio** | lmstudio (qwen3-vl-32b-instruct) | 52.4% | 52.4% | 28.7s | $0.0000 |
| **qwen2.5-vl-3b** | local (mlx-community/Qwen2.5-VL-3B-Instruct-4bit) | 49.6% | 50.0% | 2.8s | $0.0000 |
| **gemma-4b** | local (mlx-community/gemma-3-4b-it-4bit) | 38.4% | 39.2% | 5.2s | $0.0000 |

## By Category

### govt_form

| Model | Field Acc | Fuzzy Acc | Avg Latency |
|---|---|---|---|
| qwen3-vl-32b-lmstudio | 91.7% | 91.7% | 28.3s |
| qwen2.5-vl-3b | 88.3% | 90.0% | 3.0s |
| gemma-4b | 85.0% | 85.0% | 3.2s |

### id_doc

| Model | Field Acc | Fuzzy Acc | Avg Latency |
|---|---|---|---|
| qwen2.5-vl-3b | 45.0% | 45.0% | 1.5s |
| qwen3-vl-32b-lmstudio | 45.0% | 45.0% | 16.8s |
| gemma-4b | 5.0% | 7.5% | 9.5s |

### invoice

| Model | Field Acc | Fuzzy Acc | Avg Latency |
|---|---|---|---|
| qwen3-vl-32b-lmstudio | 52.7% | 52.7% | 29.6s |
| qwen2.5-vl-3b | 49.1% | 49.1% | 3.1s |
| gemma-4b | 43.6% | 44.4% | 3.1s |

### ledger

| Model | Field Acc | Fuzzy Acc | Avg Latency |
|---|---|---|---|
| gemma-4b | 20.0% | 20.0% | 5.1s |
| qwen3-vl-32b-lmstudio | 20.0% | 20.0% | 40.0s |
| qwen2.5-vl-3b | 16.0% | 16.0% | 3.4s |
