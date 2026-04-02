import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "music_db")

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def setup_library():
    db = get_db()
    tracks = db["tracks"]
    
    try:
        # 1. Indexing: Unique ID for tracks (ISRC is the industry standard)
        tracks.create_index([("isrc", ASCENDING)], unique=True)
        # Index for fast searching by name/artist
        tracks.create_index([("artist", ASCENDING), ("title", ASCENDING)])
        print("✓ Indices verified/created")
    except Exception as e:
        print(f"⚠️ Note: Indices could not be created (likely disk space), but we'll continue: {e}")
        
    return tracks

def track_management(tracks):
    # CREATE: A new hit song
    song = {
        "title": "Midnight City",
        "artist": "M83",
        "genre": "Synthwave",
        "isrc": "US-S1Z-11-00001",
        "duration_sec": 243,
        "play_count": 0,
        "tags": ["electronic", "80s-vibe", "anthemic"]
    }
    
    try:
        tracks.insert_one(song)
        print(f"✓ Added track: {song['title']} by {song['artist']}")
    except Exception as e:
        print(f"✗ Failed to add track (likely duplicate ISRC): {e}")

    # UPDATE: Increment play count (Atomic)
    # Tip: Use $inc for high-frequency updates like "plays" or "likes"
    tracks.update_one(
        {"isrc": "US-S1Z-11-00001"},
        {"$inc": {"play_count": 1}, "$set": {"last_played_at": "2024-03-23T10:00:00Z"}}
    )
    print("✓ Track play count incremented atomically")

if __name__ == "__main__":
    if not MONGO_URI:
        print("Please set MONGO_URI in .env")
    else:
        tracks_coll = setup_library()
        track_management(tracks_coll)
