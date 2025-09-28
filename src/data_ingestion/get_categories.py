import os
import json
import time
import httpx
import time


start_time = time.perf_counter()

# --- Config ---
SAVE_PATH = "./src/crawl_tiki_data"
CATEGORIES_FILE = f"{SAVE_PATH}/categories.json"
CATEGORY_LIMIT = 50  # Limit per category type (Vietnamese & English)

# Create folder if not exists
os.makedirs(SAVE_PATH, exist_ok=True)

# --- Function to generate API URL ---
def url_category_generator(page_path, cat_id, page):
    """ Generate API URL to fetch books from a category """
    return f"https://tiki.vn/api/personalish/v1/blocks/listings?limit=100&is_mweb=1&aggregations=2&sort=top_seller&urlKey={page_path}&category={cat_id}&page={page}"

# --- Function to fetch categories ---
def fetch_categories(main_category, main_cat_id):
    """ Fetch up to CATEGORY_LIMIT categories for a given main category """
    print(f"🔍 Fetching categories for {main_category}...")

    listing_url = url_category_generator(main_category, main_cat_id, "1")

    try:
        res = httpx.get(listing_url, timeout=10).json()
        level_one_categories = []

        for filter in res.get("filters", []):
            if filter.get("display_name") == "Danh Mục Sản Phẩm":
                level_one_categories = filter.get("values", [])  # No limit yet

        print(f"✅ Found {len(level_one_categories)} level 1 categories for {main_category}")

    except Exception as e:
        print(f"❌ Error fetching categories for {main_category}: {e}")
        level_one_categories = []

    # --- Fetch subcategories (level 2) ---
    print(f"🔍 Fetching level 2 categories for {main_category}...")

    all_categories = []
    for category in level_one_categories:
        if len(all_categories) >= CATEGORY_LIMIT:
            break  # Stop when reaching the limit

        time.sleep(1)  # Avoid sending requests too fast

        try:
            next_url = url_category_generator(category["display_value"], category["query_value"], 1)
            next_res = httpx.get(next_url, timeout=10).json()
            has_nested = False

            for filter in next_res.get("filters", []):
                if filter.get("display_name") == "Danh Mục Sản Phẩm":
                    sub_categories = filter["values"]
                    all_categories.extend(sub_categories)
                    has_nested = True

            if not has_nested:
                all_categories.append(category)

        except Exception as e:
            print(f"❌ Error fetching subcategories for {category['display_value']}: {e}")

        # Ensure we do not exceed CATEGORY_LIMIT
        if len(all_categories) > CATEGORY_LIMIT:
            all_categories = all_categories[:CATEGORY_LIMIT]

    print(f"✅ Total categories collected for {main_category}: {len(all_categories)}")
    return all_categories

# --- Fetch categories for both Vietnamese & English books ---
categories_vn = fetch_categories("sach-truyen-tieng-viet", "316")
# categories_en = fetch_categories("sach-tieng-anh", "320")

# --- Combine and save to JSON ---
all_categories = categories_vn  # + categories_en
with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
    json.dump(all_categories, f, ensure_ascii=False, indent=4)

print(f"✅ All categories saved to `{CATEGORIES_FILE}` (Total: {len(all_categories)})")


end_time = time.perf_counter()
print(f"\n\n⏳ Running time: {(end_time - start_time) / 60:.4f} minutes")