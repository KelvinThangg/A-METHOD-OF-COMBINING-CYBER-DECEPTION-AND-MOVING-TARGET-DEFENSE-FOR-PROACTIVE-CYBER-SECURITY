# A Cyber Defense Approach Leveraging Moving Target Defense and Cyber Deception
## Overview
This is a proactive defense method capable of complicating an attacker's reconnaissance phase. By combining Moving Target Defense and Cyber Deception and then embedding them into the system, this approach overcomes the weaknesses of both Cyber Deception and Moving Target Defense without consuming excessive resources or impacting the system.

## Installing
### Step 1: Clone the repository
```bash
git clone https://github.com/tranductridung/Dolos-Controller
```

### Step 2: Navigate to the project directory
```bash
cd Dolos-Controller/Dolos-Agent
```

### Step 3: Build the project
```bash
./linux_build.sh
```

### Step 4: Copy the agent binary
```bash
cp bin/agent linux/test/agent
```

## Configure
### 1. Configure MTD Modules
Define the configuration for MTD modules in `dolos_worker.conf` file (JSON format) located in the `files` folder. Example:
```bash
{
  "tool_1": {
    "file": "Portspoof",
    "class": "Portspoof",
    "method": "start",
    "ports": [5000, 6000]
  }
}
```
### 2. Configure Endlessh Tool
Specify Endlessh-related settings in the `worker.yml` file located in the `host_vars` folder. Example:
```bash
dolos_conf_file: dolos_worker2.conf
endlessh_ports:
  - 22
  - 2001
```
### 3. Configure Agent Information
Update the `inventory.ini` file to specify details of the DOLOS Agents. Example:
```bash
[workers]
worker1 ansible_host=192.168.1.100 ansible_user=user1 ansible_ssh_port=22
worker2 ansible_host=192.168.1.101 ansible_user=user2 ansible_ssh_port=2000
```
### 4. Copy SSH Key
Copy the SSH key of the DOLOS Controller to the DOLOS Agent:
```bash
ssh-copy-id -p SSH_port username@IP_address
```
## Usage
### 1. Install and Run DOLOS Agent from Controller
To deploy and start the DOLOS Agent, execute the following from the DOLOS Controller:
```bash
cd Dolos-Controller/Management
ansible-playbook deploy.yml -i inventory.ini --ask-become-pass
```
### 2. Stop DOLOS Agent from DOLOS Controller
To stop the DOLOS Agent, execute:
```bash
ansible-playbook stop.yml -i inventory.ini --ask-become-pass
```
### 3. Run DOLOS Agent without DOLOS Controller
**With Endlessh (ports 2001 and 2002)**
```bash
cd Dolos-Controller/Dolos-Agent/linux/test
./run.sh "2001 2002"
```
**Without Endlessh**
```bash
./run.sh
```
