import os
from pymongo import MongoClient, ASCENDING, TEXT
from dotenv import load_dotenv

# Load credentials
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "music_db")

def setup_database():
    if not MONGO_URI:
        print("❌ Error: MONGO_URI not found in .env file.")
        return

    print(f"🚀 Initializing Database: {DB_NAME}")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # --- 1. TRACKS COLLECTION ---
    print("\nSetting up 'tracks' collection...")
    tracks = db["tracks"]
    
    try:
        # Unique Index (ISRC)
        tracks.create_index([("isrc", ASCENDING)], unique=True)
        # Compound Index
        tracks.create_index([("artist", ASCENDING), ("title", ASCENDING)])
        # Text Index
        tracks.create_index([("title", TEXT), ("genre", TEXT)])
        print("✅ 'tracks' indices created")
    except Exception as e:
        print(f"⚠️ Warning: Could not create indices (likely disk space): {e}")
        print("Continuing with data seeding anyway...")

    # --- 2. ALBUMS COLLECTION ---
    print("\nSetting up 'albums' collection...")
    albums = db["albums"]
    try:
        albums.create_index([("artist", ASCENDING), ("release_year", ASCENDING)])
        print("✅ 'albums' index created")
    except:
        pass

    # --- 3. PLAYLISTS COLLECTION ---
    print("\nSetting up 'playlists' collection...")
    playlists = db["playlists"]
    try:
        playlists.create_index([("user_id", ASCENDING)])
        print("✅ 'playlists' index created")
    except:
        pass

    # --- 4. SEEDING INITIAL DATA (Optional) ---
    print("\nSeeding initial data...")
    if tracks.count_documents({}) == 0:
        sample_tracks = [
            {"title": "Starboy", "artist": "The Weeknd", "genre": "Pop", "play_count": 1500, "year": 2016, "isrc": "US-UMG-16-00001"},
            {"title": "Blinding Lights", "artist": "The Weeknd", "genre": "Pop", "play_count": 3000, "year": 2019, "isrc": "US-UMG-19-00002"},
            {"title": "Level of Concern", "artist": "Twenty One Pilots", "genre": "Indie", "play_count": 800, "year": 2020, "isrc": "US-FUE-20-00003"}
        ]
        tracks.insert_many(sample_tracks)
        print(f"✅ Preview data inserted: {len(sample_tracks)} tracks")
    else:
        print("ℹ️ Data already exists, skipping seed.")

    print(f"\n✨ Database '{DB_NAME}' is ready for your interview prep!")
    client.close()

if __name__ == "__main__":
    setup_database()
