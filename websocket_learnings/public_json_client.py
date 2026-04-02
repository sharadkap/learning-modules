import asyncio
import websockets
import json
from datetime import datetime

async def test_json_echo():
    uri = "wss://echo.websocket.org"
    
    print(f"Connecting to {uri} for JSON testing...")
    
    try:
        async with websockets.connect(uri) as websocket:
            # 1. Define a structured JSON message (Music related)
            payload = {
                "event": "LIKE_TRACK",
                "data": {
                    "track_id": "track_99",
                    "user_id": "user_456",
                    "timestamp": datetime.now().isoformat()
                },
                "metadata": {
                    "client": "python-websocket-client",
                    "version": "1.0.0"
                }
            }
            
            # 2. Convert dictionary to JSON string
            json_string = json.dumps(payload)
            print(f"\n📤 Sending JSON Payload:\n{json.dumps(payload, indent=2)}")
            
            # 3. Send to server
            await websocket.send(json_string)
            
            # 4. Listen for the echo
            print("\n📡 Waiting for echo (skipping welcome messages)...")
            async for response in websocket:
                print(f"📥 Received: {response}")
                
                # Check if this is our JSON
                try:
                    received_data = json.loads(response)
                    if "event" in received_data:
                        print(f"\n✅ Found JSON Payload!")
                        print(f"Parsed Event: {received_data['event']}")
                        print(f"Track Liked: {received_data['data']['track_id']}")
                        break # Exit loop after finding our data
                except json.JSONDecodeError:
                    # Ignore non-JSON messages (like "Request served by...")
                    continue

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_json_echo())
