import pandas as pd
import time

def process_books_to_texts(csv_file):
    print("🕷️ START process books to texts...\n")
    start_time = time.perf_counter()
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print("File not found.")
        return [], []

    def generate_book_description(row):
        name = row["name"] if pd.notna(row["name"]) else "N/A"
        link = row["link"] if pd.notna(row["link"]) else "N/A"
        price = f"{int(row['current_price'])} VND" if pd.notna(row["current_price"]) else "N/A"
        original_price = f"{int(row['original_price'])} VND" if pd.notna(row["original_price"]) else "N/A"
        discount = f"{int(row['discount_rate'])}%" if pd.notna(row["discount_rate"]) else "N/A"
        rating = f"{row['rating_average']} sao" if pd.notna(row["rating_average"]) else "N/A"
        sold = f"{int(row['quantity_sold'])}" if pd.notna(row["quantity_sold"]) else "N/A"
        authors = ", ".join([a.strip() for a in row["authors"].split(",")]) if pd.notna(row["authors"]) else "N/A"
        seller_name = row["seller_name"] if pd.notna(row["seller_name"]) else "N/A"
        manufacturer = row["manufacturer"] if pd.notna(row["manufacturer"]) else "N/A"
        category = row["category"] if pd.notna(row["category"]) else "N/A"
        short_desc = row["short_description"] if pd.notna(row["short_description"]) else "N/A"
        book_info = f"""Book Name: {name}
Link: {link}
Current Price: {price}
Original Price: {original_price}
Discount: {discount}
Rating: {rating}
Sold Quantity: {sold}
Authors: {authors}
Seller Name: {seller_name}
Manufacturer: {manufacturer}
Category: {category}
Description: {short_desc}"""
        return book_info

    texts = df.apply(generate_book_description, axis=1).tolist()
    ids = df["id"].astype(str).tolist()
    
    print(f"✅ Processed {len(texts)} books from {csv_file}\n")
    print("🕷️ END process books to texts\n\n")
    
    end_time = time.perf_counter()
    print(f"⏳ Running time: {(end_time - start_time) / 60:.4f} minutes\n")
    return texts, ids

if __name__ == "__main__":
    texts, ids = process_books_to_texts("./data/crawl_tiki_data/books_data.csv")
    print(f"First book: {texts[0]} with ID: {ids[0]}")