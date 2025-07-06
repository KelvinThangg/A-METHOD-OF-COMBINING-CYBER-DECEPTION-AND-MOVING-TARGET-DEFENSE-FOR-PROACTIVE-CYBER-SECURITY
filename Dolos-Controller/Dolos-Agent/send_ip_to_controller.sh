#!/bin/bash

# Địa chỉ IP của controller (không thay đổi)
CONTROLLER_IP="10.0.0.10"  # Thay bằng IP thực tế của controller
CONTROLLER_PORT="5000"         # Port của API trên controller
AGENT_NAME=$(hostname)         # Lấy tên của agent (worker1, worker2, ...)

# Lấy IP mới của agent sau khi shuffle
NEW_IP=$(hostname -I | awk '{print $1}')  # Lấy IP đầu tiên

if [ -z "$NEW_IP" ]; then
    echo "Error: Could not determine new IP address."
    exit 1
fi

# Gửi IP mới đến controller qua API
echo "Sending new IP ($NEW_IP) to controller ($CONTROLLER_IP:$CONTROLLER_PORT)..."
curl -X POST "http://$CONTROLLER_IP:$CONTROLLER_PORT/update-ip" \
     -H "Content-Type: application/json" \
     -d "{\"agent_name\": \"$AGENT_NAME\", \"new_ip\": \"$NEW_IP\"}" \
     --silent --fail

if [ $? -eq 0 ]; then
    echo "Successfully sent new IP to controller."
else
    echo "Failed to send new IP to controller."
    exit 1
fi
