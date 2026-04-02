import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def music_modeling_demo():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DB_NAME", "music_db")]
    
    # CASE 1: EMBEDDING (The "Album" pattern)
    # Tracks usually don't exist without an album, and albums have a fixed number of tracks.
    # This is perfect for embedding.
    album = {
        "title": "Random Access Memories",
        "artist": "Daft Punk",
        "release_year": 2013,
        "tracks": [
            {"track_no": 1, "title": "Give Life Back to Music", "duration": 274},
            {"track_no": 2, "title": "The Game of Love", "duration": 322},
            {"track_no": 3, "title": "Giorgio by Moroder", "duration": 544}
        ]
    }
    db.albums.insert_one(album)
    print("✓ Inserted Album with embedded tracks (Fast Reads!)")

    # CASE 2: REFERENCING (The "Playlist" pattern)
    # A playlist can have thousands of tracks, and tracks belong to many playlists.
    # We reference the track IDs instead of embedding the whole song data.
    
    # Let's assume we have track IDs from a central collection
    track_ids = [db.tracks.find_one()["_id"]] 
    
    playlist = {
        "name": "Summer Vibes 2024",
        "user_id": "user_123",
        "track_ids": track_ids # Only storing foreign keys
    }
    db.playlists.insert_one(playlist)
    print("✓ Created Playlist with track references (Avoids duplication)")

    # Join tracks into the playlist using $lookup
    pipeline = [
        {"$match": {"name": "Summer Vibes 2024"}},
        {
            "$lookup": {
                "from": "tracks",
                "localField": "track_ids",
                "foreignField": "_id",
                "as": "track_details"
            }
        }
    ]
    playlist_full = list(db.playlists.aggregate(pipeline))[0]
    print(f"✓ Expanded playlist '{playlist_full['name']}' using $lookup")

if __name__ == "__main__":
    music_modeling_demo()
