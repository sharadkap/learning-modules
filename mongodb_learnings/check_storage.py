import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def check_usage():
    client = MongoClient(os.getenv("MONGO_URI"))
    print("--- Database Storage Usage ---")
    try:
        # Get list of databases and their sizes
        db_info = client.admin.command("listDatabases")
        for db in db_info['databases']:
            size_mb = db['sizeOnDisk'] / (1024 * 1024)
            print(f"Database: {db['name']} | Size: {size_mb:.2f} MB")
            
        print(f"\nTotal Size on Disk: {db_info['totalSize'] / (1024 * 1024):.2f} MB")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_usage()
