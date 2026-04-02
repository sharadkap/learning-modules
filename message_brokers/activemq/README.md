# Apache ActiveMQ Learning (JMS Patterns)

Apache ActiveMQ is a popular open-source, multi-protocol, Java-based message broker. It supports industry-standard protocols like OpenWire, STOMP, MQTT, and AMQP.

## Key Concepts (JMS Terminology)
In the Java world (JCA/JMS), we talk about **Destinations**:
1.  **Queues (Point-to-Point)**: A message goes to **exactly one** consumer. If multiple consumers are listening, ActiveMQ load-balances the messages.
2.  **Topics (Publish/Subscribe)**: A message is broadcast to **all** active subscribers.

## Messaging Patterns Covered

### 1. Point-to-Point (Queues)
*   **Producer**: `queue_producer.py`
*   **Consumer**: `queue_consumer.py`
*   **Behavior**: FIFO order. Perfect for distributed tasks.

### 2. Publish/Subscribe (Topics)
*   **Producer**: `topic_producer.py`
*   **Consumer**: `topic_consumer.py`
*   **Behavior**: Broadcast. All active listeners get the message.

### 3. Message Selectors (SQL-like Filtering)
*   **Pattern**: Unlike RabbitMQ routing keys, ActiveMQ allows you to filter messages using **SQL syntax** on the headers.
*   **Example**: `priority > 5 AND region = 'US'`.
*   **Implementation**: `selector_producer.py` and `selector_consumer.py`.

### 4. Virtual Topics (The "Hybrid" Pattern)
*   **Problem**: In an interview, ask: "What if a Topic subscriber goes down?" (They lose messages).
*   **Solution**: Virtual Topics allow you to broadcast like a Topic, but receive using a **Queue**. This gives you the broadcast power of a Topic with the durability and load-balancing of a Queue.
*   **Path**: `/topic/VirtualTopic.Orders` -> `/queue/Consumer.[ClientA].VirtualTopic.Orders`.

### 5. Delayed/Scheduled Delivery
*   **Pattern**: ActiveMQ has a built-in scheduler. You can send a message now but tell the broker to hide it for 10 minutes.
*   **Use Case**: Retrying a failed payment after a cooling-off period.

### 6. Exclusive Consumers
*   **Pattern**: Ensures that only ONE consumer receives all messages from a queue, even if 10 are connected.
*   **Use Case**: When strict global ordering is required in a distributed system.

---

## Technical Details
*   **Protocol**: We are using **STOMP** (Simple Text Orientated Messaging Protocol) via the `stomp.py` library.
*   **Port**: `61613` (STOMP)
*   **Admin UI**: [http://localhost:8161](http://localhost:8161) (Credentials: `admin` / `admin`)

## How to Run:

### 1. Prerequisites (Virtual Environment)
Always ensure your virtual environment is activated before running the scripts.
```bash
# From the project root (/message_brokers)
source venv/bin/activate
# Navigate to this folder
cd activemq
```

### 2. Infrastructure
*   **Start ActiveMQ**: Ensure `docker-compose up -d` was run in the parent folder.
*   **Admin UI**: [http://localhost:8161](http://localhost:8161) (admin/admin).

### 3. Execution

#### A. Standard Queue (Point-to-Point)
1.  Tab 1: `python queue_consumer.py`
2.  Tab 2: `python queue_producer.py`

#### B. SQL-like Filtering (Message Selectors)
1.  Tab 1: `python selector_consumer.py` 
2.  Tab 2: `python selector_producer.py`
*   **Observation**: The consumer only receives "Classic Rock" and "Breaking News" because the SQL filter blocks low-priority or non-US messages.

#### C. Delayed Delivery
1.  Tab 1: `python queue_consumer.py` (Or just watch the Admin UI)
2.  Tab 2: `python delayed_producer.py`
*   **Observation**: You will see the producer finish, but the message won't "hit" the consumer/queue for exactly 5 seconds.
