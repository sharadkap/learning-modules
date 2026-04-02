import asyncio
import websockets

async def test_public_echo():
    # A widely used public WebSocket echo server
    uri = "wss://echo.websocket.org"
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Type a message to send (or 'exit' to quit):")
            
            while True:
                # Get user input in an async-friendly way
                message = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
                
                if message.lower() == 'exit':
                    break
                
                # Send message to public server
                await websocket.send(message)
                print(f"Sent: {message}")
                
                # Receive echo back
                response = await websocket.recv()
                print(f"Received from Public Server: {response}")
                
    except Exception as e:
        print(f"Connection failed: {e}")
        print("\nTip: If wss://echo.websocket.org is down, try wss://ws.postman-echo.com/raw")

if __name__ == "__main__":
    try:
        asyncio.run(test_public_echo())
    except KeyboardInterrupt:
        print("\nClient closed.")
