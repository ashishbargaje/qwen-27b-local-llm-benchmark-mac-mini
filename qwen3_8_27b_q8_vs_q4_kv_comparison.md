# Qwen3.8-27B: Q8_0 vs Q4_0 KV Cache

## Test setup

- Model: Qwen3.8-27B `IQ2_XS`
- Context: 64K
- GPU: 100%
- Workload: Same QA scenario, but token counts were not identical between runs

| Metric | Q8_0 KV | Q4_0 KV |
|---|---:|---:|
| Loaded size | 11 GB | **10 GB** |
| Generated tokens | 28,250 | 24,948 |
| Evaluation time | 4,238.26 s | **3,797.16 s** |
| Tokens/sec. | **6.67** | 6.57 |
| Memory | Higher | **~1 GB less** |
| Output quality | Slightly better | Very close to Q8_0 |

## Result

**Q4_0 is the better practical choice for this 24 GB Mac setup.**

It saves about **1 GB memory** while giving almost the same generation speed and very similar QA output quality.

The measured throughput difference is approximately **1.5%**.

> Throughput should be interpreted as an observed engineering comparison, not a perfectly controlled apples-to-apples benchmark, because the two runs did not use identical prompt-token and generated-token counts.

Q8_0 is still a good choice when maximum quality is the priority.
