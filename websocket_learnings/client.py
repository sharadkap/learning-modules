import asyncio
import websockets
import json

async def music_client():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        
        # 1. Send a preference to the server
        await websocket.send(json.dumps({"action": "subscribe", "genre": "Electronic"}))
        print("Sent subscription request...")

        # 2. Listen for incoming live updates
        print("Waiting for live song updates (Press Ctrl+C to stop)...\n")
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                if data["type"] == "SONG_CHANGE":
                    song = data["data"]
                    print(f"🎵 NOW PLAYING: {song['title']} by {song['artist']}")
        except websockets.exceptions.ConnectionClosed:
            print("Server closed the connection.")

if __name__ == "__main__":
    try:
        asyncio.run(music_client())
    except KeyboardInterrupt:
        print("\nClient stopped.")
