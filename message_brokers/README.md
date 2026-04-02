# Message Brokers vs. Event Streaming

## 1. RabbitMQ (The "Post Office")

- **Type**: Traditional Message Broker.
- **Logic**: Smart Broker, Dumb Consumer. The broker keeps track of who received what and deletes messages once they are acknowledged.
- **Best for**: Task queues, complex routing (using Exchanges), and guaranteed delivery is needed.
- **Interview Keyword**: **AMQP Protocol**, **Exchanges**, **Routing Keys**.

## 2. Apache Kafka (The "Log Book")

- **Type**: Distributed Event Streaming Platform.
- **Best for**: Big Data, Real-time Analytics, Log aggregation.
- **Interview Keyword**: **Append-only log**, **Partitions**, **Consumer Groups**.

## 3. Apache Pulsar (The "Unified Cloud-Native")

- **Type**: Multi-tenant, unified messaging and streaming.
- **Logic**: Decoupled Compute (Broker) and Storage (BookKeeper).
- **Best for**: Cloud-native apps, multi-tenancy, tiered storage (S3).
- **Interview Keyword**: **Decoupled Architecture**, **Tiered Storage**, **Unified Model**.

## 4. Apache RocketMQ (The "Business Consistency King")

- **Type**: Distributed messaging and streaming with a focus on transactions.
- **Logic**: High availability, strictly ordered, high throughput.
- **Best for**: E-commerce, Financial transactions, Distributed transactions.
- **Interview Keyword**: **Distributed Transactions**, **Strict Order**, **NameServer**.

## RabbitMQ Messaging Patterns (Interview Favorites)

### 1. FIFO (First-In-First-Out)

- **The Default**: RabbitMQ guarantees order within a single queue. The first message put in is the first one sent to a worker.

### 2. Point-to-Point (Work Queues)

- **Pattern**: One producer, many workers, but **only ONE worker** gets any single message.
- **Best for**: Heavy tasks (Encoding music, sending emails).
- **Implemented in**: `rabbitmq_producer.py` and `rabbitmq_consumer.py`.

### 3. Pub/Sub (Fanout)

- **Pattern**: One producer, many workers, and **EVERY worker** gets a copy of the message.
- **Best for**: Broadcasting notifications or configuration changes.
- **Implementation**: `rabbitmq_fanout_producer.py` and `rabbitmq_fanout_consumer.py`.

### 4. Routing (Direct)

- **Pattern**: Messages are sent to specific queues based on a **Routing Key**.
- **Example**: Sending `info` logs to one queue and `error` logs to a more urgent queue.
- **Implementation**: `rabbitmq_routing_producer.py`.

### 5. Topics (Advanced Pattern Matching)

- **Pattern**: Routes messages based on hierarchical keys and wildcards (`*`, `#`).
- **Implementation**: `rabbitmq_topic_producer.py` and `rabbitmq_topic_consumer.py`.

### 6. RPC (Remote Procedure Call)

- **Pattern**: Request-Reply. The client sends a request and waits for a response on a "callback" queue.
- **Best for**: Offloading heavy synchronous work (e.g., "Calculate this complex report and send me the result").
- **Implementation**: `rabbitmq_rpc_server.py` and `rabbitmq_rpc_client.py`.

### 7. Headers Exchange

- **Pattern**: Routes based on message **Headers** (metadata) instead of a Routing Key.
- **Logic**: Can use `x-match: all` (all headers must match) or `x-match: any`.
- **Best for**: Complex routing that depends on multiple attributes (e.g., `format: pdf` AND `language: fr`).

### 8. Dead Letter Exchanges (DLX)

- **Pattern**: Messages that are rejected, expired (TTL), or reach a limit are sent to a "Dead Letter" exchange for later inspection.
- **Best for**: Error handling and retry logic.

### 9. Publisher Confirms

- **Pattern**: The broker sends an ACK back to the **Producer** once the message is safely stored on disk/memory.
- **Best for**: Financial transactions or critical data where losing a single message is unacceptable.

---

## 🏛️ RabbitMQ Exchange Architecture Summary

| Exchange Type | Analogy         | Routing Logic                            | Use Case                               |
| :------------ | :-------------- | :--------------------------------------- | :------------------------------------- |
| **Direct**    | Single Mailbox  | Exact match on Routing Key.              | Logging (Filtered by severity).        |
| **Fanout**    | Megaphone       | Ignores keys; sends to all bound queues. | Broadcast Notifications.               |
| **Topic**     | Social Hashtag  | Pattern matching (`*`, `#`).             | Hierarchical data (Genres/Categories). |
| **Headers**   | Metadata Filter | Uses message headers instead of keys.    | Multi-attribute routing.               |

---

## How to use this project:

### 1. Infrastructure (UI Access & Monitoring)

| Broker       | UI URL                                           | Credentials       | Key View                                             |
| :----------- | :----------------------------------------------- | :---------------- | :--------------------------------------------------- |
| **RabbitMQ** | [http://localhost:15672](http://localhost:15672) | `guest` / `guest` | **Queues Tab**: See message counts and rates.        |
| **ActiveMQ** | [http://localhost:8161](http://localhost:8161)   | `admin` / `admin` | **Manage Broker**: Check 'Queues' vs 'Topics'.       |
| **Pulsar**   | [http://localhost:8080](http://localhost:8080)   | N/A               | **Rest API**: Use `pulsar-admin` CLI for monitoring. |
| **RocketMQ** | _CLI Only_                                       | N/A               | Check broker logs for connectivity status.           |
| **Kafka**    | _CLI Only_                                       | N/A               | Use `docker-compose logs kafka` or Python scripts.   |

---

### 2. How to use the UIs for Debugging

#### RabbitMQ UI (Management Console)

1.  Navigate to **Queues**.
2.  Click on `music_tasks`.
3.  Use the **"Get Messages"** button to peak into the queue without consuming (highly useful for debugging!).
4.  Watch the **Message Rates** graph to see how many messages/sec your producers are sending.

#### ActiveMQ Console

1.  Click on **"Manage ActiveMQ Broker"**.
2.  Go to the **Queues** tab to see your Point-to-Point messages.
3.  Go to the **Topics** tab to see active subscribers to your fanout broadcasts.
4.  You can **"Purge"** a queue here if it gets backed up with old data.

#### Kafka (The CLI Approach)

Kafka doesn't come with a built-in web UI by default (in production, people use tools like Confluent Control Center or Kafdrop).

- **Monitor logs**: `docker-compose logs -f kafka`
- **Check Topics**: Since Kafka is a log, the best "UI" is actually running your `consumer.py` script—it will show you exactly what is stored on the disk.

### 2. RabbitMQ Hands-on (Python)

We use the `pika` library for Python.

1.  **Setup Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

#### 🛠 Pattern A: Point-to-Point (Work Queues)

- **Concept**: Load balancing tasks between multiple workers.
- **Run**:
  1.  Tab 1: `python rabbitmq_consumer.py`
  2.  Tab 2: `python rabbitmq_consumer.py`
  3.  Tab 3: `python rabbitmq_producer.py`
- **Observation**: Tasks are distributed **Round-Robin**. Only one worker processes any given task.

#### 📣 Pattern B: Pub/Sub (Fanout)

- **Concept**: Broadcasting the same message to everyone.
- **Run**:
  1.  Tab 1: `python rabbitmq_fanout_consumer.py`
  2.  Tab 2: `python rabbitmq_fanout_consumer.py`
  3.  Tab 3: `python rabbitmq_fanout_producer.py`
- **Observation**: **Both** listeners receive the exact same announcement simultaneously.

#### 🚦 Pattern C: Selective Routing (Direct)

- **Concept**: Filtering messages based on severity/type.
- **Run**:
  1.  Tab 1 (Critical): `python rabbitmq_routing_consumer.py error critical`
  2.  Tab 2 (General): `python rabbitmq_routing_consumer.py info`
  3.  Tab 3: `python rabbitmq_routing_producer.py`
- **Observation**: Tab 1 ignores "User logged in" but catches the "DATABASE LOST" alert. Selective filtering in action.

#### 🏷 Pattern D: Advanced Routing (Topics)

- **Concept**: Hierarchical filtering using wildcards (`*`, `#`).
- **Run**:
  1.  Tab 1: `python rabbitmq_topic_consumer.py "music.rock.*"`
  2.  Tab 2: `python rabbitmq_topic_consumer.py "#"` (Everything)
  3.  Tab 3: `python rabbitmq_topic_producer.py`
- **Observation**: Tab 1 gets `music.rock.classic` but misses `music.pop.hits`. Tab 2 gets everything.

#### 📞 Pattern E: Request/Reply (RPC)

- **Concept**: Synchronous-style communication over an async broker.
- **Run**:
  1.  Tab 1 (Server): `python rabbitmq_rpc_server.py`
  2.  Tab 2 (Client): `python rabbitmq_rpc_client.py`
- **Observation**: The client "pauses" and waits for the server to return the specific metadata for the requested track.
