import re
import json
import jsonlines

from openai import OpenAI


client = OpenAI(api_key="your_api_key")


def batch_eval(query_file, result1_file, output_file_path):

    with open(query_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    queries = [
        re.findall(r"Question \d+: (.+)", line.strip())[0].replace('"', '')
        for line in lines if line.strip()
    ]

    with open(result1_file, "r") as f:
        answers1 = json.load(f)
    answers1 = [i["response"] for i in answers1]

    requests = []
    for i, (query, answer1) in enumerate(zip(queries, answers1)):
        sys_prompt = """
        ---Role---
        You are an expert tasked with evaluating a single chatbot's answer to a question based on three criteria: **Comprehensiveness**, **Diversity**, and **Empowerment**.
        """

        prompt = f"""
        You will evaluate a single chatbot's answer to a question about book recommendations on an e-commerce platform, based on four criteria: **Comprehensiveness**, **Diversity**, **Empowerment**, and **Relevance**. For each criterion, assign a score from 1 to 10 (1 being the lowest, 10 the highest) and provide a concise explanation (1-2 sentences) for the score.

        - **Comprehensiveness**: How much detail does the answer provide about the book(s), including title, author, genre, price, reviews, and other relevant information? (1 = minimal detail, 10 = exhaustive detail covering all aspects)
        - **Diversity**: How varied are the book recommendations or insights provided, covering different genres, authors, or user preferences? (1 = single perspective or limited options, 10 = highly varied and inclusive)
        - **Empowerment**: How well does the answer help the user understand their options and make informed decisions about book purchases? (1 = little clarity or guidance, 10 = highly empowering with clear decision-making support)
        - **Relevance**: How well does the answer match the user's query, providing book recommendations that align with their preferences or needs? (1 = irrelevant or off-topic, 10 = perfectly tailored to the query)

        For each criterion, evaluate the answer and provide a concise explanation (1-2 sentences).

        Here is the question:
        {query}

        Here is the chatbot's answer:
        {answer1}

        Output your evaluation as a valid JSON object with the following structure:

        {{
            "Comprehensiveness": {{
                "Score": <integer from 1 to 10>,
                "Explanation": "Explain why this score was given for comprehensiveness."
            }},
            "Diversity": {{
                "Score": <integer from 1 to 10>,
                "Explanation": "Explain why this score was given for diversity."
            }},
            "Empowerment": {{
                "Score": <integer from 1 to 10>,
                "Explanation": "Explain why this score was given for empowerment."
            }},
            "Relevance": {{
                "Score": <integer from 1 to 10>,
                "Explanation": "Explain why this score was given for relevance."
            }},
            "Overall Score": {{
                "Score": <integer from 1 to 10>,
                "Explanation": "Provide an overall score (average of the four criteria, rounded to the nearest integer) and summarize why this score was given."
            }}
        }}

        **Important Instructions**:
        - The output must be a valid JSON object with all braces (`{{` and `}}`) properly closed.
        - Do not include markdown (```json```), extra newlines, spaces, or any text outside the JSON object.
        - Ensure "Score" is an integer between 1 and 10.
        - Keep explanations concise (1-2 sentences) to avoid exceeding token limits.
        - If the token limit is reached, prioritize completing the JSON structure (especially closing all braces) over adding more explanation.
        - Double-check that the JSON includes all five keys: "Comprehensiveness", "Diversity", "Empowerment", "Relevance", and "Overall Score".
        - For the "Overall Score", calculate the average of the four criteria scores, rounded to the nearest integer.
        - Consider the e-commerce context, where accurate book details, diverse and relevant recommendations, and decision-making support are critical.
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
        metadata={
            "name": "Score LibraAI",
            "description": "nightly eval job"
        }
    )

    print(f"Batch {batch.id} has been created.")


if __name__ == "__main__":
    EVAL_DIR = "eval3"
    topk_arr = [12, 22, 24, 26, 28, 30]
    # for top_k in range(4, 31, 2):
    for top_k in topk_arr:
        query_file = "./data/questions/125_questions_for_compare.txt"
        result1_file = f"./data/{EVAL_DIR}/topk{top_k}/125_responses_libraAI_topk{top_k}.json"
        output_file_path = f"./data/{EVAL_DIR}/topk{top_k}/SCORE_LibraAI_topk{top_k}.jsonl"
        
        batch_eval(query_file, result1_file, output_file_path)
    