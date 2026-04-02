# MongoDB Setup Guide: Ubuntu & Docker

This guide covers the end-to-end process of deploying a secure, self-hosted MongoDB instance using Docker on an Oracle Cloud Infrastructure (OCI) Ubuntu server. 

## 1. Architectural Overview

To ensure maximum security and performance, this setup follows a strict 3-tier architecture. 

* **Tier 1 (Frontend):** The client application (e.g., mobile app or web frontend). It never connects directly to the database.
* **Tier 2 (API):** The backend server (e.g., Node.js, Python, etc.) hosted on a service like Vercel, AWS, or Heroku. 
* **Tier 3 (Database):** The MongoDB instance running in Docker on the OCI Ubuntu server, completely firewalled from the public internet.

*Note: If your Tier 2 API uses serverless functions with dynamic IPs, connecting Tier 2 to Tier 3 requires routing the traffic through a static IP proxy, or migrating the API server directly to the OCI instance to utilize the internal Docker network.*

---

## 2. Deploying the MongoDB Container

Docker is used to run the database securely with persistent storage and root authentication enabled from the start.

Run this command on your Ubuntu server:

    sudo docker run --name my-app-mongo -d \
      -p 27017:27017 \
      -e MONGO_INITDB_ROOT_USERNAME=admin \
      -e MONGO_INITDB_ROOT_PASSWORD=YourStrongRootPassword \
      -v mongo_data:/data/db \
      mongo:latest

### Important Flags:
* `-p 27017:27017`: Maps the default MongoDB port.
* `-v mongo_data:/data/db`: Ensures database files survive container restarts.

---

## 3. Securing the Network (Firewall & IP Whitelisting)

The database port (`27017`) must be strictly locked down to your trusted IP address (e.g., your office/home IP or your API server's static IP).

### A. Oracle Cloud (OCI) Ingress Rules
Navigate to your Virtual Cloud Network (VCN) Security List in the OCI Console and add the following rule:

| Field | Value | Explanation |
| :--- | :--- | :--- |
| **Source Type** | CIDR | Format for IP addresses. |
| **Source CIDR** | `<your-client-ip>/32` | Locks access to this specific IP only. |
| **IP Protocol** | TCP | MongoDB protocol. |
| **Destination Port Range** | `27017` | The MongoDB listening port. |
| **Description** | `MongoDB Access - Trusted IP` | Label for easy identification. |

### B. Ubuntu OS Firewall
OCI's internal `iptables` rules must match the cloud network rules. Run the following on the Ubuntu server:

    # Insert the rule for the specific IP
    sudo iptables -I INPUT 6 -s <your-client-ip> -m state --state NEW -p tcp --dport 27017 -j ACCEPT

    # Save the rule so it persists across reboots
    sudo netfilter-persistent save

*(If using UFW instead: `sudo ufw allow from <your-client-ip> to any port 27017`)*

---

## 4. Initializing the Database and Application User

Connect to your database via MongoDB Compass using the root connection string:
`mongodb://admin:YourStrongRootPassword@<your-oracle-public-ip>:27017/`

Open the `>_ MONGOSH` terminal at the bottom of Compass and run the following script to initialize the target database and create a restricted user for your API.

    // 1. Switch to the target database
    use my_app_database

    // 2. Create the dedicated API user
    db.createUser({
      user: "my_app_api_user",
      pwd: "YourSecureApiPassword", 
      roles: [ { role: "readWrite", db: "my_app_database" } ]
    })

    // 3. Insert a test document to permanently materialize the database
    db.system_config.insertOne({ 
      status: "Database initialized successfully", 
      created_at: new Date() 
    })

Once executed, click the **Refresh** icon in the Compass sidebar to view `my_app_database`. The API will now connect using:
`mongodb://my_app_api_user:YourSecureApiPassword@<your-oracle-public-ip>:27017/my_app_database`

---

## 5. Maintenance and Cleanup Commands

If you need to restart, remove, or fix accidental creations, use these commands.

### Docker Cleanup

    # Force remove a container entirely
    sudo docker rm -f my-app-mongo

    # View all running and stopped containers
    sudo docker ps -a

### MongoDB User Cleanup (via MONGOSH)

    // Switch to the database where the user exists
    use my_app_database

    // Delete the specific user
    db.dropUser("my_app_api_user")
