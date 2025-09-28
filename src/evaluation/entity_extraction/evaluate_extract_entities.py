import xml.etree.ElementTree as ET
import pandas as pd

# Define entities (lowercase)
ENTITY_MAPPING = {
    "book": "Name",
    "link": "Link",
    "price": "Price (vnd)",
    "discount": "Discount (%)",
    "sold quantity": "Sold",
    "rating": "Rating",
    "publisher": "Publisher",
    "manufacturer": "Manufacturer",
    "author": "Authors"
}

# Normalize values
def normalize_value(value):
    value = str(value).strip().lower()
    value = value.replace(",", ".")  # Standardize decimal notation
    value = value.replace("%", "")   # Remove percentage symbol
    value = value.replace(" sao", "")  # Remove "sao" in rating
    return value

# Read data from Excel
def load_ground_truth(excel_file):
    df = pd.read_excel(excel_file)
    ground_truth = {}

    for entity_type, column_name in ENTITY_MAPPING.items():
        if column_name == "Authors":
            authors = df[column_name].apply(lambda x: eval(x) if isinstance(x, str) else [])            
            # Add other delimiters
            ground_truth[entity_type] = [normalize_value(author) for sublist in authors for author in sublist]
        elif column_name == "Publisher":
            publishers = df[column_name].apply(lambda x: eval(x) if isinstance(x, str) else [])
            ground_truth[entity_type] = [normalize_value(publisher) for sublist in publishers for publisher in sublist]
        elif column_name == "Manufacturer":
            manufacturers = df[column_name].apply(lambda x: eval(x) if isinstance(x, str) else [])
            ground_truth[entity_type] = [normalize_value(manufacturer) for sublist in manufacturers for manufacturer in sublist]
        elif column_name == "Price (vnd)":
            ground_truth[entity_type] = [f"{normalize_value(price)} vnd" for price in df[column_name]]
        elif column_name == "Rating":
            ground_truth[entity_type] = [f"{normalize_value(rating)}" for rating in df[column_name]]
        else:
            ground_truth[entity_type] = [normalize_value(str(x)) for x in df[column_name]]
    
    return ground_truth

# Read data from .graphml
def load_graphml_data(graphml_file):
    tree = ET.parse(graphml_file)
    root = tree.getroot()
    namespaces = {'ns': 'http://graphml.graphdrawing.org/xmlns'}
    return root, namespaces

# Evaluation
def evaluate_entities(root, namespaces, ground_truth):
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    # Iterate through nodes in .graphml
    for node in root.findall(".//ns:node", namespaces):
        entity_id = normalize_value(node.get("id").strip('"'))
        entity_type = normalize_value(node.find("./ns:data[@key='d0']", namespaces).text.strip('"'))

        print(f"Entity ID: {entity_id}, Entity Type: {entity_type}")  # Debug

        # Check entity_type
        if entity_type in ground_truth:
            # Check entity_id
            if entity_id in ground_truth[entity_type]:
                true_positives += 1
                # print(f"True Positive: {entity_id} ({entity_type})")  # Debug
            else:
                false_positives += 1
                print(f"False Positive: '{entity_id}' ({entity_type})")  # Debug
        else:
            false_positives += 1
            print(f"False Positive (Invalid Entity Type): {entity_id} ({entity_type})")  # Debug

    # Calculate false negatives
    for entity_type, entities in ground_truth.items():
        for entity in entities:
            found = False
            for node in root.findall(".//ns:node", namespaces):
                node_entity_id = normalize_value(node.get("id").strip('"'))
                node_entity_type = normalize_value(node.find("./ns:data[@key='d0']", namespaces).text.strip('"'))
                if node_entity_type == entity_type and node_entity_id == entity:
                    found = True
                    break
            if not found:
                false_negatives += 1

    # Compute metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives
    }

# Main function
def main():
    excel_file = "./data/tiki_books_vn.xlsx"
    graphml_file = "./dickens_ollama/graph_chunk_entity_relation.graphml"

    ground_truth = load_ground_truth(excel_file)
    root, namespaces = load_graphml_data(graphml_file)
    results = evaluate_entities(root, namespaces, ground_truth)

    print(f"Precision: {results['precision']:.2f}")
    print(f"Recall: {results['recall']:.2f}")
    print(f"F1-Score: {results['f1_score']:.2f}")
    print(f"True Positives: {results['true_positives']}")
    print(f"False Positives: {results['false_positives']}")
    print(f"False Negatives: {results['false_negatives']}")

if __name__ == "__main__":
    main()