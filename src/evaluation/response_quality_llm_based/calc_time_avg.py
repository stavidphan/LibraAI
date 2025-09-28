def calc_average_elapsed_time(log_file: str) -> float:
    times = []

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                try:
                    elapsed = float(parts[1])
                    times.append(elapsed)
                except ValueError:
                    continue  

    if not times:
        print("Không có dữ liệu hợp lệ.")
        return 0.0

    avg = sum(times) / len(times)
    print(f"Số dòng hợp lệ: {len(times)}")
    print(f"Trung bình thời gian (cột 2): {avg:.4f} giây")
    return avg

if __name__ == "__main__":
    log_path = "./data/eval5/topk6_old/time_responses_topk6.log" 
    log_path = "./data/eval5/topk6_old/time_query_context_topk6.log" 
    log_path = "./data/eval5/topk6_old/number_token_context_topk6.log"

    log_path = "./data/eval5/topk6_new/time_responses_topk6.log" 
    log_path = "./data/eval5/topk6_new/time_query_context_topk6.log" 
    log_path = "./data/eval5/topk6_new/number_token_context_topk6.log"
    calc_average_elapsed_time(log_path)
