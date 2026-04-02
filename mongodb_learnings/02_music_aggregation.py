import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def run_music_analytics():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DB_NAME", "music_db")]
    tracks = db["tracks"]

    # Seed data for analytics if empty
    if tracks.count_documents({}) <= 1:
        tracks.insert_many([
            {"title": "Starboy", "artist": "The Weeknd", "genre": "Pop", "play_count": 1500, "year": 2016},
            {"title": "Blinding Lights", "artist": "The Weeknd", "genre": "Pop", "play_count": 3000, "year": 2019},
            {"title": "Level of Concern", "artist": "Twenty One Pilots", "genre": "Indie", "play_count": 800, "year": 2020},
            {"title": "Chlorine", "artist": "Twenty One Pilots", "genre": "Indie", "play_count": 1200, "year": 2018},
            {"title": "One More Time", "artist": "Daft Punk", "genre": "Electronic", "play_count": 5000, "year": 2000},
        ])

    # Interview Task: Find top genres by total play_count
    pipeline = [
        # 1. Filter tracks from 2000 onwards
        {"$match": {"year": {"$gte": 2000}}},
        
        # 2. Group by genre and sum plays
        {
            "$group": {
                "_id": "$genre",
                "total_plays": {"$sum": "$play_count"},
                "unique_artists": {"$addToSet": "$artist"},
                "avg_plays": {"$avg": "$play_count"}
            }
        },
        
        # 3. Add a field for artist count
        {"$addFields": {"artist_count": {"$size": "$unique_artists"}}},
        
        # 4. Sort by most played
        {"$sort": {"total_plays": -1}},
        
        # 5. Clean up output
        {"$project": {"_id": 0, "genre": "$_id", "total_plays": 1, "artist_count": 1}}
    ]

    print("--- Top Music Genres by Play Count ---")
    results = list(tracks.aggregate(pipeline))
    for res in results:
        print(f"Genre: {res['genre']} | Plays: {res['total_plays']} | Artists: {res['artist_count']}")

if __name__ == "__main__":
    run_music_analytics()
