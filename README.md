# Proactive Cyber Security: Combining Cyber Deception & Moving Target Defense

> **Capstone Project - Faculty of Computer Networks & Communications - UIT**
> **Topic:** A Method of Combining Cyber Deception and Moving Target Defense for Proactive Cyber Security

![Badge](https://img.shields.io/badge/Security-Proactive-blue) ![Badge](https://img.shields.io/badge/MTD-IP%20Shuffle-green) ![Badge](https://img.shields.io/badge/Platform-Kubernetes%20K3s-orange) ![Badge](https://img.shields.io/badge/Monitoring-Splunk-black)

## 📖 Introduction

In an era where cyber attacks are becoming increasingly sophisticated (APT, Zero-day), traditional static defense measures are proving less effective. This project proposes and implements a **Proactive Defense Model** designed to disrupt the asymmetry of cyber warfare.

Our solution integrates two key strategies:
1.  **Moving Target Defense (MTD):** Continuously changing the attack surface (IP addresses, resource locations) to disrupt the attacker's reconnaissance phase.
2.  **Cyber Deception:** Deploying decoys and fake services to detect presence early and divert attackers from critical assets.

## 🏗 System Architecture

The system operates on a **Controller - Agent** model, orchestrated by the **DOLOS/Proteus Architecture**.

### 1. Key Components
* **Proteus Controller:** The central unit for coordination, monitoring, and response.
    * **Automation:** Ansible.
    * **Monitoring & Analytics:** Splunk SIEM.
    * **Response Logic:** Webhook Listener & Python Scripts.
* **Proteus Agent:** The target worker nodes protected by the system.
    * **Platform:** Docker & K3s (Lightweight Kubernetes).
    * **Deception Modules:** Portspoof, Honeyports, Endlessh, Invisiport.

### 2. Operational Workflow
1.  **Detection:** Suricata IDS or Deception modules identify suspicious activities.
2.  **Alerting:** Logs are forwarded to Splunk for analysis and alert generation.
3.  **Response:** Splunk triggers a Webhook to the Controller.
    * *Severity 2 (Reconnaissance/Scan):* Triggers **S-MTD (IP Shuffle)**.
    * *Severity 3 (Exploit/Attack):* Triggers **NL-MTD + R-MTD (Pod Migration/Node Drain)**.

![System Diagram](https://via.placeholder.com/800x400?text=System+Architecture+Diagram)
*(Reference: Figures 7 & 8 in the report)*

## 🛠 Tech Stack

| Domain | Technology |
| :--- | :--- |
| **Orchestration** | Kubernetes (K3s), Docker |
| **Automation** | Ansible, Python 3.7 |
| **Monitoring & SIEM** | Splunk, Suricata IDS |
| **Security & Network** | Sophos XG Firewall, Iptables |
| **Storage** | Longhorn (Distributed Block Storage) |
| **Deception Tools** | Portspoof, Endlessh (SSH Tarpit), Honeyports |

## 🚀 Features & Strategies

### 1. S-MTD: IP Shuffle
* **Mechanism:** Dynamically rotates the IP addresses of worker nodes within the local network.
* **Triggers:** Time-driven (Periodic) or Event-driven (upon detecting Nmap scans).
* **Impact:** Disrupts network mapping and disconnects active attack sessions.

### 2. NL-MTD + R-MTD: Pod Migration
* **Mechanism:** Utilizes K3s and Longhorn to "Drain" a compromised node.
* **Operation:** Services (Pods) are automatically migrated to a clean node with near-zero downtime (High Availability).
* **Use Case:** Mitigates malware infections or backdoors planted in containers.

### 3. Cyber Deception Modules
* **Portspoof:** Emulates thousands of open ports to slow down reconnaissance.
* **Endlessh:** An SSH tarpit that keeps attackers stuck in an infinite login loop.
* **Honeyports:** Fake ports that block IPs immediately upon connection.

## ⚙️ Installation & Deployment

### Prerequisites
* OS: Linux (Ubuntu 20.04/22.04).
* Python 3.7+, Docker, Ansible.

## ⚙️ Installation & Deployment

### Step 1: Setup Controller

```bash
# Update system
sudo apt update

# Install required packages
sudo apt install -y docker.io git cmake ansible python3.7 python3.7-dev
```

---

### Step 2: Network & SSH Configuration

Configure passwordless SSH access from the Controller to all Agent nodes.

```bash
# Generate SSH key (if not already created)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy SSH key to each agent (repeat for all agents)
ssh-copy-id -p <SSH_port> <username>@<IP_address>
```

Verify SSH connectivity:
```bash
ssh -p <SSH_port> <username>@<IP_address>
```

---

### Step 3: Deploy Proteus Agent (Cyber Deception & MTD Modules)

Deploy all protection modules to worker nodes using Ansible.

```bash
# Navigate to controller directory
cd Dolos-Controller/Management

# Deploy all modules to agents
sudo ansible-playbook deploy.yml -i inventory.ini --ask-become-pass
```

To stop all modules:
```bash
sudo ansible-playbook stop.yml -i inventory.ini
```

---

### Step 4: Enable Hostname-Based Communication (Recommended)

Enable hostname resolution to maintain connectivity during IP shuffling.

```bash
sudo systemctl enable systemd-resolved --now
sudo systemctl enable avahi-daemon --now
```

---

### Step 5: Configure Splunk & Log Forwarding

1. Install **Splunk Enterprise** on the Controller.
2. Install **Splunk Universal Forwarder** on all Agents.
3. Configure log monitoring for:
   - Suricata logs (`eve.json`, `fast.log`)
   - Proteus/DOLOS logs (`dolos.log`)
4. Create Splunk alerts based on:
   - Reconnaissance behavior
   - Deception module triggers
   - Exploitation indicators

---

### Step 6: Start Webhook Listener & IP Update API

Start automated response services on the Controller.

```bash
# Start webhook listener
sudo python3 listener.py
```

```bash
# Start IP update API
sudo python3 update_inventory_api.py
```

---

### Step 7: Enable S-MTD (IP Shuffle)

Prepare IP shuffle scripts on each Agent.

```bash
chmod +x ip_shuffle.sh
chmod +x send_ip_to_controller.sh
```

(Optional) Enable periodic IP shuffling via cron:
```bash
crontab -e
```

Example (shuffle every 5 minutes):
```bash
*/5 * * * * /path/to/ip_shuffle.sh
```

---

### Step 8: Deploy NL-MTD + R-MTD (K3s Pod Migration)

Verify Kubernetes cluster status.

```bash
kubectl get nodes -o wide
```

Drain a compromised node:
```bash
kubectl drain <worker-node-name> \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --force
```

Re-enable the node after remediation:
```bash
kubectl uncordon <worker-node-name>
```

---

### Step 9: Verification & Attack Simulation

- Perform port scanning from an attacker machine (e.g., Kali Linux)
- Observe:
  - Fake services and ports
  - Splunk alerts
  - Automatic IP shuffle or pod migration
- Verify:
  - Attacker session disruption
  - Service availability
  - Near-zero downtime

---

### Step 10: Stop the System (Optional)

Cleanly stop all defense modules.

```bash
sudo ansible-playbook stop.yml -i inventory.ini
```
## 📊 Experimental Results

The system was evaluated through multiple test runs on the agent nodes to measure both performance overhead and security effectiveness.

### 1. Performance Overhead
We measured the system resource consumption under different operating conditions. The results indicate that the defense mechanisms introduce manageable overhead.

| State / Operation | CPU Overhead | RAM Usage | Network Traffic (Packets/min) |
| :--- | :--- | :--- | :--- |
| **Idle (Baseline)** | 2.4% | 33% | Rec: 56 / Trans: 70 |
| **With DOLOS Active** | 2.6% | 38% | Rec: 78 / Trans: 98 |
| **During IP Shuffle** | 16% | 39% | Rec: 64,750 / Trans: 81,258 |
| **During Node Drain** | 7.9% | 40% | Rec: 67,234 / Trans: 79,284 |

> [cite_start]**Note:** The spikes in traffic and CPU during *IP Shuffle* and *Node Drain* are temporary, caused by the exchange of configuration data and container migration between the Controller and Agents[cite: 1526, 1528].

### 2. Defense Effectiveness
We simulated specific attack scenarios to validate the system's response capabilities.

#### 🛡️ Scenario A: Reconnaissance (Nmap Scan)
* **Attack:** Full port scan using Nmap.
* **Response:** **S-MTD (IP Shuffle)** triggered upon detecting the scan signature.
* **Outcome:** The attacker's session was disconnected immediately. [cite_start]The scan failed to map the network topology correctly[cite: 1279, 1526].

#### 🛡️ Scenario B: Malware Infection
* **Attack:** Malicious payload execution and backdoor creation inside a container.
* **Response:** **R-MTD (Node Drain)** triggered by Splunk alerts.
* **Outcome:** The compromised node was isolated. The victim Pod was automatically migrated to a clean node with near-zero downtime. [cite_start]The malware was effectively removed from the active service[cite: 1463, 1512].

### 3. Time-to-Compromise Improvement
[cite_start]Comparison of the time required for an attacker to compromise the system with and without the defense layers[cite: 1533].

| Security Layer | Compromise Rate | Time to Compromise |
| :--- | :--- | :--- |
| **Layer 1 (No Defense)** | ~85% | ~1 hour |
| **Layer 2 (With IP Shuffle)** | 0% - 61% | ~14 hours |
| **Layer 3 (Full DOLOS MTD)** | **< 6%** | **> 48 hours** |

> **Conclusion:** The combination of Cyber Deception and MTD significantly increases the complexity and cost for attackers, extending the reconnaissance and exploitation time by over **40x** compared to an undefended system.
