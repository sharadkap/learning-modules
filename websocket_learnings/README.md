# WebSocket Programming in Python

WebSockets provide a **full-duplex**, persistent connection between a client and a server. Unlike HTTP (Request-Response), WebSockets allow the server to push data to the client at any time.

## Key Concepts

1.  **Handshake**: WebSockets start as an HTTP request with an `Upgrade` header.
2.  **Stateful**: The server must keep track of all active connections.
3.  **Concurrency**: Because connections stay open, you MUST use asynchronous programming (`asyncio` in Python).
4.  **Scaling**: Scaling WebSockets is harder than HTTP because you can't just use a simple round-robin load balancer (clients need to stay connected to the _same_ server, or you need a Pub/Sub like Redis).

## Use Cases Covered

1.  **[server.py](./server.py)**: Basic Echo Server.
2.  **[broadcast_server.py](./broadcast_server.py)**: Music "Live Ticker" (Server-to-Client push).
3.  **[integrated_app.py](./integrated_app.py)**: Client sends data -> Server saves to **MongoDB** -> Server broadcasts to ALL clients.
4.  **[like_button_client.py](./like_button_client.py)**: Simulates a user liking a song and receiving real-time notifications.
5.  **[public_echo_client.py](./public_echo_client.py)**: Test against online servers.
6.  **[public_json_client.py](./public_json_client.py)**: Demonstrates how to send and parse structured **JSON data** over a WebSocket connection.

## Setup

1.  Navigate to this folder: `cd websocket_learnings`
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run the server in one terminal and the client in another.
