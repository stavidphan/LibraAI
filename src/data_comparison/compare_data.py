import pandas as pd
from tabulate import tabulate
import time

def detect_changes(old_file, new_file):
    print("\n\n\n🕷️ START compare data...\n")
    start_time = time.time()
    df_old = pd.read_csv(old_file).drop_duplicates(subset=['id']).set_index('id')
    df_new = pd.read_csv(new_file).drop_duplicates(subset=['id']).set_index('id')
    added_ids = df_new.index.difference(df_old.index)
    common_ids = df_old.index.intersection(df_new.index)
    changed_ids = []
    changed_details = {}
    for id in common_ids:
        old_row = df_old.loc[id]
        new_row = df_new.loc[id]
        if not old_row.equals(new_row):
            changed_ids.append(id)
            changes = {col: f"{old_row[col]} → {new_row[col]}" 
                      for col in df_old.columns 
                      if old_row[col] != new_row[col]}
            changed_details[id] = changes
        
    print(f"\n📌 Total new books added: {len(added_ids)}")
    print(f"📌 Total books with changed information: {len(changed_ids)}")
    
    if not added_ids.any() and not changed_ids:
        print("\n⚡ No new or changed books detected. Skipping save.\n")
        return None
    
    # Display the changes in console
    # table_data = []
    # for id in added_ids:
    #     name = df_new.loc[id, 'name']
    #     table_data.append([id, name, 'Added', 'N/A'])
    # for id in changed_ids:
    #     name = df_new.loc[id, 'name']
    #     changes_str = ', '.join([f"{col}: {changed_details[id][col]}" 
    #                            for col in changed_details[id]])
    #     table_data.append([id, name, 'Changed', changes_str])
    
    # if table_data:
    #     print(tabulate(table_data, headers=["ID", "Name", "Status", "Change Details"], tablefmt="fancy_grid"))
    # else:
    #     print("No new or changed books")
        
    all_updated_books = df_new.loc[added_ids.union(changed_ids)]
    temp_output = "temp_changes.csv"
    all_updated_books.reset_index().to_csv(temp_output, index=False)

    print("\n✅ Temp change report generated.\n")
    end_time = time.time()
    print("🕷️ END compare data\n")
    print(f"⏱️ Execution time: {(end_time - start_time):.2f} seconds\n")

    return temp_output 

if __name__ == "__main__":
    detect_changes("./data/compare/books_data_old.csv", 
                  "./data/compare/books_data_new.csv", 
                  "./data/compare/books_update_report.csv")