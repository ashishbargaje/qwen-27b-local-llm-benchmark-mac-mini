# 27B Local LLM on a 24GB Mac mini M4

## Overview

This repository documents a practical local-LLM experiment:

> **Can a 27B parameter model run on a 24GB Mac mini M4 with a large context window and usable inference speed?**

The goal was not simply to make the model load. The experiment focused on the trade-off between:

- model size
- aggressive quantization
- context length
- KV-cache memory
- inference speed
- memory pressure
- practical QA and image-understanding workloads

The final configuration reached a useful balance for this hardware:

```text
Hardware           : Mac mini M4
Unified Memory     : 24 GB
Model              : 27B
Model Quantization : IQ2_XS (2-bit)
Context            : 64K
KV Cache           : Q8_0
KV Cache Size      : ~2.125 GB
Runtime            : Ollama
```

---

## 1. Why This Experiment?

A 27B model is large for a 24GB consumer machine.

The question was therefore not:

> "Can I launch it once?"

The more useful engineering question was:

> **"Can I keep a 27B model usable under real workload conditions without giving up too much speed or context?"**

That led to a series of memory and workload experiments rather than a single benchmark.

---

## 2. Memory Story: From Baseline to Final Configuration

### 2.1 Baseline — Before the Test

Before loading the workload, the Mac was using approximately:

| Metric | Baseline |
|---|---:|
| Physical Memory | 24.00 GB |
| Memory Used | 8.66 GB |
| App Memory | 5.86 GB |
| Wired Memory | 1.27 GB |
| Compressed | 806 MB |
| Cached Files | 10.03 GB |
| Swap Used | 0 bytes |

The system therefore had a relatively large amount of available memory before the LLM workload started.

---

### 2.2 During Inference — Memory Jumps

Once the 27B workload was running, the memory footprint changed substantially.

One observed state showed:

| Metric | Observed |
|---|---:|
| `llama-server` | 14.06 GB |
| Physical Memory | 24.00 GB |
| Memory Used | 20.16 GB |
| App Memory | 2.21 GB |
| Wired Memory | 14.60 GB |
| Compressed | 2.79 GB |
| Cached Files | 3.79 GB |
| Swap Used | 0 bytes |

A later high-memory state showed:

| Metric | Observed |
|---|---:|
| `llama-server` | 14.30 GB |
| Physical Memory | 24.00 GB |
| Memory Used | 21.83 GB |
| App Memory | 2.65 GB |
| Wired Memory | 14.79 GB |
| Compressed | 3.75 GB |
| Cached Files | 1.80 GB |
| Swap Used | 0 bytes |

The important observation was that the **LLM server itself was around 14 GB** during the run, while total system memory consumption rose above 20 GB.

At the same time, **swap remained at 0 bytes** in the captured states.

That made memory efficiency a key part of the experiment.

---

## 3. The KV-Cache Optimization

The most useful optimization came from changing the KV-cache precision.

### F16 KV Cache vs Q8_0 KV Cache

| Metric | F16 KV | Q8_0 KV |
|---|---:|---:|
| Prompt tokens | — | 1,124 |
| Generated tokens | 30,169 | 28,250 |
| Generation speed | **6.68 tok/s** | **6.67 tok/s** |
| KV cache | **4.0 GB** | **2.125 GB** |

### What changed?

KV-cache usage dropped from:

```text
4.0 GB
    ↓
2.125 GB
```

That is a saving of approximately:

```text
1.875 GB
≈ 46.9%
```

At the same time, measured generation speed was effectively unchanged:

```text
6.68 tok/s
vs
6.67 tok/s
```

This was the key reason for choosing **Q8_0 KV cache** for the final configuration.

---

## 4. Why Keep 64K Context?

A smaller context could reduce memory pressure further, but the experiment was specifically interested in long-context workloads.

The final setup therefore retained:

```text
Context = 64K
```

The goal was to reduce memory where it had a relatively low performance impact rather than simply shrinking the context window.

---

## 5. Final Configuration

The configuration that emerged from the experiments was:

```text
Mac mini M4
24 GB Unified Memory

27B model
IQ2_XS model quantization
64K context
Q8_0 KV cache
~2.125 GB KV cache
Ollama runtime
```

The practical rationale is:

- **2-bit model quantization** makes the 27B model viable on 24GB hardware.
- **64K context** preserves the long-context capability being tested.
- **Q8_0 KV cache** cuts KV memory substantially compared with F16.
- The observed generation speed remained around **6.7 tok/s** for the long QA workload.

---

## 6. Test 1 — Complex QA Strategy Workload

The first major workload was a long-form, complex QA strategy task.

### Measured result

```text
Prompt tokens       : 1,124
Generated tokens    : 28,250
Evaluation duration : 4,238.26 seconds
Tokens / second     : 6.67
```

The model produced approximately **28K generated tokens** from the workload.

This test is useful because it exercises much more than a short chat response: long-form reasoning, sustained generation, and a large output context.

The complete prompt and generated output are preserved in the repository.

---

## 7. Test 2 — Image Understanding

The second workload evaluated image understanding using a composite containing **10 deliberately varied chart cases**.

The test included cases such as:

- clean charts
- smaller fonts
- overlapping legends
- dense numerical values
- decimal values
- negative values
- visually similar colours
- rotated labels
- crossing series
- low-resolution / noisy rendering

### Measured result

```text
Prompt tokens       : 3,220
Generated tokens    : 5,540
Evaluation duration : 779.63 seconds
Tokens / second     : 7.11
```

The generated analysis described the charts individually and captured values, legends, labels and the intentionally difficult visual conditions present in the test set.

The composite image used for the test is included in the repository.

---

## 8. Post-Test Memory Recovery

After the workload completed and the LLM process was no longer occupying the same memory footprint, the captured state showed:

| Metric | After Test |
|---|---:|
| Physical Memory | 24.00 GB |
| Memory Used | 7.58 GB |
| App Memory | 3.30 GB |
| Wired Memory | 1.59 GB |
| Compressed | 2.03 GB |
| Cached Files | 2.22 GB |
| Swap Used | 0 bytes |

This is useful because it shows that the large memory footprint was associated with the running LLM workload rather than becoming a persistent memory allocation after the test.

---

## 9. What We Learned

### 1. Model size alone is not the whole story

A 27B model can be made viable on a 24GB system by combining aggressive model quantization with careful runtime configuration.

### 2. KV cache can be a meaningful memory lever

The move from F16 KV to Q8_0 reduced the measured KV footprint by almost half:

```text
4.0 GB → 2.125 GB
```

without a meaningful change in measured generation speed for the QA test.

### 3. Long context is expensive

Keeping a 64K context while running a 27B model puts significant pressure on a 24GB machine. This makes every memory decision matter.

### 4. "It fits" is not the same as "it is usable"

The interesting target is not simply loading the model. The target is a configuration that still works under a realistic workload with acceptable speed and memory behaviour.

---

## 10. Reproducibility

The repository keeps the important experimental artefacts together:

- test code
- prompts
- raw logs
- generated output
- screenshots
- configuration notes

For an apples-to-apples comparison, keep the following constant:

```text
Model version
Quantization
Context length
KV cache type
Prompt
Hardware
Runtime
```

Small runtime changes can affect memory and throughput.

---

## 11. Scope and Limitations

This is a **practical experiment**, not a formal benchmark suite.

The reported numbers are observations from this specific:

- Mac mini M4
- 24GB unified-memory configuration
- 27B model
- IQ2_XS model quantization
- 64K context
- Q8_0 KV cache
- Ollama runtime
- test workloads

Results can vary with model version, prompt structure, runtime settings, background applications and other system conditions.

---

## Conclusion

The experiment reached a practical local-inference configuration:

> **27B @ 2-bit + 64K context + Q8_0 KV cache on a 24GB Mac mini M4**

The main lesson is not that a 27B model can fit on a 24GB machine.

The more interesting lesson is that **careful memory engineering can move the boundary between "too large to run" and "practical enough to experiment with."**

That is particularly interesting for local AI-assisted software engineering, QA and agentic workflows where privacy, control and predictable local execution matter.
