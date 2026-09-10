# Qwen3.8 27B — 2-bit Model + Q4 KV Cache + 65K Context

## What we are configuring

- **Model:** `hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS`
- **Model quantization:** `IQ2_XS` (2-bit model quantization)
- **KV cache:** `q4_0`
- **Flash Attention:** enabled
- **Context:** `65536` (65K)

> **Important:** The 2-bit quantization is part of the downloaded model itself. The `IQ2_XS` GGUF is the 2-bit model artifact. `q4_0` is a separate KV-cache setting.

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

### 2. Set Q4 KV cache

```bash
launchctl setenv OLLAMA_KV_CACHE_TYPE q4_0
```

### 3. Enable Flash Attention

```bash
launchctl setenv OLLAMA_FLASH_ATTENTION 1
```

### 4. Set 65K context

```bash
launchctl setenv OLLAMA_CONTEXT_LENGTH 65536
```

### 5. Verify all three settings

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

### 6. Quit and reopen Ollama

From the macOS menu bar:

**Ollama icon → Quit Ollama**

Then open **Ollama** again from Applications.

### 7. Verify the settings after restart

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

### 8. Run the 2-bit model

```bash
ollama run hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS
```

### 9. Verify the loaded model

In another Terminal window:

```bash
ollama ps
```

Expected shape:

```text
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL
hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS    ...    ~10 GB    100% GPU    65536    ...
```

The exact `SIZE` can vary slightly by runtime state, so the important checks are:

- `PROCESSOR` = `100% GPU`
- `CONTEXT` = `65536`
- Q4 KV is set to `q4_0`
- The model is the `IQ2_XS` GGUF

---

## Simple mental model

```text
Qwen3.8-27B IQ2_XS GGUF
        ↓
   2-bit model weights

        +

     q4_0 KV cache
        ↓
   4-bit KV cache

        +

    65K context
        ↓
     65536 tokens
```

So:

**`IQ2_XS` = model quantization**  
**`q4_0` = KV-cache quantization**  
**`65536` = context window**
