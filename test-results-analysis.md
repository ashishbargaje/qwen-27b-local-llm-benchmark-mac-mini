# Test Results Analysis

## Executive Summary

This experiment evaluated a **27B parameter LLM on a Mac mini M4 with 24GB unified memory** using:

```text
Model quantization : IQ2_XS (2-bit)
Context            : 64K
KV cache           : Q8_0
KV cache size      : ~2.125 GB
Runtime            : Ollama
```

Two practical workloads were tested:

1. Complex QA strategy generation
2. Image understanding across 10 deliberately difficult chart examples

The final configuration achieved approximately **6.67 tok/s on the QA workload** and **7.11 tok/s on the image workload**.

The most important optimization was the KV-cache change from **F16 to Q8_0**, reducing the observed KV footprint from **4.0 GB to 2.125 GB** while keeping measured QA generation speed essentially unchanged.

---

## 1. Memory Analysis

### Baseline

Before the workload:

- Physical memory: **24.00 GB**
- Memory used: **8.66 GB**
- App memory: **5.86 GB**
- Wired memory: **1.27 GB**
- Cached files: **10.03 GB**
- Swap: **0 bytes**

This provides the reference point for the subsequent memory growth.

### During the workload

Two observed high-memory states were captured.

#### State A

- `llama-server`: **14.06 GB**
- Memory used: **20.16 GB**
- Wired memory: **14.60 GB**
- Compressed memory: **2.79 GB**
- Cached files: **3.79 GB**
- Swap: **0 bytes**

#### State B — Higher observed memory state

- `llama-server`: **14.30 GB**
- Memory used: **21.83 GB**
- Wired memory: **14.79 GB**
- Compressed memory: **3.75 GB**
- Cached files: **1.80 GB**
- Swap: **0 bytes**

### Interpretation

The key practical observation is that the **llama-server process alone was around 14.0–14.3 GB**, while total memory consumption rose to approximately **20–21.8 GB**.

The system also showed increasing memory pressure during the workload, but the captured states still showed **0 bytes of swap**.

This indicates that the workload was placing substantial pressure on a 24GB machine, making memory configuration important.

---

## 2. KV Cache Optimization

The strongest quantitative optimization came from KV-cache precision.

| Metric | F16 KV | Q8_0 KV |
|---|---:|---:|
| Generated tokens | 30,169 | 28,250 |
| Generation speed | 6.68 tok/s | 6.67 tok/s |
| KV cache | 4.0 GB | 2.125 GB |

### Memory saving

```text
4.0 - 2.125 = 1.875 GB
```

Relative saving:

```text
1.875 / 4.0 × 100 ≈ 46.9%
```

### Speed impact

Measured generation speed changed from:

```text
6.68 tok/s → 6.67 tok/s
```

That is a difference of only about:

```text
0.01 tok/s
≈ 0.15%
```

For this particular workload, that is effectively negligible.

### Decision

This makes **Q8_0 KV** a strong practical choice for this 24GB system:

> nearly half the KV memory with essentially the same measured generation speed in the QA run.

---

## 3. Test 1 — Complex QA Strategy

### Raw benchmark

```text
Prompt tokens       : 1,124
Generated tokens    : 28,250
Evaluation duration : 4,238.26 seconds
Tokens / second     : 6.67
```

Approximate wall-clock generation time:

```text
4,238.26 sec
≈ 70.6 minutes
```

### What this test demonstrates

This was a sustained long-form generation workload rather than a short chat interaction.

The useful signals are:

- the model remained operational for a very long generation
- roughly **28K output tokens** were produced
- generation speed stayed around **6.67 tok/s**
- the 64K context configuration remained in use
- the system remained in the observed no-swap states

For QA architecture experiments, this is more representative of sustained reasoning workloads than a short 100-token benchmark.

---

## 4. Test 2 — Image Understanding

### Raw benchmark

```text
Prompt tokens       : 3,220
Generated tokens    : 5,540
Evaluation duration : 779.63 seconds
Tokens / second     : 7.11
```

Approximate generation time:

```text
779.63 sec
≈ 13.0 minutes
```

### Test composition

The image workload contained 10 charts designed to stress different visual-reading conditions:

1. Clean chart
2. Smaller fonts
3. Overlapping legend
4. Dense numerical values
5. Decimal values
6. Negative values
7. Similar colours
8. Rotated labels
9. Multiple series crossing
10. Low-resolution / noisy rendering

### Observed model behaviour

The generated analysis reported:

- chart titles
- axis labels
- series names
- individual values
- legends
- the intentional visual quirks in the test set

This is especially useful because the test was not limited to a clean, single chart. It intentionally included cases that tend to challenge visual parsing.

---

## 5. Before / Peak / After Memory Story

The memory snapshots create a useful progression.

```text
BEFORE
8.66 GB memory used
        ↓
MODEL LOAD / INFERENCE
20.16 GB observed
        ↓
HIGHER OBSERVED STATE
21.83 GB observed
        ↓
TEST COMPLETE
7.58 GB memory used
```

The `llama-server` process reached approximately:

```text
14.06–14.30 GB
```

during the observed workload states.

After the workload, the captured memory footprint returned to roughly:

```text
7.58 GB used
```

with:

```text
Swap Used = 0 bytes
```

This supports the conclusion that the large memory footprint was tied to the active inference workload.

---

## 6. Why the Final Configuration Makes Sense

### IQ2_XS for the model

The 27B model needs aggressive model quantization to make a 24GB machine practical.

### 64K context

The experiment intentionally retained a large context window because long-context behaviour was part of the objective.

### Q8_0 KV

This was the key memory optimisation:

```text
F16 KV  = 4.0 GB
Q8_0 KV = 2.125 GB
```

The speed result did not materially change in the measured QA run.

### Overall balance

The final configuration therefore prioritises:

```text
Large model
+ Long context
+ Lower KV footprint
+ Usable local speed
```

rather than maximising any single metric.

---

## 7. Engineering Takeaways

### Takeaway 1 — Memory is a first-class tuning dimension

On a 24GB unified-memory machine, model memory and KV-cache memory can dominate the practical experience.

### Takeaway 2 — The best configuration is not always the default

A default memory setup may spend memory on precision that does not materially improve the target workload.

### Takeaway 3 — Measure the whole system

Looking only at model size is not enough.

The experiment also tracked:

- `llama-server`
- total memory used
- wired memory
- compressed memory
- cached files
- swap
- KV-cache footprint

### Takeaway 4 — QA workloads need workload-specific benchmarking

A short prompt benchmark can look great while a long-running architecture or test-strategy workload behaves very differently.

---

## 8. What This Means for QA Architecture

From a QA Architect perspective, the interesting question is not:

> "Can the model answer a few questions?"

It is:

> **"Can a local model sustain the kind of reasoning, context and artefact processing that a QA engineering workflow actually needs?"**

This experiment is an early step toward evaluating local models for:

- test strategy drafting
- test scenario generation
- requirements analysis
- risk analysis
- defect triage support
- test-data reasoning
- visual artefact analysis
- documentation assistance
- future agentic QA workflows

The next step is to move from isolated capability tests toward repeatable evaluation suites with explicit quality scoring.

---

## 9. Limitations

These numbers should be treated as practical observations, not universal benchmarks.

Results can change with:

- model version
- runtime version
- background applications
- prompt structure
- output length
- context usage
- KV configuration
- system state

Most importantly, **throughput alone does not establish output quality**.

A future benchmark should score the generated answer for correctness, completeness, hallucination rate, reasoning quality and task success in addition to tokens/sec.

---

## Final Result

For the tested workloads, the configuration:

```text
27B
IQ2_XS
64K context
Q8_0 KV
24GB M4
```

proved that a large local model can be pushed into a practically interesting operating range on consumer hardware.

The most compelling result is the KV-cache optimisation:

> **~46.9% less KV memory with essentially unchanged measured QA generation speed.**

That is the core engineering result of this experiment.
