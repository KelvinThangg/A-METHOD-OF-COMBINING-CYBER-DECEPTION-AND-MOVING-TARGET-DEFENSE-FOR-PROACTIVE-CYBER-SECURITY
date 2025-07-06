#!/bin/bash

# --- CẤU HÌNH ---
# Điền đường dẫn tuyệt đối đến file inventory của bạn.
# Ví dụ: /home/splunk/ansible/inventory.ini
INVENTORY_PATH="/home/splunk/Desktop/Dolos-Controller/Management/inventory.ini"

# --- Bắt đầu Script ---

# 1. Kiểm tra xem IP có được cung cấp làm tham số không
if [ -z "$1" ]; then
  echo "$(date): [ERROR] Không có địa chỉ IP nào được cung cấp. Dừng script."
  exit 1
fi

ALERT_IP=$1
LOG_PREFIX="$(date): [IP: $ALERT_IP]"

echo "$LOG_PREFIX Bắt đầu quá trình khắc phục sự cố."

# --- BƯỚC KIỂM TRA (PRE-FLIGHT CHECK) ---
echo "$LOG_PREFIX Đang tìm kiếm worker tương ứng với IP trong file inventory..."

# Kiểm tra xem file inventory có tồn tại và đọc được không
if [ ! -f "$INVENTORY_PATH" ]; then
    echo "$LOG_PREFIX [ERROR] Không tìm thấy file inventory tại '$INVENTORY_PATH'. Dừng script."
    exit 1
fi

# 2. Dùng grep và cut để tìm worker name từ IP trong file inventory
#    - grep "ansible_host=$ALERT_IP": Tìm dòng có chứa chuỗi khớp chính xác.
#    - cut -d' ' -f1: Lấy phần đầu tiên của dòng (tên worker), với dấu cách là dấu phân cách.
WORKER_NAME=$(grep "ansible_host=$ALERT_IP" "$INVENTORY_PATH" | cut -d' ' -f1)

# 3. Kiểm tra xem có tìm thấy worker không
if [ -z "$WORKER_NAME" ]; then
  echo "$LOG_PREFIX [ERROR] Không tìm thấy worker nào có IP '$ALERT_IP' trong file inventory '$INVENTORY_PATH'."
  exit 1
fi

echo "$LOG_PREFIX Đã tìm thấy Worker: '$WORKER_NAME' tương ứng với IP '$ALERT_IP'."

# --- BƯỚC THỰC THI ---
echo "$LOG_PREFIX Bắt đầu drain node '$WORKER_NAME'..."

# 4. Thực thi lệnh drain với tên worker tìm được
kubectl drain "$WORKER_NAME" --ignore-daemonsets --delete-emptydir-data --force --disable-eviction=true

# Kiểm tra xem lệnh drain có thành công không
if [ $? -ne 0 ]; then
  echo "$LOG_PREFIX [ERROR] Lệnh drain thất bại. Sẽ không thực hiện uncordon."
  exit 1
fi

echo "$LOG_PREFIX Drain node '$WORKER_NAME' thành công."
echo "$LOG_PREFIX Bắt đầu uncordon node '$WORKER_NAME'..."

# 5. Thực thi lệnh uncordon với sudo như bạn yêu cầu
sudo kubectl uncordon "$WORKER_NAME"

echo "$LOG_PREFIX Đã uncordon node '$WORKER_NAME'."
echo "$LOG_PREFIX Quá trình khắc phục sự cố hoàn tất."

# --- Kết thúc Script ---

