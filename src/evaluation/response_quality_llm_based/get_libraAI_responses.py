import requests
import json
import time
import re
import os


def query_api_and_save(query_file, result1_file, log_file, top_k, mode="hybrid"):
    url = "http://localhost:8000/query"
    headers = {"Content-Type": "application/json"}

    # Read the list of questions from the file
    with open(query_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Extract questions
    queries = [
        re.findall(r"Question \d+: (.+)", line.strip())[0].replace('"', '')
        for line in lines if line.strip()
    ]

    results = []
    successful_count = 0

    # Clear or create timing log file
    with open(log_file, "w", encoding="utf-8") as log_f:
        log_f.write("QuestionIdx\tElapsedTime(s)\tQuery\n")

    for idx, query in enumerate(queries, start=1):
        payload = {
            "query": query,
            "mode": mode,
            "top_k": top_k
        }

        print(f"Sending request {idx}: {query}")
        start_time = time.time()

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            elapsed_time = round(time.time() - start_time, 3)

            api_result = response.json()
            results.append(api_result)
            successful_count += 1
            print(f"✓ Received response for question {idx} in {elapsed_time} seconds")

            # Append response time to log
            with open(log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"{idx}\t{elapsed_time}\t{query}\n")

            # Save every 10 successful responses
            if successful_count % 10 == 0:
                with open(result1_file, "w", encoding="utf-8") as out_f:
                    json.dump(results, out_f, ensure_ascii=False, indent=4)
                print(f"💾 Auto-saved after {successful_count} successful responses")

        except requests.exceptions.RequestException as e:
            elapsed_time = round(time.time() - start_time, 3)
            print(f"✗ Error on request {idx}: {e}")
            results.append({"result": f"ERROR: {str(e)}"})

            with open(log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"{idx}\tERROR\t{query}\n")

        time.sleep(0.5)  # Optional: delay between requests

    # Final save
    with open(result1_file, "w", encoding="utf-8") as out_f:
        json.dump(results, out_f, ensure_ascii=False, indent=4)

    print(f"\n✅ All responses saved to {result1_file}")
    print(f"🕒 Timing log saved to {log_file}")


if __name__ == "__main__":
    EVAL_DIR = "eval3"
    topk_arr = [4]
    for top_k in range(6, 31, 2):
    # for top_k in topk_arr:
        topk_eval_dir = f"./data/{EVAL_DIR}/topk{top_k}"
        os.makedirs(topk_eval_dir, exist_ok=True)
        query_api_and_save(
            query_file="./data/questions/125_questions_for_compare.txt",
            result1_file=f"{topk_eval_dir}/125_responses_libraAI_topk{top_k}.json",
            log_file=f"{topk_eval_dir}/time_responses_topk{top_k}.log",
            top_k=top_k
        )