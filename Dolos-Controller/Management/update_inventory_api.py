from flask import Flask, request, jsonify
import os
import re
import logging

app = Flask(__name__)

# Thiết lập logging
logging.basicConfig(
    filename='update_inventory.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] :: %(message)s'
)

# Tìm đường dẫn động đến inventory.ini
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTORY_FILE = os.path.join(BASE_DIR, "inventory.ini")

# Đọc nội dung inventory.ini
def read_inventory():
    if not os.path.exists(INVENTORY_FILE):
        logging.error(f"Inventory file not found at {INVENTORY_FILE}")
        return "[workers]\n"
    with open(INVENTORY_FILE, 'r') as f:
        content = f.read()
        logging.info(f"Read inventory file: {content}")
        return content

# Cập nhật inventory.ini với IP mới, chỉ cho worker đã tồn tại
def update_inventory(agent_name, new_ip):
    inventory_content = read_inventory()
    lines = inventory_content.splitlines()
    workers_section = False
    updated = False
    new_lines = []

    logging.info(f"Attempting to update IP for agent_name: {agent_name} to {new_ip}")

    for line in lines:
        if line.strip() == "[workers]":
            workers_section = True
            new_lines.append(line)
            continue
        if workers_section and line.strip().startswith("["):
            workers_section = False
        if workers_section:
            # Kiểm tra nếu dòng chứa agent_name và cập nhật IP
            if re.match(rf"^{agent_name}\s+", line):
                # Giữ nguyên các tham số khác (như ansible_user, ansible_ssh_port)
                existing_params = line.split()
                new_line = f"{agent_name} ansible_host={new_ip}"
                for param in existing_params[2:]:  # Bỏ qua agent_name và ansible_host
                    if not param.startswith("ansible_host="):
                        new_line += f" {param}"
                new_lines.append(new_line)
                updated = True
                logging.info(f"Updated line for {agent_name}: {new_line}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Nếu không tìm thấy agent_name để cập nhật, không thêm mới
    if not updated:
        logging.warning(f"No update performed, {agent_name} not found in inventory")
        return False

    # Ghi lại file inventory.ini
    with open(INVENTORY_FILE, 'w') as f:
        f.write("\n".join(new_lines) + "\n")
    logging.info(f"Successfully updated inventory file with new IP for {agent_name}")
    return True

@app.route('/update-ip', methods=['POST'])
def update_ip():
    data = request.get_json()
    if not data or 'agent_name' not in data or 'new_ip' not in data:
        logging.error("Missing agent_name or new_ip in request")
        return jsonify({"error": "Missing agent_name or new_ip"}), 400

    agent_name = data['agent_name']
    new_ip = data['new_ip']
    
    logging.info(f"Received update request: agent_name={agent_name}, new_ip={new_ip}")

    try:
        if update_inventory(agent_name, new_ip):
            return jsonify({"message": f"Updated IP for {agent_name} to {new_ip}"}), 200
        else:
            return jsonify({"message": f"No update performed, {agent_name} not found in inventory"}), 200
    except Exception as e:
        logging.error(f"Error updating inventory: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logging.info(f"Starting API with inventory file at {INVENTORY_FILE}")
    app.run(host="0.0.0.0", port=5000)
