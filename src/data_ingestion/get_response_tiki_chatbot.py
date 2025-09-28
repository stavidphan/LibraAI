import httpx
import time
import json
import re
from typing import List, Dict

def query_api_and_save(questions_file: str, output_file: str) -> None:
    # Đọc file câu hỏi
    with open(questions_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    questions = [
        re.findall(r"Question \d+: (.+)", line.strip())[0].replace('"', '')
        for line in lines if line.strip()
    ]

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en,vi;q=0.9,en-US;q=0.8",
        "origin": "https://chat-service.tiki.vn",
        "referer": "https://chat-service.tiki.vn/",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
        "x-access-token": "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxNjY4MDg1NiIsImlhdCI6MTc0Mzk0NTM2NCwiZXhwIjoxNzQ0MDMxNzY0LCJpc3MiOiJodHRwczovL3Rpa2kudm4iLCJjdXN0b21lcl9pZCI6IjE2NjgwODU2IiwiZW1haWwiOiJ0aGFuaGR1eXBoYW4yMTIzQGdtYWlsLmNvbSIsImNsaWVudF9pZCI6InRpa2ktc3NvIiwibmFtZSI6IjE2NjgwODU2Iiwic2NvcGUiOiJzc28iLCJncmFudF90eXBlIjoic21zIn0.CThmkKN_tOYCtMqWBbTEKCg_vFuGyk8VVyx2LCBbBkAiNufYk9DIQjjocckfYUWDslrB0LIyIovmdMeDI6ZGtlhjL6t79veA84I6MNOJHVAbvWjOLvqEYEuQmyMGLJMorNTl0jGFZH8h4MfBrk6gy9d0f_DBo8nOD1-ZttMaD36QM2Pedu2GczL4uFC261t9Ill5Urr3_yJNmskYtp9WSCtRsC-pN5QTmnVh288dBtfm1b7E0MZsKAZFQvLVTMKGTBOOy-bJLAFMeD0LBXscXEIIkJ8xl-igRSO_b6Y8KspifWQtE6ZNGH9aH-s6Nm08nR2gsRE83oLBYmz8NURmK4Pr0GauYQ_nsfAMBrWoh_y2JW7cbUXyPD95hxAnKqG2AJ77SUS3msC1YRDcvEXLSoEkIdfhganJndi7qlk7GoZE1osTcp2kQAJ6cV_XAWbGGgdkYs30a87F55ZlZ1LzRpUspscmQU7ngDl3f5JD_WNLDeJJjlt9oMq0-_ipG76y29uIByf1pquX7S4ODbFFHUcc61hSFzbF2TWjXpJWVICqhxiPIrp4BkHX2a8T4Xw2fvDbeTHQud7AyZX9ywAC3liYmudBFYJEGncNACglvnydso9jmM1cnBooK0EVpgkjwNxsR4Kxxk0dISuFCL4yeutJR7Co_pRHDbL0SJXhfDw",
        "x-source": "shopping"
    }

    results: List[Dict[str, str]] = []
    MAX_RETRIES = 3
    REQUEST_DELAY = 2  # Delay tối thiểu giữa các request (giây)
    BATCH_SIZE = 5     # Số request tối đa trước khi nghỉ dài hơn

    def get_complete_response(q: str) -> str:
        retry_count = MAX_RETRIES
        response_text = ""
        
        while retry_count > 0:
            try:
                query = httpx.QueryParams({"content": q})
                url = f"https://falcon-api.tiki.vn/ext/v1/chat-stream?{query}"
                
                with httpx.stream("GET", url, headers=headers, timeout=60.0) as response:
                    buffer = ""
                    for chunk in response.iter_text():
                        if chunk.strip():
                            buffer += chunk
                            # print(chunk, end="", flush=True)
                            # Kiểm tra xem đã nhận được is_stop chưa
                            if '"is_stop":true' in buffer:
                                return buffer
                    
                    # Nếu hết stream mà chưa có is_stop
                    response_text = buffer
                    if '"is_stop":true' not in response_text:
                        print(f"\nIncomplete response for '{q}', retrying...")
                        retry_count -= 1
                        time.sleep(REQUEST_DELAY * 2)  # Delay dài hơn khi retry
                    else:
                        return response_text
                
            except (httpx.RequestError, httpx.TimeoutException) as e:
                print(f"\nError: {e} for question '{q}', retrying ({retry_count} attempts left)...")
                retry_count -= 1
                time.sleep(REQUEST_DELAY * 2)
            
            if retry_count == 0:
                print(f"\nFailed to get complete response for '{q}' after {MAX_RETRIES} attempts")
                return response_text
        
        return response_text

    def extract_second_last_content(response_text: str) -> str:
        if not response_text:
            return ""
            
        lines = response_text.strip().split("\n\n")
        is_stop_index = -1
        
        # Tìm is_stop từ dưới lên
        for i in range(len(lines) - 1, -1, -1):
            if '"is_stop":true' in lines[i]:
                is_stop_index = i
                break
        
        if is_stop_index == -1:
            return ""
            
        # Tìm content thứ 2 từ is_stop
        content_count = 0
        for i in range(is_stop_index - 1, -1, -1):
            if '"content":' in lines[i]:
                content_count += 1
                if content_count == 2:
                    match = re.search(r'"content":"(.*?)"(?=,|$)', lines[i])
                    return match.group(1) if match else ""
        
        return ""  # Trả về rỗng nếu không đủ 2 content

    # Xử lý từng câu hỏi
    for idx, q in enumerate(questions):
        print(f"\nProcessing question {idx + 1}/{len(questions)}: {q}")
        
        # Gửi request và lấy response hoàn chỉnh
        response_text = get_complete_response(q)
        final_content = extract_second_last_content(response_text)
        
        results.append({"question": q, "response": final_content})
        print("\n" + "=" * 50)

        # Auto-save sau mỗi 10 câu hỏi
        if (idx + 1) % 10 == 0:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"Auto-saved {idx + 1} results to {output_file}")

        # Điều chỉnh delay để tránh block
        if (idx + 1) % BATCH_SIZE == 0:
            print(f"Pausing after {BATCH_SIZE} requests to avoid rate limiting...")
            time.sleep(REQUEST_DELAY * 3)  # Delay dài hơn sau mỗi batch
        else:
            time.sleep(REQUEST_DELAY)  # Delay cơ bản giữa các request

    # Lưu kết quả cuối cùng
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Completed! Final results saved to {output_file}")

if __name__ == "__main__":
    questions_file = "./data/questions/125_questions_for_compare.txt"
    output_file = "./data/response_of_LLM/125_responses_tikiAI.json"
    query_api_and_save(questions_file, output_file)