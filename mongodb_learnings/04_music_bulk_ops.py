import os
import time
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

load_dotenv()

def sync_trending_scores():
    """
    Imagine we calculate 'trending scores' in a Python service 
    and need to update 1000s of tracks at once.
    """
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DB_NAME", "music_db")]
    tracks = db["tracks"]
    
    # Mock data: A list of updates from an external API
    external_updates = [
        {"isrc": "US-S1Z-11-00001", "score": 98.5},
        {"isrc": "US-WB1-16-00123", "score": 85.2},
        {"isrc": "GB-AHT-20-00456", "score": 77.0},
    ]
    
    # Bulk preparation
    operations = []
    for update in external_updates:
        operations.append(
            UpdateOne(
                {"isrc": update["isrc"]},
                {"$set": {"trending_score": update["score"], "last_sync": time.time()}},
                upsert=True
            )
        )
    
    if operations:
        print(f"Syncing {len(operations)} trending scores in ONE network request...")
        result = tracks.bulk_write(operations)
        print(f"✓ Bulk Sync Complete: {result.upserted_count} new, {result.modified_count} updated.")

if __name__ == "__main__":
    sync_trending_scores()
