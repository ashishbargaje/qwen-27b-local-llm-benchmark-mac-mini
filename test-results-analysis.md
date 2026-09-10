# Test Results Analysis

## Executive Summary

This experiment evaluated a **27B parameter LLM on a Mac mini M4 with 24GB unified memory** using:

```text
Model quantization : IQ2_XS (2-bit)
Context            : 64K
Primary KV cache   : Q8_0
Latest KV cache    : Q4_0
Runtime             : Ollama
```

Two practical workloads were tested:

1. Complex QA strategy generation
2. Image understanding across 10 deliberately difficult chart examples

The baseline Q8_0 configuration achieved approximately **6.67 tok/s on the QA workload** and **7.11 tok/s on the image workload**.

The key optimization path was:

```text
F16 KV
   ↓
Q8_0 KV
   ↓
Q4_0 KV
```

The F16 → Q8_0 change reduced the observed KV footprint from **4.0 GB to 2.125 GB** while keeping measured QA generation speed essentially unchanged.

The later Q8_0 → Q4_0 experiment reduced the loaded runtime size by approximately **1 GB**, with measured throughput changing from **6.67 tok/s to 6.57 tok/s**.

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

That is a difference of about:

```text
0.01 tok/s
≈ 0.15%
```

For this particular workload, that observed difference was effectively negligible.

### Baseline Decision

This made **Q8_0 KV** a strong baseline for the 24GB system:

> Nearly half the KV memory with essentially the same measured generation speed in the QA run.

---

## 3. Q8_0 → Q4_0 KV Optimization

The next optimization step evaluated whether the KV cache could be reduced further.

| Metric | Q8_0 KV | Q4_0 KV |
|---|---:|---:|
| Context | 64K | 64K |
| Loaded runtime size | ~11 GB | **~10 GB** |
| Generated tokens | 28,250 | 24,948 |
| Evaluation time | 4,238.26 s | 3,797.16 s |
| Tokens/sec. | **6.67** | 6.57 |
| Memory | Higher | **~1 GB less** |
| Output quality | Slightly better | Very close |

The measured throughput difference is approximately:

```text
6.67 tok/s → 6.57 tok/s
≈ 1.5%
```

The two runs did not use identical prompt-token and generated-token counts, so this should be treated as an **observed engineering comparison**, not a perfectly controlled benchmark.

### Latest Practical Decision

For this 24GB Mac setup, **Q4_0 KV is the more practical configuration when additional memory headroom is more valuable than a small throughput difference**.

---

## 4. Test 1 — Complex QA Strategy

### Q8_0 baseline

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

### Q4_0 optimization run

```text
Prompt tokens       : 4,295
Generated tokens    : 24,948
Evaluation duration : 3,797.16 seconds
Tokens / second     : 6.57
```

This was a sustained long-form generation workload rather than a short chat interaction.

The useful signals are:

- the model remained operational for a very long generation
- thousands of output tokens were produced
- generation speed stayed around the measured range above
- the 64K context configuration remained in use
- the system remained in the observed no-swap states

For QA architecture experiments, this is more representative of sustained reasoning workloads than a short 100-token benchmark.

---

## 5. Test 2 — Image Understanding

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

This is useful because the test was not limited to a clean, single chart. It intentionally included cases that can challenge visual parsing.

---

## 6. Before / Peak / After Memory Story

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

## 7. Why the Current Configuration Makes Sense

### IQ2_XS for the model

The 27B model needs aggressive model quantization to make a 24GB machine practical.

### 64K context

The experiment intentionally retained a large context window because long-context behaviour was part of the objective.

### Q8_0 as baseline

Q8_0 significantly reduced KV memory compared with F16 with essentially unchanged measured QA generation speed in the original comparison.

### Q4_0 as the latest optimization

Q4_0 reduced the loaded runtime size by approximately **1 GB** versus Q8_0, with approximately **1.5% lower measured throughput** in the observed comparison.

### Overall balance

The current practical target therefore prioritises:

```text
Large model
+ Long context
+ Lower KV footprint
+ Usable local speed
```

rather than maximising any single metric.

---

## 8. Engineering Takeaways

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

### Takeaway 5 — Optimizations should be evaluated as trade-offs

Q8_0 and Q4_0 show that reducing memory can be worthwhile even when it introduces a small throughput trade-off.

---

## 9. What This Means for QA Architecture

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

## 10. Limitations

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

The Q8_0 and Q4_0 runs also used different prompt-token and generated-token counts, so their total evaluation durations should not be treated as directly comparable.

A future benchmark should score generated answers for correctness, completeness, hallucination rate, reasoning quality and task success in addition to tokens/sec.

---

## 11. Latest Practical Configuration

For the tested 24GB system, the latest practical configuration is:

```text
Hardware           : Mac mini M4
Unified Memory     : 24 GB

Model              : Qwen3.8-27B
Model Quantization : IQ2_XS (2-bit)

Context            : 64K
KV Cache           : Q4_0

Runtime            : Ollama
```

Q8_0 remains a useful baseline and alternative when the priority is maximum KV-cache precision rather than additional memory headroom.

---

## 12. Reproducibility

The repository keeps the important experimental artefacts together:

- test code
- prompts
- raw logs
- generated output
- screenshots
- configuration notes
- comparison results

For an apples-to-apples comparison, keep the following constant:

```text
Model version
Model quantization
Context length
KV cache type
Prompt
Hardware
Runtime
```

Small runtime changes can affect memory and throughput.

---

## Final Result

The experiment demonstrates that a **27B local LLM can be pushed into a practically interesting operating range on a 24GB Apple Silicon system** through careful memory and runtime engineering.

The progression was:

```text
27B IQ2_XS
     ↓
64K context
     ↓
Q8_0 KV baseline
     ↓
Q4_0 KV optimization
     ↓
~1 GB lower loaded runtime size
with ~1.5% measured throughput trade-off
```

The core engineering result is:

> **Q4_0 provided additional memory headroom on the 24GB system while retaining similar measured QA throughput and very close observed output quality.**

The broader lesson is:

> **Careful memory engineering, workload testing and evidence-based trade-offs can move the boundary between "too large to run" and "practical enough to use."**

This is particularly relevant to local AI-assisted software engineering, QA and agentic workflows where privacy, control and predictable local execution matter.
