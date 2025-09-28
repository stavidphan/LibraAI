import os
import json
import httpx
import pandas as pd
import time
import random
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
CRAWL_DIR = os.getenv("CRAWL_DIR", "data/crawl_tiki_data")
BOOKS_CRAWL_LIMIT = int(os.getenv("BOOKS_CRAWL_LIMIT", 500))
NUM_CATEGORIES = int(os.getenv("NUM_CATEGORIES", 20))

def crawl_books(output_file):
    print("\n\n\n🕷️ START crawling books from Tiki...\n")
    start_time = time.perf_counter()

    # Load categories from CRAWL_DIR
    categories_file = os.path.join("src/crawl_tiki_data/categories.json")
    with open(categories_file, "r", encoding="utf-8") as f:
        all_categories = json.load(f)

    BOOKS_PER_CAT = max(1, BOOKS_CRAWL_LIMIT // NUM_CATEGORIES)
    # User-Agent List for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
    ]

    HEADERS = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://tiki.vn/",
        "Accept": "application/json, text/plain, */*"
    }

    def url_category_generator(page_path, cat_id, page):
        return f"https://tiki.vn/api/personalish/v1/blocks/listings?limit=100&is_mweb=1&aggregations=2&sort=top_seller&urlKey={page_path}&category={cat_id}&page={page}"

    def fetch_with_retry(url, client, retries=5, timeout=10):
        for attempt in range(retries):
            try:
                response = client.get(url, headers=HEADERS, timeout=timeout)
                if response.status_code == 302:
                    print(f"⚠️ Redirected (302) - Wait 5 seconds...")
                    time.sleep(5)
                    continue
                response.raise_for_status()
                return response.json()
            except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
                print(f"⚠️ Error {e} - Retry ({attempt + 1}/{retries})")
                time.sleep(5)
        return None

    def list_books_in_cat(category, num_books_needed, client):
        books_set = set()
        books_list = []
        page = 1
        while len(books_list) < num_books_needed and page <= 10:
            url = url_category_generator(category["url_key"], category["query_value"], page)
            res = fetch_with_retry(url, client)
            if res is None or "data" not in res:
                page += 1
                continue
            for book in res["data"]:
                if len(books_list) >= num_books_needed:
                    break
                id_book = book.get("id", "")
                url_book = f"https://tiki.vn/api/v2/products/{id_book}?platform=web&spid=226923791&version=3"
                res_book = fetch_with_retry(url_book, client)
                if res_book is None:
                    continue
                required_fields = ["id", "name", "short_url", "price", "original_price"]
                if any(field not in res_book or res_book[field] is None for field in required_fields):
                    continue
                if res_book.get("rating_average", 0) == 0 or res_book.get("discount_rate", 0) == 0:
                    continue
                book_name = res_book["name"]
                if book_name in books_set:
                    continue
                books_set.add(book_name)
                authors = [author["name"] for author in res_book.get("authors", []) if "name" in author]
                author_names = ", ".join(authors) if authors else None
                manufacturers = []
                for spec in res_book.get("specifications", []):
                    for attr in spec.get("attributes", []):
                        if attr.get("code") == "manufacturer":
                            manufacturers.append(attr.get("value"))
                manufacturer_name = ", ".join(manufacturers) if manufacturers else None
                category_name = res_book.get("categories", {}).get("name", "Unknown")
                seller_name = res_book.get("current_seller", {}).get("name", "Unknown")
                quantity_sold = res_book.get("quantity_sold", {}).get("value", 0)
                info_book = {
                    "id": res_book["id"],
                    "name": book_name,
                    "link": res_book["short_url"],
                    "current_price": res_book["price"],
                    "original_price": res_book["original_price"],
                    "discount_rate": res_book.get("discount_rate", 0),
                    "rating_average": res_book.get("rating_average", 0),
                    "quantity_sold": quantity_sold,
                    "authors": author_names,
                    "seller_name": seller_name,
                    "category": category_name,
                    "manufacturer": manufacturer_name,
                    "short_description": res_book.get("short_description", "")
                }
                books_list.append(info_book)
            page += 1
            time.sleep(5)
        return books_list

    all_books = []
    books_needed = BOOKS_CRAWL_LIMIT
    category_index = 0

    with httpx.Client() as client:
        while books_needed > 0 and category_index < len(all_categories):
            category = all_categories[category_index]
            num_books_per_cat = min(BOOKS_PER_CAT, books_needed)
            books = list_books_in_cat(category, num_books_per_cat, client)
            all_books.extend(books)
            books_collected = len(books)
            books_needed -= books_collected
            print(f"✅ {category['display_value']} - Collected {books_collected} books (Remaining: {books_needed})")
            category_index += 1

    if books_needed > 0:
        print(f"⚠️ Exhausted all categories. Not enough books ({BOOKS_CRAWL_LIMIT}), collected {len(all_books)}.")
    else:
        print(f"✅ Successfully collected {len(all_books)} books as requested ({BOOKS_CRAWL_LIMIT}).")

    df = pd.DataFrame(all_books)
    df.to_csv(output_file, index=False)
    print(f"✅ Total books: {len(all_books)} saved to {output_file}")
    
    end_time = time.perf_counter()
    print("\n🕷️ END crawling books from Tiki...\n\n")
    print(f"⏳ Running time: {(end_time - start_time) / 60:.4f} minutes\n")
    return output_file, len(all_books)

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    crawl_books(os.path.join(CRAWL_DIR, f"books_data_{timestamp}.csv"))