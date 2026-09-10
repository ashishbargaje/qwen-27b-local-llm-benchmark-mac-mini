# Qwen3.8-27B on a 24GB Mac mini M4

## Overview

This repository documents a practical local-LLM engineering experiment:

> **Can a 27B parameter model run on a 24GB Mac mini M4 with a large context window and usable inference speed?**

The goal was not simply to make the model load.

The experiment focused on the trade-offs between:

- model size
- aggressive quantization
- context length
- KV-cache memory
- inference speed
- memory pressure
- practical QA workloads
- image-understanding workloads
- speculative decoding / MTP

The investigation evolved from a **Q8_0 KV-cache baseline** to a **Q4_0 KV-cache optimization** in order to improve memory headroom on a constrained 24GB unified-memory system.

---

## 1. Why This Experiment?

A 27B model is large for a 24GB consumer machine.

The question was therefore not:

> "Can I launch it once?"

The more useful engineering question was:

> **"Can I keep a 27B model usable under realistic workload conditions without giving up too much speed or context?"**

That led to a series of memory, runtime and workload experiments rather than a single benchmark.

---

## 2. Experimental Configuration

### Hardware

```text
Hardware           : Mac mini M4
Unified Memory     : 24 GB
Runtime            : Ollama
```

### Model

```text
Model              : Qwen3.8-27B
Model Quantization : IQ2_XS (2-bit)
Context            : 64K
```

### Configuration Evolution

The experiment was evaluated in stages.

### Baseline

```text
27B
IQ2_XS model quantization
64K context
Q8_0 KV cache
```

Observed:

```text
Loaded runtime size : ~11 GB
Generation speed    : 6.67 tok/s
```

### Optimization

The KV-cache precision was then changed from Q8_0 to Q4_0.

```text
27B
IQ2_XS model quantization
64K context
Q4_0 KV cache
```

Observed:

```text
Loaded runtime size : ~10 GB
Generation speed    : 6.57 tok/s
```

This reduced the loaded runtime footprint by approximately **1 GB**, with a measured throughput difference of approximately **1.5%**.

---

## 3. Memory Story

### 3.1 Baseline — Before the Workload

Before loading the LLM workload, the Mac was using approximately:

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

### 3.2 During Inference

Once the 27B workload was running, memory usage increased substantially.

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

The important observation was that the LLM workload pushed total system memory usage above 20 GB while the captured states still showed:

```text
Swap Used = 0 bytes
```

This made memory efficiency an important part of the experiment.

---

## 4. KV-Cache Optimization

One of the most useful optimization areas was KV-cache precision.

### F16 KV Cache vs Q8_0 KV Cache

| Metric | F16 KV | Q8_0 KV |
|---|---:|---:|
| Prompt tokens | — | 1,124 |
| Generated tokens | 30,169 | 28,250 |
| Generation speed | **6.68 tok/s** | **6.67 tok/s** |
| KV cache | **4.0 GB** | **2.125 GB** |

The measured KV-cache footprint changed from:

```text
4.0 GB
   ↓
2.125 GB
```

This is a saving of approximately:

```text
1.875 GB
≈ 46.9%
```

Measured generation speed remained effectively unchanged:

```text
6.68 tok/s
vs
6.67 tok/s
```

This showed that Q8_0 KV cache could significantly reduce memory usage compared with F16 without a meaningful throughput penalty in the tested workload.

---

## 5. Q8_0 vs Q4_0 KV Cache

The next optimization step was to evaluate whether the KV cache could be reduced further.

| Metric | Q8_0 KV | Q4_0 KV |
|---|---:|---:|
| Model | Qwen3.8-27B IQ2_XS | Qwen3.8-27B IQ2_XS |
| Context | 64K | 64K |
| Loaded Runtime Size | ~11 GB | **~10 GB** |
| Generation Speed | **6.67 tok/s** | 6.57 tok/s |
| Memory | Higher | **~1 GB lower** |
| QA Output Quality | Slightly better | Very close |

Measured throughput difference:

```text
6.67 tok/s
vs
6.57 tok/s

≈ 1.5% difference
```

### Engineering Decision

For a 24GB Mac mini, **Q4_0 KV cache is the more practical configuration when additional memory headroom is more valuable than a small throughput difference**.

The observed trade-off was approximately:

```text
~1 GB memory saved
        +
~1.5% lower measured throughput
```

The QA outputs from Q4_0 were very close to Q8_0 in the tested workload, with no major degradation observed.

---

## 6. Long-Context Strategy

The experiment was specifically interested in long-context workloads.

The configuration therefore retained:

```text
Context = 64K
```

The objective was to reduce memory usage through runtime optimization rather than simply reducing the context window.

This is relevant to workloads such as:

- large test specifications
- architecture documents
- logs
- requirements
- source-code analysis
- multi-file QA workflows

---

## 7. Test 1 — Complex QA Strategy Workload

The main workload was a long-form QA strategy task.

### Q8_0 KV Result

```text
Prompt tokens       : 1,124
Generated tokens    : 28,250
Evaluation duration : 4,238.26 seconds
Tokens / second     : 6.67
```

### Q4_0 KV Result

```text
Prompt tokens       : 4,295
Generated tokens    : 24,948
Evaluation duration : 3,797.16 seconds
Tokens / second     : 6.57
```

The workload exercised areas such as:

- distributed-system failure scenarios
- Kafka duplicate and out-of-order events
- retry and idempotency behaviour
- race conditions
- DB / Kafka / ERP consistency
- consumer crash and replay scenarios
- reconciliation
- security
- performance considerations

The complete prompts and generated outputs are preserved in the repository.

### Important Benchmark Note

The Q8_0 and Q4_0 runs did not generate exactly the same number of tokens and did not use identical prompt-token counts.

Therefore, the results should be interpreted primarily as **engineering observations of memory and sustained throughput**, rather than as a perfectly controlled apples-to-apples benchmark.

---

## 8. Test 2 — Image Understanding

The second workload evaluated image understanding using a composite containing **10 deliberately varied chart cases**.

The test included:

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

### Measured Result

```text
Prompt tokens       : 3,220
Generated tokens    : 5,540
Evaluation duration : 779.63 seconds
Tokens / second     : 7.11
```

The generated analysis described the charts individually and captured values, legends, labels and the intentionally difficult visual conditions present in the test set.

The composite image used for the test is included in the repository.

---

## 9. Speculative Decoding / MTP Experiment

I also experimented with **MTP (Multi-Token Prediction) / speculative decoding** as a possible inference-speed optimization.

The configuration was **not stable in my Apple Silicon environment and resulted in a crash**.

Therefore:

- no speedup is claimed
- no performance improvement is included in the benchmark results
- the experiment is retained as a negative result

This is an important part of the engineering investigation: not every optimization produced a usable result.

---

## 10. Post-Test Memory Recovery

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

This indicates that the high-memory footprint was associated with the running LLM workload rather than becoming a persistent allocation after the test.

---

## 11. Engineering Findings

### 1. Model quantization is critical

A 27B model can be made viable on a 24GB unified-memory system by combining aggressive model quantization with careful runtime configuration.

### 2. KV cache is an important memory lever

Changing KV-cache precision produced a meaningful reduction in memory usage.

The F16 → Q8_0 experiment reduced the measured KV footprint from:

```text
4.0 GB → 2.125 GB
```

with almost no measured throughput change in that workload.

### 3. Q4_0 provides additional memory headroom

The Q8_0 → Q4_0 experiment reduced the loaded runtime size by approximately:

```text
~11 GB → ~10 GB
```

while measured throughput changed from:

```text
6.67 tok/s → 6.57 tok/s
```

This makes Q4_0 attractive for a 24GB system where memory headroom matters.

### 4. Long context is expensive

Running a 27B model with a large context window puts significant pressure on a 24GB unified-memory system.

Every memory decision therefore becomes important.

### 5. "It fits" is not the same as "it is usable"

The interesting engineering target is not simply loading the model.

The target is a configuration that continues to work under realistic workloads with acceptable:

- memory pressure
- inference speed
- context capacity
- output quality

### 6. Failed optimizations are still useful results

The MTP experiment did not produce a usable result on the tested Apple Silicon setup.

Documenting that failure avoids making an unsupported performance claim and helps identify areas for future investigation.

---

## 12. Current Practical Configuration

Based on the experiments performed so far, the current practical configuration for this 24GB system is:

```text
Hardware           : Mac mini M4
Unified Memory     : 24 GB

Model              : Qwen3.8-27B
Model Quantization : IQ2_XS (2-bit)

Context            : 64K
KV Cache           : Q4_0

Runtime            : Ollama
```

The practical rationale is:

- **IQ2_XS** makes the 27B model viable within the hardware constraint.
- **64K context** preserves the long-context capability being evaluated.
- **Q4_0 KV cache** provides additional memory headroom.
- The measured throughput remained around **6.6 tok/s** in the long QA experiments.
- QA output quality remained very close to Q8_0 in the tested scenarios.

Q8_0 remains a useful alternative when the priority is maximum KV-cache precision rather than additional memory headroom.

---

## 13. Reproducibility

The repository keeps the important experimental artefacts together:

- test code
- prompts
- raw logs
- generated output
- screenshots
- configuration notes
- comparison results

### Environment Setup

For the Q4_0 configuration used in the latest experiment:

```bash
launchctl setenv OLLAMA_KV_CACHE_TYPE q4_0
launchctl setenv OLLAMA_FLASH_ATTENTION 1
launchctl setenv OLLAMA_CONTEXT_LENGTH 65536
```

Verify:

```bash
launchctl getenv OLLAMA_KV_CACHE_TYPE
launchctl getenv OLLAMA_FLASH_ATTENTION
launchctl getenv OLLAMA_CONTEXT_LENGTH
```

Expected:

```text
q4_0
1
65536
```

Run the model:

```bash
ollama run hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS
```

Check the loaded model:

```bash
ollama ps
```

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

## 14. Repository Structure

The repository contains the experimental code, prompts, outputs, logs and supporting evidence used during the investigation.

The goal is to keep both the **implementation** and the **observed evidence** reproducible.

---

## 15. Scope and Limitations

This is a **practical engineering experiment**, not a formal benchmark suite.

The reported numbers are observations from this specific environment:

- Mac mini M4
- 24GB unified memory
- Qwen3.8-27B
- IQ2_XS model quantization
- 64K context
- Ollama runtime
- tested KV-cache configurations
- specific QA and vision workloads

Results can vary with:

- model version
- prompt structure
- output length
- runtime settings
- background applications
- operating-system state
- hardware configuration

The Q8_0 and Q4_0 QA runs also used different prompt-token and generated-token counts, so their total evaluation durations should not be treated as directly comparable.

---

## Conclusion

This experiment demonstrates that a **27B local LLM can be pushed into a practical operating range on a 24GB Apple Silicon system** through careful memory and runtime engineering.

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
     ↓
MTP experiment
     ↓
Unstable on Apple Silicon
```

The main lesson is not simply that a 27B model can fit on a 24GB machine.

The more interesting lesson is:

> **Careful memory engineering, workload testing and evidence-based trade-offs can move the boundary between "too large to run" and "practical enough to use."**

This is particularly relevant to local AI-assisted software engineering, QA and agentic workflows where privacy, control and predictable local execution matter.
