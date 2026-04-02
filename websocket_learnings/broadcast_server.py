import asyncio
import websockets
import json
import random

# Track all connected clients
connected_clients = set()

async def broadcast_updates(websocket):
    # Register client
    connected_clients.add(websocket)
    print(f"Listener joined. Total listeners: {len(connected_clients)}")
    
    try:
        # Keep the connection open
        async for message in websocket:
            # If client sends something, we can handle it
            data = json.loads(message)
            print(f"Received request from client: {data}")
    except Exception:
        pass
    finally:
        # Unregister client
        connected_clients.remove(websocket)
        print(f"Listener left. Total listeners: {len(connected_clients)}")

async def simulate_song_changes():
    """Simulate a radio station changing songs every few seconds"""
    songs = [
        {"title": "Starboy", "artist": "The Weeknd"},
        {"title": "Midnight City", "artist": "M83"},
        {"title": "Blinding Lights", "artist": "The Weeknd"},
        {"title": "Chlorine", "artist": "Twenty One Pilots"}
    ]
    
    while True:
        if connected_clients:
            new_song = random.choice(songs)
            payload = json.dumps({
                "type": "SONG_CHANGE",
                "data": new_song,
                "timestamp": json.dumps(str(asyncio.get_event_loop().time()))
            })
            print(f"Broadcasting new song: {new_song['title']}")
            
            # Send to everyone!
            # Using asyncio.gather to send in parallel
            await asyncio.gather(
                *[client.send(payload) for client in connected_clients],
                return_exceptions=True
            )
        
        await asyncio.sleep(5) # Change song every 5 seconds

async def main():
    # Start the websocket server
    server = websockets.serve(broadcast_updates, "localhost", 8765)
    
    # Run the server and the simulator concurrently
    await asyncio.gather(server, simulate_song_changes())

if __name__ == "__main__":
    print("🚀 Music Live-Ticker Server started on ws://localhost:8765")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
