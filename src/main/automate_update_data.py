import os
from datetime import datetime
import time
from src.data_ingestion.get_books import crawl_books
from src.data_comparison.compare_data import detect_changes
from src.data_preprocessing.process_tiki_books import process_books_to_texts
import httpx
import logging
from dotenv import load_dotenv
from difflib import unified_diff

# Load environment variables from .env file in project root
load_dotenv()

# Configuration from environment variables
CRAWL_DIR = os.getenv("CRAWL_DIR", "data/crawl_tiki_data")
COMPARE_DIR = os.getenv("COMPARE_DIR", "data/compare")
DAYS_TO_KEEP = int(os.getenv("DAYS_TO_KEEP", 7))
INSERT_BATCH_API = os.getenv("INSERT_BATCH_API", "http://localhost:8000/insert_batch")
LOG_FILE = os.getenv("LOG_FILE", "data/update_data.log")
LOG_FILE_MODE = os.getenv("LOG_FILE_MODE", "w")

# Configure logging to append with timestamp
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode=LOG_FILE_MODE
)

def get_latest_file(directory, prefix, extension=".csv", exclude_file=None):
    """Find the most recent file in the directory based on timestamp, excluding a specified file."""
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith(extension)]
    if exclude_file:
        files = [f for f in files if os.path.join(directory, f) != exclude_file]
    
    if not files:
        logging.info(f"No valid files found in {directory} with prefix {prefix} after exclusion")
        return None
    
    valid_files = []
    for f in files:
        try:
            parts = f.split('_')
            if len(parts) < 3:
                logging.warning(f"Skipping file with invalid format: {f}")
                continue
            timestamp_str = f"{parts[-2]}_{parts[-1].replace(extension, '')}"
            datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
            valid_files.append(f)
        except ValueError:
            logging.warning(f"Skipping file with invalid timestamp: {f}")
            continue
    
    if not valid_files:
        logging.info(f"No valid files found in {directory} with prefix {prefix} after validation")
        return None
    
    latest_file = max(valid_files, key=lambda f: datetime.strptime(f"{f.split('_')[-2]}_{f.split('_')[-1].replace(extension, '')}", "%Y-%m-%d_%H-%M-%S"))
    logging.info(f"Latest file found: {latest_file}")
    return os.path.join(directory, latest_file)

def cleanup_old_files(directory, days_to_keep=DAYS_TO_KEEP):
    """Delete files older than the specified number of days."""
    now = datetime.now()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if not filename.endswith('.csv'):
            continue
        try:
            parts = filename.split('_')
            if len(parts) < 3:
                logging.warning(f"Skipping cleanup of invalid file: {filename}")
                continue
            timestamp_str = f"{parts[-2]}_{parts[-1].replace('.csv', '')}"
            file_date = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
            if (now - file_date).days > days_to_keep:
                os.remove(file_path)
                logging.info(f"Deleted old file: {file_path}")
        except (ValueError, IndexError):
            logging.warning(f"Skipping cleanup of invalid file: {filename}")
            continue

def process_and_insert(file_path):
    """Process a file and insert its data into LightRAG."""
    try:
        start_time = time.time()
        texts, ids = process_books_to_texts(file_path)
        with httpx.Client() as client:
            logging.info(f"START inserting data from {file_path} into LightRAG...")
            # response = client.post(
            #     INSERT_BATCH_API,
            #     json={"texts": texts, "ids": ids}
            # )
            response = client.post(
                INSERT_BATCH_API,
                json={"path": file_path}
            )
            response.raise_for_status()
            end_time = time.time()
            logging.info(f"\n\nTotal insert data time: {end_time - start_time:.2f} seconds")
            logging.info(f"END inserting {len(texts)} books into LightRAG\n")
    except Exception as e:
        logging.error(f"Insert failed for {file_path}: {e}")

def main():
    logging.info(f"\n\nSTART crontab...")
    """Run the data update process with flexible trigger frequency."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    new_file = os.path.join(CRAWL_DIR, f"books_data_{timestamp}.csv")
    new_file = os.path.join(CRAWL_DIR, f"books_data_2025-06-13_14-30-45.csv")
    changes_file = os.path.join(COMPARE_DIR, f"changes_{timestamp}.csv")

    os.makedirs(CRAWL_DIR, exist_ok=True)
    os.makedirs(COMPARE_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Step 1: Crawl new data
    # try:
    #     logging.info("START crawling data...")
    #     start_time = time.time()
    #     _, num_books_collected = crawl_books(new_file)
    #     end_time = time.time()
    #     logging.info(f"\n\nCrawled {num_books_collected} books in {end_time - start_time:.2f} seconds.")
    #     logging.info(f"END crawling data, output: {new_file}\n")
    # except Exception as e:
    #     logging.error(f"Crawl failed: {e}")
    #     return

    # Step 2: Find the most recent old file for comparison, excluding the new file
    logging.info(f"Scanning directory: {CRAWL_DIR} for files with prefix: books_data")
    old_file = get_latest_file(CRAWL_DIR, "books_data", exclude_file=new_file)
    if old_file:
        # If there's an old file, compare and insert changes
        try:
            logging.info("START comparing data...")
            start_time = time.time()
            temp_changes_file = detect_changes(old_file, new_file)
            logging.info(f"Comparison time: {time.time() - start_time:.2f} seconds")
            
            # if changes data today not differrent with changes data yesterday => don't save change files
            if temp_changes_file:
                latest_change_file = get_latest_file(COMPARE_DIR, "changes")

                should_save = True
                if latest_change_file:
                    with open(temp_changes_file, 'r', encoding='utf-8') as f1, open(latest_change_file, 'r', encoding='utf-8') as f2:
                        diff = list(unified_diff(
                            f1.readlines(), 
                            f2.readlines()
                        ))
                        if not diff:
                            logging.info("Detected changes are same as latest changes. Skip saving and inserting.")
                            should_save = False

                if should_save:
                    os.replace(temp_changes_file, changes_file)
                    logging.info(f"END comparing data | New changes detected and saved to {changes_file}")
                    process_and_insert(changes_file)
                else:
                    os.remove(temp_changes_file)
            else:
                logging.info("No new or changed books. Nothing to insert.")
            
            logging.info(f"END comparing data.\n\n\n")
        except Exception as e:
            logging.error(f"Comparison failed: {e}")
            return
    else:
        # If no old file (first crawl), insert the new file directly
        logging.info("No previous file found, inserting initial crawl data...")
        process_and_insert(new_file)

    # Clean up old files
    cleanup_old_files(CRAWL_DIR, DAYS_TO_KEEP)
    cleanup_old_files(COMPARE_DIR, DAYS_TO_KEEP)

if __name__ == "__main__":
    main()