import pandas as pd
from typing import Dict, Any

def create_custom_kg_for_batch(csv_file, batch_size: int = 100) -> list[Dict[str, Any]]:

    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print("File not found.")
        return [], []
    
    custom_kgs = []
    
    for start_idx in range(0, len(df), batch_size):
        batch_df = df.iloc[start_idx:start_idx + batch_size]
        custom_kg = {
            "chunks": [],
            "entities": [],
            "relationships": []
        }

        for index, row in batch_df.iterrows():
            book_data = row.to_dict()
            # Convert all values to strings and handle NaN
            book_data = {k: str(v) if pd.notna(v) else "" for k, v in book_data.items()}
            source_id = f"book-{book_data['id']}"
            book_name = book_data["name"]

            # Create chunk content (keep as before)
            chunk_content = (
                f"Book Name: {book_data['name']}\n"
                f"Author: {book_data['authors']}\n"
                f"Publisher: {book_data['manufacturer']}\n"
                f"Category: {book_data['category']}\n"
                f"Seller: {book_data['seller_name']}\n"
                f"Link: {book_data['link']}\n"
                f"Current Price: {book_data['current_price']} VND\n"
                f"Original Price: {book_data['original_price']} VND\n"
                f"Discount Rate: {book_data['discount_rate']}%\n"
                f"Rating: {book_data['rating_average']} stars\n"
                f"Quantity Sold: {book_data['quantity_sold']}\n"
                f"Description: {book_data['short_description']}"
            )

            custom_kg["chunks"].append({
                "content": chunk_content,
                "source_id": source_id
            })

            # Create entities for each column
            entities = [
                {
                    "entity_name": book_name,
                    "entity_type": "Book Name",
                    "description": f"The book '{book_name}', a published work categorized under '{book_data['category']}' with specific attributes like price, sales, and rating.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["authors"],
                    "entity_type": "Author",
                    "description": f"The author '{book_data['authors']}' who wrote the book '{book_name}'.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["seller_name"],
                    "entity_type": "Seller Name",
                    "description": f"The seller '{book_data['seller_name']}' offering the book '{book_name}' for purchase.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["manufacturer"],
                    "entity_type": "Manufacturer",
                    "description": f"The manufacturer '{book_data['manufacturer']}' responsible for publishing the book '{book_name}'.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["current_price"],
                    "entity_type": "Current Price",
                    "description": f"The Current Price of the book '{book_name}', set at {book_data['current_price']}.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["original_price"],
                    "entity_type": "Original Price",
                    "description": f"The Original Price of the book '{book_name}', set at {book_data['original_price']}.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["discount_rate"],
                    "entity_type": "Discount",
                    "description": f"The Discount of the book '{book_name}', set at {book_data['discount_rate']}.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["quantity_sold"],
                    "entity_type": "Sold Quantity",
                    "description": f"The Sold Quantity of the book '{book_name}', set at {book_data['quantity_sold']}.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["rating_average"],
                    "entity_type": "Rating",
                    "description": f"The Rating of the book '{book_name}', set at {book_data['rating_average']}.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["category"],
                    "entity_type": "Category",
                    "description": f"The book '{book_name}' belongs to the '{book_data['category']}' genre.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["link"],
                    "entity_type": "Link",
                    "description": f"The Link of the book '{book_name}', set at {book_data['link']}.",
                    "source_id": source_id
                },
                {
                    "entity_name": book_data["short_description"],
                    "entity_type": "Description",
                    "description": f"Summary of the book '{book_name}': {book_data['short_description']}.",
                    "source_id": source_id
                }
            ]
            custom_kg["entities"].extend(entities)

            # Create relationships between Book Name and other entities
            relationships = [
                {
                    "src_id": book_name,
                    "tgt_id": book_data["authors"],
                    "description": f"The book '{book_name}' was written by '{book_data['authors']}'.",
                    "keywords": "authorship",
                    "weight": 1.0,
                    "source_id": source_id
                },
                {
                    "src_id": book_name,
                    "tgt_id": book_data["seller_name"],
                    "description": f"The book '{book_name}' is sold by '{book_data['seller_name']}'.",
                    "keywords": "sold by",
                    "weight": 1.0,
                    "source_id": source_id
                },
                {
                    "src_id": book_name,
                    "tgt_id": book_data["manufacturer"],
                    "description": f"The book '{book_name}' was published by '{book_data['manufacturer']}'.",
                    "keywords": "published by",
                    "weight": 1.0,
                    "source_id": source_id
                },
                {
                    "src_id": book_name,
                    "tgt_id": book_data["current_price"],
                    "description": f"The book '{book_name}' is currently priced at '{book_data['current_price']}'.",
                    "keywords": "has price",
                    "weight": 1.0,
                    "source_id": source_id
                },
                {
                    "src_id": book_name,
                    "tgt_id": book_data["original_price"],
                    "description": f"The book '{book_name}' originally cost '{book_data['original_price']}'.",
                    "keywords": "originally priced",
                    "weight": 1.0,
                    "source_id": source_id
                },
                {
                    "src_id": book_name,
                    "tgt_id": book_data["discount_rate"],
                    "description": f"The book '{book_name}' is available at a '{book_data['discount_rate']}' discount.",
                    "keywords": "has discount",
                    "weight": 1.0,
                    "source_id": source_id
                },
                {
                    "src_id": book_name,
                    "tgt_id": book_data["quantity_sold"],
                    "description": f"The book '{book_name}' has sold '{book_data['quantity_sold']}' copies.",
                    "keywords": "has sold quantity",
                    "weight": 1.0,
                    "source_id": source_id
                },
                {
                    "src_id": book_name,
                    "tgt_id": book_data["rating_average"],
                    "description": f"The book '{book_name}' has a rating of '{book_data['rating_average']}'.",
                    "keywords": "has rating",
                    "weight": 1.0,
                    "source_id": source_id
                },
                {
                    "src_id": book_name,
                    "tgt_id": book_data["category"],
                    "description": f"The book '{book_name}' falls under the '{book_data['category']}' genre.",
                    "keywords": "belongs to category",
                    "weight": 1.0,
                    "source_id": source_id
                },
                {
                    "src_id": book_name,
                    "tgt_id": book_data["link"],
                    "description": f"The book '{book_name}' is available at '{book_data['link']}'.",
                    "keywords": "has link",
                    "weight": 1.0,
                    "source_id": source_id
                },
                {
                    "src_id": book_name,
                    "tgt_id": book_data["short_description"],
                    "description": f"The book '{book_name}' summary: '{book_data['short_description']}'.",
                    "keywords": "has description",
                    "weight": 1.0,
                    "source_id": source_id
                }
            ]
            custom_kg["relationships"].extend(relationships)
        
        custom_kgs.append(custom_kg)
    
    return custom_kgs, df