# 🐳 Infrastructure Setup Guide (Docker)

This guide covers how to set up the entire engineering environment for this project on **macOS** and **Ubuntu**. We use Docker to ensure "it works on my machine" consistency across all 5 message brokers and MongoDB.

---

## 🚀 1. Install Docker

### **For macOS**

1.  **Download**: [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/).
2.  **Architecture**: Choose **Apple Chip** (M1/M2/M3) or **Intel** based on your Mac.
3.  **Permissions**: Open Docker Desktop and grant the internal permissions it requests.
4.  **Verify**: Open your terminal and run:
    ```bash
    docker --version
    docker compose version
    ```

### **For Ubuntu (Server/Desktop)**

Run the following commands to install Docker Engine:

```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install ca-certificates curl gnupg

# Add Docker’s official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group (optional, to avoid using 'sudo')
sudo usermod -aG docker $USER
# logout and log back in for this to take effect
```

---

## 🛠 2. Spin Up Infrastructure

All brokers are defined in the `message_brokers/docker-compose.yml` file.

1.  **Navigate directly to the folder**:
    ```bash
    cd message_brokers
    ```
2.  **Start all services**:
    ```bash
    docker compose up -d
    ```
    _Note: Add `-d` to run in the background._

---

## 📊 3. Verifying the Components

Once running, you can access the following management consoles:

| Technology   | UI / Endpoint                                    | Default Ports | Credentials       |
| :----------- | :----------------------------------------------- | :------------ | :---------------- |
| **RabbitMQ** | [http://localhost:15672](http://localhost:15672) | 5672, 15672   | `guest` / `guest` |
| **ActiveMQ** | [http://localhost:8161](http://localhost:8161)   | 61613, 8161   | `admin` / `admin` |
| **Pulsar**   | [http://localhost:8080](http://localhost:8080)   | 6650, 8080    | N/A               |
| **Kafka**    | `localhost:9092`                                 | 9092, 2181    | N/A               |
| **RocketMQ** | `localhost:9876`                                 | 9876, 10911   | N/A               |
| **MongoDB**  | `localhost:27017`                                | 27017         | N/A (Docker)      |

---

## 🐍 4. Python Environment Setup

The interactive documentation relies on Python scripts to interact with these brokers.

1.  **Create Virtual Env**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  **Install Global Dependencies**:
    ```bash
    pip install pika stomp.py confluent-kafka pulsar-client pymongo websockets python-dotenv
    ```

---

## 🔍 Troubleshooting

### **Memory Issues (Pulsar/RocketMQ)**

Pulsar and RocketMQ are heavy. If they keep crashing:

- **Mac**: Increase "Memory" in Docker Desktop Settings > Resources (8GB recommended).
- **Ubuntu**: Ensure you have a swap file enabled if RAM is < 8GB.

### **Port Conflicts**

If a service fails to start with "Address already in use":

- Check if you have a local instance of MongoDB or RabbitMQ running natively.
- Run `lsof -i :PORT` to find the culprit process and kill it.

### **ARM Macs (M1/M2)**

RocketMQ and Pulsar might require specific images. The `docker-compose.yml` uses multi-arch images, but for older versions, you might need to specify `--platform linux/amd64` in the compose file if you encounter "Exec format error".
