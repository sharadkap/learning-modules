# Apache Kafka: The Event Streaming Platform

Kafka is NOT a message broker in the traditional sense. It is a **distributed append-only commit log**. Understanding this shift is the key to passing any Kafka interview.

## 1. The Core Paradigm Shift

| Feature | RabbitMQ/ActiveMQ (Messaging) | Apache Kafka (Streaming) |
| :--- | :--- | :--- |
| **Data Storage** | Transient (Deleted after ACK) | Persistent (Retained for days/years) |
| **Consumer Logic** | Passive (Pushed by broker) | Active (Pulled by consumer) |
| **Ordering** | Guaranteed per queue | Guaranteed **per Partition** |
| **Replayability** | No (Once gone, it's gone) | Yes (Move the "Offset" back) |

## 2. Key Concepts

### Topics & Partitions
A **Topic** is a category (e.g., `user_clicks`). A Topic is split into **Partitions**.
*   This is how Kafka scales! Different partitions can live on different servers.
*   A message with a specific key (e.g., `user_id: 123`) always goes to the same partition, ensuring order for *that* user.

### Offsets
An **Offset** is just a number. It represents the position of a message in a partition.
*   Consumers keep track of their own offset.
*   If a consumer crashes, it just restarts from its last saved offset.

### Consumer Groups
This is how Kafka does load balancing.
*   If you have 4 partitions and 4 consumers in a group, each consumer gets 1 partition.
*   If you have 4 partitions and 2 consumers, each gets 2 partitions.
*   **Crucial**: One partition can only be read by one consumer in a group at a time.

---

## 🧠 The Silent Partner: ZooKeeper

In our `docker-compose.yml`, you noticed we started a `zookeeper` service. Kafka (in the version we are using) cannot run without it.

### What does ZooKeeper do?
1.  **Controller Election**: It elects one Kafka broker to be the "Controller" (the boss of the cluster).
2.  **Cluster Membership**: It maintains a list of all active brokers.
3.  **Topic Metadata**: It stores which partitions belong to which brokers.
4.  **Leader Election**: If a partition leader fails, ZooKeeper helps elect a new one from the replicas.

### 💡 Tip: KRaft (Modern Kafka)
Modern Kafka (v3.0+) is moving away from ZooKeeper toward a built-in consensus protocol called **KRaft**. 
*   **Why?** Removing ZooKeeper simplifies the architecture and allows Kafka to handle millions of partitions more efficiently. 
*   *Note: Our current setup uses ZooKeeper as it's still the most common configuration in existing enterprise environments.*

---

## 🚀 How to Run the Lesson

We use the `confluent-kafka` library (the industry standard).

### 1. Prerequisites (Virtual Environment)
Always ensure your virtual environment is activated before running the scripts.
```bash
# From the project root (/message_brokers)
source venv/bin/activate
# Navigate to this folder
cd kafka
```

### 2. The Producer
The producer sends "Streaming Events" (e.g., songs played). We use the **User Name** as the partitioning key to ensure order per user.
```bash
python producer.py
```
**Look for**: Offset and Partition numbers in the output. This shows how Kafka is organizing the data.

### 3. The Consumer
The consumer reads from the beginning of the log. Because Kafka is persistent, you can run this **after** the producer has already finished.
```bash
python consumer.py
```
**Key Observation**: Notice you see the "History" (Offset 0, 1, 2...). This is **Replayability** in action!

---

## 💡 Tip: Why use Kafka?
When an interviewer asks why you didn't just use RabbitMQ:
> *"I chose Kafka because we needed **replayability**. We needed to be able to re-process the last 24 hours of data if our analytics algorithm changed. Traditional brokers delete data after it's read; Kafka treats data as a permanent stream of truth."*
