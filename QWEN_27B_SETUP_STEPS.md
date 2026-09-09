# Qwen3.8 27B GSQ-RCO IQ2_XS — Practical Setup & Verification Steps

## 1. Pull and run the 2-bit IQ2_XS model

```bash
ollama run hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS
```

## 2. Check the loaded model

```bash
ollama ps
```

## 3. Check Ollama environment variables

```bash
env | grep '^OLLAMA_'
```

## 4. Check the important Ollama settings

```bash
launchctl getenv OLLAMA_FLASH_ATTENTION

launchctl getenv OLLAMA_KV_CACHE_TYPE

launchctl getenv OLLAMA_NUM_PARALLEL

launchctl getenv OLLAMA_MAX_LOADED_MODELS
```

## 5. Check memory usage

### macOS overall memory

```bash
vm_stat
```

```bash
memory_pressure
```

### Process-level memory

```bash
ps aux | grep -i ollama
```

For a live view:

```bash
top -o mem
```

In Activity Monitor, also check **Memory** for the Ollama process and overall memory pressure.

## 6. Set the context window

For an Ollama model, set the context for the running session with:

```bash
/set parameter num_ctx 65536
```

Then continue the chat.

Alternatively, start a new chat and set the context in the Ollama model configuration before running it.

## 7. Check the context window

```bash
ollama ps
```

Check the **CONTEXT** column. It should show:

```text
65536
```

## 8. Final verification

```bash
ollama ps
```

Confirm:

- Model: `Qwen3.8-27B-GSQ-RCO-IQ2_XS`
- Processor: expected Apple GPU/CPU usage
- Model size
- Context: `65536`

## Quick command sequence

```bash
ollama run hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS

ollama ps

env | grep '^OLLAMA_'

launchctl getenv OLLAMA_FLASH_ATTENTION
launchctl getenv OLLAMA_KV_CACHE_TYPE
launchctl getenv OLLAMA_NUM_PARALLEL
launchctl getenv OLLAMA_MAX_LOADED_MODELS

vm_stat
memory_pressure
ps aux | grep -i ollama

ollama ps
```
