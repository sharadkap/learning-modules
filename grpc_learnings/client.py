import grpc
import time

# Import generated gRPC code
# These modules provide the typed Message classes and the Service Stub
import protos.messenger_pb2 as pb2
import protos.messenger_pb2_grpc as pb2_grpc

def run_unary(stub):
    """
    1. UNARY: Basic Request-Response
    - WHY: Demonstrates the simplest RPC lifecycle where the client waits for a 
           single response before proceeding.
    - HOW: Instantiates a StatusRequest object. The Stub handles the serialization 
           and transport over the HTTP/2 connection.
    """
    print("--- Unary Request ---")
    response = stub.GetLearningStatus(pb2.StatusRequest(user_id="researcher-01"))
    print(f"Server Response: {response.message} (Active: {response.active})")

def run_server_streaming(stub):
    """
    2. SERVER STREAMING: Single request, stream of responses
    - WHY: Optimal for real-time updates where the client consumes a persistent push of data.
    - HOW: The Stub returns a generator-like iterator. The client consumes this via a 
           standard 'for' loop, reacting to each binary DATA frame as it arrives.
    """
    print("\n--- Server Streaming (Real-time updates) ---")
    responses = stub.StreamLearnings(pb2.TopicRequest(topic="gRPC Protocols"))
    for update in responses:
        print(f"[{update.timestamp}] Progress {update.progress}%: {update.content}")

def run_client_streaming(stub):
    """
    3. CLIENT STREAMING: Multiple requests, single final response
    - WHY: Used for asynchronous 'Sharded Uploads' where the client pushes fragments 
           over time without loading the entire dataset into local memory.
    - HOW: We pass a generator function (generate_notes) to the Stub call. This 
           facilitates a 'lazy upload' over the persistent TCP pipe.
    """
    print("\n--- Client Streaming (Uploading research notes) ---")

    def generate_notes():
        notes = [
            "Note 1: gRPC uses HTTP/2 Multiplexing", 
            "Note 2: Built on Protocol Buffers", 
            "Note 3: Binary TLV serialization", 
            "Note 4: Typed interface contracts"
        ]
        for note in notes:
            # LATENCY SIMULATION: Simulating a human user or slow-moving data source
            time.sleep(1)
            yield pb2.ResearchNote(text=note)

    response = stub.SubmitResearchNotes(generate_notes())
    print(f"Server Summary: {response.final_summary} (Total {response.count})")

def run_bidirectional_streaming(stub):
    """
    4. BI-DIRECTIONAL STREAMING: Continuous shared flow
    - WHY: The pinnacle of full-duplex communication. Ideal for real-time interaction.
    - HOW: The client consumes the 'response_stream' iterator in a non-blocking loop 
           while its outgoing 'make_feed_requests' generator remains active.
    """
    print("\n--- Bi-directional Streaming (Collaborative Feed) ---")

    def make_feed_requests():
        updates = [
            ("Engineer", "Initializing system..."), 
            ("Lead", "Monitoring data flow..."), 
            ("QA", "Verifying latency...")
        ]
        for user, msg in updates:
            # Continuous outgoing stream
            time.sleep(1)
            yield pb2.FeedUpdate(user=user, message=msg)

    # Initializing the persistent pipe
    response_stream = stub.CollaborativeFeed(make_feed_requests())
    for resp in response_stream:
        # Reacting to server echoes in real-time
        print(f"   [Feed Update] {resp.user}: {resp.message}")

if __name__ == '__main__':
    """
    STUB PATTERN: The LearningMessengerStub is our local proxy for the remote server. 
    It abstracts all network framing, HTTP/2 flow control, and service discovery 
    behind simple Python method calls.
    """
    # Connect to the orchestrator via a persistent HTTP/2 channel
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = pb2_grpc.LearningMessengerStub(channel)

        # Execute the multi-modal driver suite
        run_unary(stub)
        run_server_streaming(stub)
        run_client_streaming(stub)
        run_bidirectional_streaming(stub)
