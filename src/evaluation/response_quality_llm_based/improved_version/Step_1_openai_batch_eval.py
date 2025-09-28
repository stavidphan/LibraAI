import re
import json
import jsonlines

from openai import OpenAI


client = OpenAI(api_key="your_api_key")


def batch_eval(query_file, result1_file, result2_file, output_file_path):

    with open(query_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    queries = [
        re.findall(r"Question \d+: (.+)", line.strip())[0].replace('"', '')
        for line in lines if line.strip()
    ]

    with open(result1_file, "r") as f:
        answers1 = json.load(f)
    answers1 = [i["response"] for i in answers1]

    with open(result2_file, "r") as f:
        answers2 = json.load(f)
    answers2 = [i["response"] for i in answers2]

    requests = []
    for i, (query, answer1, answer2) in enumerate(zip(queries, answers1, answers2)):
        sys_prompt = """
        ---Role---
        You are an expert tasked with evaluating two answers to the same question based on three criteria: **Comprehensiveness**, **Diversity**, and **Empowerment**.
        """

        prompt = f"""
        You will evaluate two answers to the same question based on four criteria: **Comprehensiveness**, **Diversity**, **Empowerment**, and **Overall**.

        Your task is to determine whether both answers provide **a similar and sufficient level of response** for each criterion. You are not comparing which answer is better in detail — you are only checking if they are **equal in informational value**, based on what the user asked.

        Definitions:
        - **Comprehensiveness**: Do both answers cover the key aspect(s) of the question equally well?
        - **Diversity**: Do both answers include similar levels of variety or perspectives relevant to the question?
        - **Empowerment**: Do both answers help the reader equally well in understanding or making a decision?
        - **Overall**: Based on the above three, do the answers feel equally informative overall?

        For **each criterion**, choose one of:
        - `"Equal"` → if both answers address the question similarly and sufficiently.
        - `"Not equal"` → if one answer clearly lacks essential content the other includes.

        Here is the question:
        {query}

        Here are the two answers:

        **Answer 1:**
        {answer1}

        **Answer 2:**
        {answer2}

        Output your evaluation as a valid JSON object with the following structure:

        {{
        "Comprehensiveness": {{
            "Result": "Equal" or "Not equal",
            "Explanation": "Briefly explain why the answers are equal or not for this criterion."
        }},
        "Diversity": {{
            "Result": "Equal" or "Not equal",
            "Explanation": "Briefly explain why the answers are equal or not for this criterion."
        }},
        "Empowerment": {{
            "Result": "Equal" or "Not equal",
            "Explanation": "Briefly explain why the answers are equal or not for this criterion."
        }},
        "Overall": {{
            "Result": "Equal" or "Not equal",
            "Explanation": "Summarize whether the two answers are overall equal in informational value."
        }}
        }}

        **Important Instructions**:
        - The output must be a **valid JSON object** with all braces (`{{` and `}}`) properly closed.
        - Do not include markdown formatting (e.g., ```json), extra newlines, or any explanation outside the JSON.
        - Each "Result" must be exactly `"Equal"` or `"Not equal"`.
        - Keep each explanation short (1–2 sentences).
        - Prioritize a complete and well-formed JSON structure, especially closing all braces, even if explanation must be trimmed.
        """

        request_data = {
            "custom_id": f"request-{i+1}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt},
                ],
            },
        }

        requests.append(request_data)

    with jsonlines.open(output_file_path, mode="w") as writer:
        for request in requests:
            writer.write(request)

    print(f"Batch API requests written to {output_file_path}")

    batch_input_file = client.files.create(
        file=open(output_file_path, "rb"), purpose="batch"
    )
    batch_input_file_id = batch_input_file.id

    batch = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "nightly eval job"},
    )

    print(f"Batch {batch.id} has been created.")


if __name__ == "__main__":
    EVAL_DIR = "eval5"
    topk_arr = [6]
    # for top_k in range(4, 31, 2):
    for top_k in topk_arr:
        query_file = "./data/questions/125_questions_for_compare.txt"
        result1_file = "./data/eval5/topk6_new/125_responses_libraAI_topk6.json"
        result2_file = "./data/eval5/topk6_old/125_responses_libraAI_topk6.json"
        output_file_path = f"./data/{EVAL_DIR}/compare_equal_with_old/IMPROVE_batch_eval_topk{top_k}.jsonl"
        
        batch_eval(query_file, result1_file, result2_file, output_file_path)
    