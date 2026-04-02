import asyncio
import websockets
import json
import random

async def simulate_likes():
    uri = "ws://localhost:8765"
    tracks = ["Starboy", "Midnight City", "Blinding Lights", "Chlorine"]
    user_id = f"user_{random.randint(100, 999)}"
    
    print(f"Connecting as {user_id}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            # Function to listen for broadcasts
            async def listen():
                try:
                    while True:
                        msg = await websocket.recv()
                        data = json.loads(msg)
                        if data["type"] == "NOTIFICATION":
                            print(f"\n📢 SERVER BROADCAST: {data['message']}")
                            print(f"📊 Global stats for this track: {data['total_likes_saved']} likes")
                except:
                    pass

            # Start listening in background
            listener_task = asyncio.create_task(listen())

            # Simulate sending 3 likes over a few seconds
            for _ in range(3):
                await asyncio.sleep(random.randint(2, 5))
                track = random.choice(tracks)
                
                payload = {
                    "type": "LIKE",
                    "track_id": track,
                    "user_id": user_id
                }
                
                print(f"\n👆 Clicking LIKE for '{track}'...")
                await websocket.send(json.dumps(payload))
            
            print("\nFinished sending likes. Waiting 5s for final broadcasts...")
            await asyncio.sleep(5)
            listener_task.cancel()

    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_likes())
