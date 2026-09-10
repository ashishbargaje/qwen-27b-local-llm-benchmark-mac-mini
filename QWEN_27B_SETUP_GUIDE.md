# Qwen3.8-27B — 2-bit Model + Q4/Q8 KV Cache + 65K Context

## What we are configuring

- **Model:** `hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS`
- **Model quantization:** `IQ2_XS` (2-bit model quantization)
- **KV cache:** `q8_0` or `q4_0`
- **Flash Attention:** enabled
- **Context:** `65536` (65K)

> **Important:** `IQ2_XS` is the 2-bit model quantization. `q8_0` / `q4_0` is a separate KV-cache setting.

---

## Steps

### 1. Stop the currently loaded model

```bash
ollama stop hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS
```

Check:

```bash
ollama ps
```

It should be empty.

---

### 2. Choose the KV cache

For **Q8_0**:

```bash
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
```

For **Q4_0**:

```bash
launchctl setenv OLLAMA_KV_CACHE_TYPE q4_0
```

Choose **one**, not both.

---

### 3. Enable Flash Attention

```bash
launchctl setenv OLLAMA_FLASH_ATTENTION 1
```

---

### 4. Set 65K context

```bash
launchctl setenv OLLAMA_CONTEXT_LENGTH 65536
```

---

### 5. Verify the settings

```bash
launchctl getenv OLLAMA_KV_CACHE_TYPE
launchctl getenv OLLAMA_FLASH_ATTENTION
launchctl getenv OLLAMA_CONTEXT_LENGTH
```

For Q8_0, expected:

```text
q8_0
1
65536
```

For Q4_0, expected:

```text
q4_0
1
65536
```

---

### 6. Quit and reopen Ollama

From the macOS menu bar:

**Ollama icon → Quit Ollama**

Then open **Ollama** again from Applications.

---

### 7. Verify the settings after restart

```bash
launchctl getenv OLLAMA_KV_CACHE_TYPE
launchctl getenv OLLAMA_FLASH_ATTENTION
launchctl getenv OLLAMA_CONTEXT_LENGTH
```

Confirm the values are still:

```text
q8_0 or q4_0
1
65536
```

---

### 8. Run the 2-bit model

```bash
ollama run hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS
```

---

### 9. Verify the loaded model

In another Terminal window:

```bash
ollama ps
```

Expected shape:

```text
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL
hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS    ...    ...    100% GPU    65536    ...
```

The exact `SIZE` can vary with runtime state.

Check:

- `PROCESSOR` = `100% GPU`
- `CONTEXT` = `65536`
- KV cache = `q8_0` or `q4_0`, depending on what you selected
- Model = `IQ2_XS` GGUF

---

## Quick setup

### Q8_0

```bash
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
launchctl setenv OLLAMA_FLASH_ATTENTION 1
launchctl setenv OLLAMA_CONTEXT_LENGTH 65536
```

### Q4_0

```bash
launchctl setenv OLLAMA_KV_CACHE_TYPE q4_0
launchctl setenv OLLAMA_FLASH_ATTENTION 1
launchctl setenv OLLAMA_CONTEXT_LENGTH 65536
```

Then quit/reopen Ollama and run:

```bash
ollama run hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS
```

Verify with:

```bash
ollama ps
```

---

## Simple mental model

```text
Qwen3.8-27B IQ2_XS GGUF
        ↓
    2-bit model weights

        +

      q8_0 OR q4_0
        ↓
    KV cache precision

        +

       65K context
        ↓
      65536 tokens
```

So:

**`IQ2_XS` = model quantization**  
**`q8_0` / `q4_0` = KV-cache quantization**  
**`65536` = context window**
