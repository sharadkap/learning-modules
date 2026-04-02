import grpc
from concurrent import futures
import time

# Generated gRPC code
# These modules handle the low-level binary framing and marshalling
import protos.messenger_pb2 as pb2
import protos.messenger_pb2_grpc as pb2_grpc

class LearningMessengerServicer(pb2_grpc.LearningMessengerServicer):
    """
    ARCHITECTURE NOTE: The Servicer is the backend heart of the gRPC system.
    It inherits from the generated base class to implement the actual application logic
    behind the strictly-typed Service Contract.
    """

    def GetLearningStatus(self, request, context):
        """
        1. UNARY: Basic Request-Response
        - WHY: Used as the primary system-readiness handshake in microservice health checks.
        - WHAT: Receives a single StatusRequest frame.
        - HOW: Returns a static StatusResponse, providing a definitive liveness probe for the client.
        """
        print(f"📡 Unary Request from: {request.user_id}")
        return pb2.StatusResponse(
            message=f"System ready for research. Status check OK.",
            active=True
        )

    def StreamLearnings(self, request, context):
        """
        2. SERVER STREAMING: Single request, multiple responses pushed to client
        - WHY: Crucial for real-time telemetry where the client shouldn't have to poll for updates.
        - WHAT: The server initiates a 'push' of multiple data frames over a single TCP connection.
        - HOW: Utilizing the Python 'yield' pattern allows the server to fire individual binary DATA 
               frames frame-by-frame, ensuring the entire response is never held in memory at once.
        """
        topic = request.topic
        print(f"📡 Server Streaming topic: {topic}")

        updates = [
            f"Searching for research papers on {topic}...",
            f"Analyzing core principles of {topic}...",
            f"Synthesizing key gRPC use cases...",
            "Finalizing the consolidated report."
        ]

        for i, update in enumerate(updates):
            # Simulated real-time latency
            time.sleep(1)
            yield pb2.LearningUpdate(
                content=update,
                progress=(i + 1) * 25,
                timestamp=time.strftime("%H:%M:%S")
            )

    def SubmitResearchNotes(self, request_iterator, context):
        """
        3. CLIENT STREAMING: Client sends stream, server responds with summary at end
        - WHY: Optimized for 'Sharded Uploads' (e.g. logs or large files) to circumvent 
               HTTP/2 frame limits on single requests.
        - WHAT: The server continuously listens to the client's fragments.
        - HOW: Drains the inbound 'request_iterator' using a for-loop, performing 
               logic only after the caller closes the stream.
        """
        print("📡 Receiving stream of research notes...")
        count = 0
        notes = []

        for note in request_iterator:
            count += 1
            notes.append(note.text)
            print(f"   - Received fragment {count}: {note.text[:20]}...")

        return pb2.SummaryResponse(
            count=count,
            final_summary=f"Processed {count} notes. Key takeaway: {notes[-1] if notes else 'None'}"
        )

    def CollaborativeFeed(self, request_iterator, context):
        """
        4. BI-DIRECTIONAL STREAMING: Continuous shared flow between both client and server
        - WHY: The pinnacle of gRPC. Ideal for chat, collaborative editors, or control signals.
        - WHAT: Both partners simultaneously read and write to the same persistent stream.
        - HOW: The server concurrently pulls updates from the client's 'request_iterator' while 
               yielding responses back over the same persistent HTTP/2 connection.
        """
        print("📡 Bi-directional 'Collaborative Feed' opened.")

        for feed_update in request_iterator:
            print(f"   [Feed] From {feed_update.user}: {feed_update.message}")

            # FULL-DUPLEX ECHO: Immediate real-time response to received data
            yield pb2.FeedUpdate(
                user="System",
                message=f"Acknowledged {feed_update.user}'s update: {feed_update.message}"
            )

def serve():
    """
    - CONCURRENCY: We utilize ThreadPoolExecutor because gRPC relies on persistent HTTP/2 pipes. 
      A thread pool ensures long-lived streaming calls do not block other clients.
    - MULTIPLEXING: All patterns are registered on the same port (50051) using the 
      Multiplexing capabilities of HTTP/2.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_LearningMessengerServicer_to_server(
        LearningMessengerServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    print("🚀 gRPC server logic running on port 50051...")
    server.start()
    try:
        while True:
            time.sleep(86400) # Maintain daemon state
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
