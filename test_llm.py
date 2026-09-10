from helper import get_llm_response

#prompt for testing complex use case such as deriving QA strategy:
with open("llm_input.txt", "r", encoding="utf-8") as f:
    prompt = f.read()

# simple prompt for quick testing:
# prompt = "Explain in 5 concise points what a software test case is."

# prompt for testing with images:
# prompt = "Describe exactly what is visible in all these image."

llm_response = get_llm_response(prompt)

with open("llm_output.txt", "w", encoding="utf-8") as f:
    f.write(llm_response)

print("\n===== LLM RESPONSE =====\n")
print(llm_response)