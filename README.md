# Proactive Cyber Security: Combining Cyber Deception & Moving Target Defense

> **Capstone Project - Faculty of Computer Networks & Communications - UIT**
> [cite_start]**Topic:** A Method of Combining Cyber Deception and Moving Target Defense for Proactive Cyber Security [cite: 6, 13]

![Badge](https://img.shields.io/badge/Security-Proactive-blue) ![Badge](https://img.shields.io/badge/MTD-IP%20Shuffle-green) ![Badge](https://img.shields.io/badge/Platform-Kubernetes%20K3s-orange) ![Badge](https://img.shields.io/badge/Monitoring-Splunk-black)

## 📖 Introduction

[cite_start]In an era where cyber attacks are becoming increasingly sophisticated (APT, Zero-day), traditional static defense measures are proving less effective[cite: 34]. This project proposes and implements a **Proactive Defense Model** designed to disrupt the asymmetry of cyber warfare.

Our solution integrates two key strategies:
1.  [cite_start]**Moving Target Defense (MTD):** Continuously changing the attack surface (IP addresses, resource locations) to disrupt the attacker's reconnaissance phase[cite: 39].
2.  [cite_start]**Cyber Deception:** Deploying decoys and fake services to detect presence early and divert attackers from critical assets[cite: 40].

## 🏗 System Architecture

[cite_start]The system operates on a **Controller - Agent** model, orchestrated by the **DOLOS/Proteus Architecture**[cite: 412, 437].

### 1. Key Components
* [cite_start]**Proteus Controller:** The central unit for coordination, monitoring, and response[cite: 437].
    * [cite_start]**Automation:** Ansible[cite: 450].
    * [cite_start]**Monitoring & Analytics:** Splunk SIEM[cite: 469].
    * [cite_start]**Response Logic:** Webhook Listener & Python Scripts[cite: 673].
* [cite_start]**Proteus Agent:** The target worker nodes protected by the system[cite: 470].
    * [cite_start]**Platform:** Docker & K3s (Lightweight Kubernetes)[cite: 508, 509].
    * [cite_start]**Deception Modules:** Portspoof, Honeyports, Endlessh, Invisiport[cite: 434].

### 2. Operational Workflow
1.  [cite_start]**Detection:** Suricata IDS or Deception modules identify suspicious activities[cite: 471].
2.  [cite_start]**Alerting:** Logs are forwarded to Splunk for analysis and alert generation[cite: 485].
3.  [cite_start]**Response:** Splunk triggers a Webhook to the Controller[cite: 489].
    * [cite_start]*Severity 2 (Reconnaissance/Scan):* Triggers **S-MTD (IP Shuffle)**[cite: 493].
    * [cite_start]*Severity 3 (Exploit/Attack):* Triggers **NL-MTD + R-MTD (Pod Migration/Node Drain)**[cite: 497].

![System Diagram](https://via.placeholder.com/800x400?text=System+Architecture+Diagram)
*(Reference: Figures 7 & 8 in the report)*

## 🛠 Tech Stack

| Domain | Technology |
| :--- | :--- |
| **Orchestration** | [cite_start]Kubernetes (K3s), Docker [cite: 469, 508] |
| **Automation** | [cite_start]Ansible, Python 3.7 [cite: 450, 510] |
| **Monitoring & SIEM** | [cite_start]Splunk, Suricata IDS [cite: 469, 471] |
| **Security & Network** | [cite_start]Sophos XG Firewall, Iptables [cite: 472, 507] |
| **Storage** | [cite_start]Longhorn (Distributed Block Storage) [cite: 825] |
| **Deception Tools** | [cite_start]Portspoof, Endlessh (SSH Tarpit), Honeyports [cite: 434] |

## 🚀 Features & Strategies

### 1. S-MTD: IP Shuffle
* [cite_start]**Mechanism:** Dynamically rotates the IP addresses of worker nodes within the local network[cite: 502, 663].
* [cite_start]**Triggers:** Time-driven (Periodic) or Event-driven (upon detecting Nmap scans)[cite: 667, 673].
* [cite_start]**Impact:** Disrupts network mapping and disconnects active attack sessions[cite: 306, 1526].

### 2. NL-MTD + R-MTD: Pod Migration
* [cite_start]**Mechanism:** Utilizes K3s and Longhorn to "Drain" a compromised node[cite: 960].
* [cite_start]**Operation:** Services (Pods) are automatically migrated to a clean node with near-zero downtime (High Availability)[cite: 985].
* [cite_start]**Use Case:** Mitigates malware infections or backdoors planted in containers[cite: 1450].

### 3. Cyber Deception Modules
* [cite_start]**Portspoof:** Emulates thousands of open ports to slow down reconnaissance[cite: 112].
* [cite_start]**Endlessh:** An SSH tarpit that keeps attackers stuck in an infinite login loop.
* [cite_start]**Honeyports:** Fake ports that block IPs immediately upon connection[cite: 113].

## ⚙️ Installation & Deployment

### Prerequisites
* [cite_start]OS: Linux (Ubuntu 20.04/22.04)[cite: 506].
* [cite_start]Python 3.7+, Docker, Ansible[cite: 516].

### Step 1: Setup Controller
```bash
# Update and install dependencies
sudo apt update
sudo apt install -y docker.io git cmake ansible python3.7 python3.7-dev

# Copy SSH Key to Agents
ssh-copy-id -p <ssh_port> <username>@<IP_Agent>
