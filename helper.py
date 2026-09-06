import ollama

def get_llm_response(prompt):
    response = ollama.chat(
        model="hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [
                    f"images/image_{image:02d}.png" for image in range(1, 12)
                ]
            }
        ]
    )
    eval_count = response.eval_count
    eval_duration_sec = response.eval_duration / 1_000_000_000
    tokens_per_sec = eval_count / eval_duration_sec
    prompt_tokens = response.prompt_eval_count
    llm_logs = f"""
                Generated tokens: {eval_count}
                Evaluation duration: {eval_duration_sec:.2f} seconds
                Tokens per second: {tokens_per_sec:.2f}
                Prompt tokens: {prompt_tokens}
                """
    with open("llm_logs.txt", "w", encoding="utf-8") as f:
        f.write(llm_logs)

    return response.message.content
