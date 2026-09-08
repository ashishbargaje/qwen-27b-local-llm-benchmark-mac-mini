from io import StringIO

from helper import get_llm_response, txt_to_csv
import pandas as pd

f = open("archive/qa-strategy-llm-output.md", "r", encoding="utf-8")
qa_strategy = f.read()
f.close()

prompt = f"""
Generate 50 critical test cases based on the following QA strategy:

{qa_strategy}

Return ONLY valid CSV.

CSV columns:
ID,Scenario,Priority,Test Type,Expected Result

Rules:
- Use comma as the delimiter.
- First row must be the header.
- Generate exactly 50 test cases.
- Do not use Markdown tables.
- Do not use ```csv or ``` code fences.
- Do not add any explanation before or after the CSV.
- If a field contains a comma, enclose that field in double quotes.
"""

llm_response = get_llm_response(prompt).strip()

if llm_response.startswith("```"):
    lines = llm_response.splitlines()

    if lines[0].strip().startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    llm_response = "\n".join(lines).strip()

df = pd.read_csv(StringIO(llm_response))
df.to_csv("test_cases.csv", index=False)

# with open("test_cases.txt", "w", encoding="utf-8") as f:
#     f.write(llm_response)
# txt_to_csv("test_cases.txt", "test_cases.csv")