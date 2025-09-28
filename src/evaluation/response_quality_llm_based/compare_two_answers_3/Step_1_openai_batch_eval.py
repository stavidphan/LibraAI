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
        You will evaluate two answers to the same question based on three criteria: **Comprehensiveness**, **Diversity**, and **Empowerment**.

        - **Comprehensiveness**: How much detail does the answer provide to cover all aspects and details of the question?
        - **Diversity**: How varied and rich is the answer in providing different perspectives and insights on the question?
        - **Empowerment**: How well does the answer help the reader understand and make informed judgments about the topic?

        For each criterion, select the better answer: "Answer 1", "Answer 2", or "Equal".  
        **"Equal"** means that both answers provide equally good information for that criterion — neither is clearly better. For example, if the question asks for the price of a product, and both answers provide the correct price with similar clarity, then select "Equal".

        Provide a concise explanation (1-2 sentences) for your choice in each criterion.

        Then, select an **Overall Winner**: "Answer 1", "Answer 2", or "Equal", and summarize why you selected it based on the three criteria.

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
                "Winner": "Answer 1" or "Answer 2" or "Equal",
                "Explanation": "Explain why this answer is better (or equal) for comprehensiveness."
            }},
            "Diversity": {{
                "Winner": "Answer 1" or "Answer 2" or "Equal",
                "Explanation": "Explain why this answer is better (or equal) for diversity."
            }},
            "Empowerment": {{
                "Winner": "Answer 1" or "Answer 2" or "Equal",
                "Explanation": "Explain why this answer is better (or equal) for empowerment."
            }},
            "Overall Winner": {{
                "Winner": "Answer 1" or "Answer 2" or "Equal",
                "Explanation": "Summarize why this answer is the overall winner (or equal) based on the three criteria."
            }}
        }}

        **Important Instructions**:
        - The output must be a **valid JSON object** with all braces (`{{` and `}}`) properly closed.
        - Do not include markdown (```json```), extra newlines, spaces, or any text outside the JSON object.
        - Ensure "Winner" is exactly one of: "Answer 1", "Answer 2", or "Equal".
        - Keep explanations concise (2-3 sentences) to avoid exceeding token limits.
        - If the token limit is reached, prioritize completing the JSON structure (especially closing all braces) over adding more explanation.
        - Double-check that the JSON includes all four keys: "Comprehensiveness", "Diversity", "Empowerment", and "Overall Winner".
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
        result1_file = f"./data/eval5/topk6_new/125_responses_libraAI_topk6.json"
        result2_file = "./data/eval5/topk6_old/125_responses_libraAI_topk6.json"
        output_file_path = f"./data/{EVAL_DIR}/compare_3_with_old/batch_eval_topk{top_k}.jsonl"
        
        batch_eval(query_file, result1_file, result2_file, output_file_path)
    