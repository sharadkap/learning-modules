import asyncio
import websockets
import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# 1. Setup Environment and MongoDB
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "music_db")

# Global variables
connected_clients = set()

def get_mongo_collection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db["activity_logs"]

# Initialize collection
activity_logs = get_mongo_collection()

async def handle_client(websocket):
    # Register client
    connected_clients.add(websocket)
    print(f"✅ New connection. Active listeners: {len(connected_clients)}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Check for "LIKE" events
                if data.get("type") == "LIKE":
                    track_id = data.get("track_id", "unknown")
                    user_id = data.get("user_id", "guest")
                    
                    print(f"📩 Received LIKE for {track_id} from {user_id}")
                    
                    # 2. PERSIST TO MONGODB
                    log_entry = {
                        "event": "LIKE",
                        "track_id": track_id,
                        "user_id": user_id,
                        "timestamp": datetime.now()
                    }
                    result = activity_logs.insert_one(log_entry)
                    print(f"💾 Saved to MongoDB index: {result.inserted_id}")
                    
                    # 3. BROADCAST TO OTHERS
                    broadcast_msg = json.dumps({
                        "type": "NOTIFICATION",
                        "message": f"🔥 Someone just liked {track_id}!",
                        "total_likes_saved": activity_logs.count_documents({"track_id": track_id})
                    })
                    
                    # Send to everyone else
                    if connected_clients:
                        await asyncio.gather(
                            *[client.send(broadcast_msg) for client in connected_clients],
                            return_exceptions=True
                        )
                
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid JSON format"}))
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"❌ Connection closed. Active listeners: {len(connected_clients)}")

async def main():
    print(f"🚀 Integrated WebSocket + MongoDB Server running on ws://localhost:8765")
    print(f"📂 Logging events to MongoDB database: {DB_NAME}")
    
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping server...")
