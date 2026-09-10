import ollama
import csv

def get_llm_response(prompt):
    response = ollama.chat(
        model="hf.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF:IQ2_XS",
        # model="qwen3.8:27b-mlx",
        messages=[
            {
                # overall rules / persona / behavior
                "role": "system",
                "content": "You are a QA Architect. Generate precise and structured output."
            },
            {       
                # current specific task         
                "role": "user",
                "content": prompt,
                "images": [
                    f"images/image_{image:02d}.png" for image in range(1, 12)
                ]
            }
        ],
        options={"temperature": 0.0}, #temperature=0.0 for deterministic output (0 randomness) and temperature=1.0 for more creative output
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


def txt_to_csv(input_file, output_file):
    f = open(input_file, "r", encoding="utf-8")
    lines = f.readlines()
    f.close()

    rows = []
    for line in lines:
        if line.strip() == "":
            continue
        row = line.strip().split("|")
        row = [cell.strip() for cell in row]
        rows.append(row)

        f = open(output_file, "w", newline="", encoding="utf-8")
        writer = csv.writer(f)
        writer.writerows(rows)
        f.close()