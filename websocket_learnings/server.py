import asyncio
import websockets

async def echo_handler(websocket):
    print(f"New client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Received: {message}")
            response = f"Server Echo: {message}"
            await websocket.send(response)
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")

async def main():
    # Start the server on localhost:8765
    async with websockets.serve(echo_handler, "localhost", 8765):
        print("🚀 Socket Server started on ws://localhost:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping server...")
