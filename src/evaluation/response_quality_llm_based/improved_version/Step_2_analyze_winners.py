import json
import re
import os

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

# Analyze and summarize JSON
def analyze_winners(data, output_dir, top_k):
    categories = ["Comprehensiveness", "Diversity", "Empowerment", "Overall"]
    result_count = {category: {"Equal": 0, "Not equal": 0} for category in categories}
    total_requests = len(data)
    failed_parses = 0
    valid_requests = 0
    fixed_jsons = []
    invalid_jsons = []
    quality_metrics = {f'topk{top_k}': {category: [0.0, 0.0] for category in categories}}

    for request in data:
        try:
            response_body = request["response"]["body"]["choices"][0]["message"]["content"]
            cleaned_body = response_body.strip()
            was_fixed = False

            if cleaned_body.startswith('```json') and cleaned_body.endswith('```'):
                cleaned_body = cleaned_body[7:-3].strip()
            elif cleaned_body.startswith('```') and cleaned_body.endswith('```'):
                cleaned_body = cleaned_body[3:-3].strip()

            cleaned_body = re.sub(r'[^\x20-\x7E\n\t]', '', cleaned_body).strip()

            if cleaned_body.startswith('{') and not cleaned_body.endswith('}\n}'):
                cleaned_body += '}'
                was_fixed = True

            response_json = json.loads(cleaned_body)

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
                result = response_json[category].get("Result", "")
                if result in ["Equal", "Not equal"]:
                    result_count[category][result] += 1
                else:
                    print(f"Invalid result '{result}' in request {request['custom_id']} for {category}")
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
            print(f"Error processing request {request.get('custom_id', 'unknown')}: {e}")
            failed_parses += 1
            invalid_jsons.append({
                "custom_id": request.get("custom_id", "unknown"),
                "error": str(e),
                "response_body": response_body,
                "cleaned_body": cleaned_body
            })
            continue

    summary_lines = []
    summary_lines.append(f"Total requests: {total_requests}")
    summary_lines.append(f"Valid requests (including fixed): {valid_requests}")
    summary_lines.append(f"Fixed JSONs: {len(fixed_jsons)}")
    summary_lines.append(f"Failed parses (could not be fixed): {len(invalid_jsons)}\n")

    if valid_requests > 0:
        for category in categories:
            eq = result_count[category]["Equal"]
            neq = result_count[category]["Not equal"]
            total = eq + neq
            if total > 0:
                eq_percent = round((eq / total) * 100, 2)
                neq_percent = round((neq / total) * 100, 2)
                quality_metrics[f'topk{top_k}'][category] = [eq_percent, neq_percent]
            else:
                eq_percent = neq_percent = 0.0
            summary_lines.append(f"{category}:")
            summary_lines.append(f"  Equal     : {eq} times ({eq_percent:.2f}%)")
            summary_lines.append(f"  Not equal : {neq} times ({neq_percent:.2f}%)\n")
    else:
        summary_lines.append("No valid requests to analyze.")

    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, f'winners_summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(summary_lines))
    print(f"Summary saved to: {summary_path}")

    metrics_path = os.path.join(output_dir, f'quality_metrics_topk{top_k}.json')
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(quality_metrics, f, indent=2)
    print(f"Quality metrics saved to: {metrics_path}")


EVAL_DIR = "eval5"
topk_arr = [6]
for top_k in topk_arr:
    file_path = f"./data/eval5/compare_equal_with_old/IMPROVE_batch_eval_topk6_output.jsonl"
    output_dir = f"./data/{EVAL_DIR}/compare_equal_with_old/"

    # Execute
    data = read_jsonl_file(file_path)
    analyze_winners(data, output_dir, top_k)