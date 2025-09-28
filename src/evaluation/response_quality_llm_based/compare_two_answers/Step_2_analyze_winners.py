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
    categories = ["Comprehensiveness", "Diversity", "Empowerment", "Overall Winner"]
    winners_count = {category: {"Answer 1": 0, "Answer 2": 0} for category in categories}
    total_requests = len(data)
    failed_parses = 0
    valid_requests = 0
    fixed_jsons = []  # Store fixed JSONs
    invalid_jsons = []  # Store JSONs that could not be fixed
    quality_metrics = {f'topk{top_k}': {category: [0.0, 0.0] for category in categories}}


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
            if cleaned_body.startswith('{') and not cleaned_body.endswith('}\n}'):
                cleaned_body += '}'
                was_fixed = True

            # Try to parse JSON
            response_json = json.loads(cleaned_body)

            # Check JSON structure
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
                winner = response_json[category].get("Winner", "")
                if winner in ["Answer 1", "Answer 2"]:
                    winners_count[category][winner] += 1
                else:
                    print(f"Invalid winner '{winner}' in request {request['custom_id']} for {category}")
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

    # # Print list of fixed JSONs
    # if fixed_jsons:
    #     print("\nFixed JSONs:")
    #     for idx, fixed_json in enumerate(fixed_jsons, 1):
    #         print(f"\nFixed JSON #{idx}:")
    #         print(f"Request ID: {fixed_json['custom_id']}")
    #         print("\nOriginal response_body:")
    #         print("-" * 50)
    #         print(fixed_json['response_body'])
    #         print("-" * 50)
    #         print("\nFixed body (after adding '}'):")
    #         print("-" * 50)
    #         print(fixed_json['fixed_body'])
    #         print("-" * 50)

    # # Print list of invalid JSONs
    # if invalid_jsons:
    #     print("\nInvalid JSONs (could not be fixed):")
    #     for idx, invalid_json in enumerate(invalid_jsons, 1):
    #         print(f"\nInvalid JSON #{idx}:")
    #         print(f"Request ID: {invalid_json['custom_id']}")
    #         print(f"Error: {invalid_json['error']}")
    #         print("\nOriginal response_body:")
    #         print("-" * 50)
    #         print(invalid_json['response_body'])
    #         print("-" * 50)
    #         print("\nCleaned body (after processing):")
    #         print("-" * 50)
    #         print(invalid_json['cleaned_body'])
    #         print("-" * 50)

    # Calculate quality metrics
    summary_lines = []
    summary_lines.append(f"Total requests: {total_requests}")
    summary_lines.append(f"Valid requests (including fixed): {valid_requests}")
    summary_lines.append(f"Fixed JSONs: {len(fixed_jsons)}")
    summary_lines.append(f"Failed parses (could not be fixed): {len(invalid_jsons)}\n")

    if valid_requests > 0:
        for category in categories:
            answer1_count = winners_count[category]["Answer 1"]
            answer2_count = winners_count[category]["Answer 2"]
            total_counts = answer1_count + answer2_count
            if total_counts > 0:
                answer1_percent = round((answer1_count / total_counts) * 100, 2)
                answer2_percent = round((answer2_count / total_counts) * 100, 2)
                quality_metrics[f'topk{top_k}'][category] = [answer1_percent, answer2_percent]
            else:
                answer1_percent = answer2_percent = 0.0
            summary_lines.append(f"{category}:")
            summary_lines.append(f"  Answer 1: {answer1_count} times ({answer1_percent:.2f}%)")
            summary_lines.append(f"  Answer 2: {answer2_count} times ({answer2_percent:.2f}%)\n")
    else:
        summary_lines.append("No valid requests to analyze.")

    # Save summary to file
    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, f'winners_summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(summary_lines))
    print(f"Summary saved to: {summary_path}")

    # Save quality metrics to JSON
    metrics_path = os.path.join(output_dir, f'quality_metrics_topk{top_k}.json')
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(quality_metrics, f, indent=2)
    print(f"Quality metrics saved to: {metrics_path}")


EVAL_DIR = "eval3"
topk_arr = [2]
# for top_k in range(2, 31, 2):
for top_k in topk_arr:
    file_path = f"./data/eval5/compare_4_with_tiki/batch_eval_topk6_output.jsonl"
    output_dir = f"./data/eval5/compare_4_with_tiki"

    # Execute
    data = read_jsonl_file(file_path)
    analyze_winners(data, output_dir, top_k)