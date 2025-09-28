import json
import re
import os
import numpy as np

# Read JSONL file
def read_jsonl_file(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Error parsing JSONL line: {e}")
                continue
    return data

# Analyze and aggregate scores into metrics file
def analyze_scores(data, output_dir, top_k):
    categories = ["Comprehensiveness", "Diversity", "Empowerment", "Relevance", "Overall Score"]
    scores = {category: [] for category in categories}  # Lưu điểm số cho từng tiêu chí
    failed_parses = 0
    valid_requests = 0
    fixed_jsons = []  # Lưu JSON đã sửa
    invalid_jsons = []  # Lưu JSON không thể sửa
    quality_metrics = {f'topk{top_k}': {category: {"Mean": 0.0, "Std": 0.0} for category in categories}}

    for request in data:
        try:
            response_body = request["response"]["body"]["choices"][0]["message"]["content"]
            cleaned_body = response_body.strip()
            was_fixed = False

            # Clean markdown if present
            if cleaned_body.startswith('```json') and cleaned_body.endswith('```'):
                cleaned_body = cleaned_body[7:-3].strip()
            elif cleaned_body.startswith('```') and cleaned_body.endswith('```'):
                cleaned_body = cleaned_body[3:-3].strip()

            # Remove invalid characters
            cleaned_body = re.sub(r'[^\x20-\x7E\n\t]', '', cleaned_body).strip()

            # Check and fix missing '}'
            if cleaned_body.startswith('{') and not cleaned_body.endswith('}'):
                cleaned_body += '}'
                was_fixed = True

            # Try to parse JSON
            response_json = json.loads(cleaned_body)
            # print(response_json)

            # Check JSON structure and extract scores
            for category in categories:
                if category not in response_json:
                    print(f"Missing category {category} in request {request['custom_id']}")
                    failed_parses += 1
                    invalid_jsons.append({
                        "custom_id": request["custom_id"],
                        "error": f"Missing category {category}",
                        "response_body": response_body,
                        "cleaned_body": cleaned_body
                    })
                    break
                score = response_json[category].get("Score", None)
                if isinstance(score, int) and 1 <= score <= 10:
                    scores[category].append(score)
                else:
                    print(f"Invalid score '{score}' in request {request['custom_id']} for {category}")
                    failed_parses += 1
                    invalid_jsons.append({
                        "custom_id": request["custom_id"],
                        "error": f"Invalid score {score} for {category}",
                        "response_body": response_body,
                        "cleaned_body": cleaned_body
                    })
                    break
            else:
                valid_requests += 1
                if was_fixed:
                    fixed_jsons.append({
                        "custom_id": request["custom_id"],
                        "response_body": response_body,
                        "fixed_body": cleaned_body
                    })

        except json.JSONDecodeError as e:
            failed_parses += 1
            invalid_jsons.append({
                "custom_id": request["custom_id"],
                "error": str(e),
                "response_body": response_body,
                "cleaned_body": cleaned_body
            })
            continue
        except (KeyError, TypeError) as e:
            print(f"Error processing request {request['custom_id']}: {e}")
            failed_parses += 1
            invalid_jsons.append({
                "custom_id": request["custom_id"],
                "error": str(e),
                "response_body": response_body,
                "cleaned_body": cleaned_body
            })
            continue

    # Calculate quality metrics
    if valid_requests > 0:
        for category in categories:
            if scores[category]:
                mean_score = round(np.mean(scores[category]), 2)
                std_score = round(np.std(scores[category]), 2)
                quality_metrics[f'topk{top_k}'][category] = {"Mean": mean_score, "Std": std_score}
            else:
                quality_metrics[f'topk{top_k}'][category] = {"Mean": 0.0, "Std": 0.0}

    # Save quality metrics to JSON
    os.makedirs(output_dir, exist_ok=True)
    metrics_path = os.path.join(output_dir, f'SCORE_quality_metrics_topk{top_k}.json')
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(quality_metrics, f, indent=2)
    print(f"Quality metrics saved to: {metrics_path}")

# Main execution
EVAL_DIR = "eval3"
topk_arr = [2]
for top_k in range(4, 31, 2):
# for top_k in topk_arr:
    file_path = f"./data/{EVAL_DIR}/topk{top_k}/SCORE_output_topk{top_k}.jsonl"
    output_dir = f"./data/{EVAL_DIR}/topk{top_k}"

    # Execute
    data = read_jsonl_file(file_path)
    analyze_scores(data, output_dir, top_k)