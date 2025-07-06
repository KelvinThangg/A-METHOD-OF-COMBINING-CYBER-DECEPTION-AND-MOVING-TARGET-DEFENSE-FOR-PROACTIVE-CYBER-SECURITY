# listener.py
import json
import os
import subprocess
import sys
import datetime
from flask import Flask, request

# Tạo một ứng dụng web Flask
app = Flask(__name__)

# --- CẤU HÌNH ---
REMEDIATION_SCRIPT_PATH = "/home/splunk/Desktop/Dolos-Controller/Management/remediate_worker.sh"
ANSIBLE_PLAYBOOK_PATH = "/home/splunk/Desktop/Dolos-Controller/Management/ip_shuffle_playbook.yml"
ANSIBLE_INVENTORY_PATH = "/home/splunk/Desktop/Dolos-Controller/Management/inventory.ini"

def find_target_worker_from_ip(pod_ip):
    """
    Tìm tên worker trong inventory dựa trên IP.
    Hàm này đã được sửa để so sánh chính xác.
    """
    try:
        with open(ANSIBLE_INVENTORY_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('[') and not line.startswith('#'):
                    # --- SỬA LỖI TẠI ĐÂY ---
                    # Tách dòng thành các phần tử dựa trên khoảng trắng
                    parts = line.split()
                    if not parts:
                        continue

                    worker_name_from_line = parts[0]
                    ip_found_on_line = None

                    # Tìm phần tử ansible_host và trích xuất IP
                    for part in parts[1:]:
                        if part.startswith('ansible_host='):
                            # Tách bằng dấu '=' để lấy giá trị IP
                            ip_found_on_line = part.split('=', 1)[1]
                            break
                    
                    # Thực hiện so sánh BẰNG (==) thay vì IN
                    if ip_found_on_line and ip_found_on_line == pod_ip:
                        print(f"INFO: Tìm thấy worker '{worker_name_from_line}' có IP '{pod_ip}' (khớp chính xác)")
                        return worker_name_from_line
            
        print(f"WARNING: Không tìm thấy worker nào có IP '{pod_ip}' trong inventory")
        return None
        
    except FileNotFoundError:
        print(f"ERROR: Không tìm thấy file inventory tại '{ANSIBLE_INVENTORY_PATH}'")
        return None
    except Exception as e:
        print(f"ERROR: Lỗi khi đọc inventory file: {e}")
        return None

# Định nghĩa một "route" để lắng nghe các request từ Splunk
@app.route('/splunk_alert', methods=['POST'])
def splunk_webhook_listener():
    """
    Hàm này sẽ được thực thi mỗi khi Splunk gửi một alert đến URL này.
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n--- [ {current_time} ] ---")
    print("INFO: Đã nhận được alert từ Splunk!")

    try:
        data = request.get_json()
        print("INFO: Dữ liệu nhận được (dạng thô):")
        print(json.dumps(data, indent=4))

        result = data.get('result', {})
        if not result:
            print("ERROR: Payload không chứa trường 'result'.")
            return "Invalid payload", 400

        severity = result.get('alert.severity')
        pod_ip_to_check = result.get('dest_ip')

        print(f"INFO: Phân tích alert: Severity='{severity}', Dest_IP='{pod_ip_to_check}'")

        if severity == "1":
            print("CRITICAL: Mức độ nghiêm trọng là 1. Bắt đầu quá trình khắc phục sự cố.")
            
            if not pod_ip_to_check:
                print("ERROR: Không tìm thấy 'dest_ip' trong alert để thực hiện hành động.")
                return "Missing dest_ip in result", 400
            
            if not os.path.exists(REMEDIATION_SCRIPT_PATH):
                print(f"ERROR: Không tìm thấy script khắc phục sự cố tại '{REMEDIATION_SCRIPT_PATH}'")
                return "Remediation script not found on server", 500

            try:
                print(f"ACTION: Đang thực thi '{REMEDIATION_SCRIPT_PATH}' với IP '{pod_ip_to_check}'...")
                subprocess.Popen([REMEDIATION_SCRIPT_PATH, pod_ip_to_check])
                print("ACTION: Script đã được kích hoạt thành công.")
            except Exception as e:
                print(f"ERROR: Có lỗi khi thực thi script khắc phục sự cố: {e}", file=sys.stderr)
                return "Error executing script", 500

        elif severity == "2":
            print("CRITICAL: Mức độ nghiêm trọng là 2. Kích hoạt Ansible playbook để chạy ip_shuffle.sh.")

            if not pod_ip_to_check:
                print("ERROR: Không tìm thấy 'dest_ip' trong alert để thực hiện hành động.")
                return "Missing dest_ip in result", 400

            if not all([os.path.exists(ANSIBLE_PLAYBOOK_PATH), os.path.exists(ANSIBLE_INVENTORY_PATH)]):
                print(f"ERROR: Thiếu file playbook hoặc inventory.")
                return "Ansible playbook or inventory not found on server", 500

            # Tìm tên worker dựa trên IP
            target_worker = find_target_worker_from_ip(pod_ip_to_check)
            if not target_worker:
                print(f"INFO: Không thể xác định worker nào có IP '{pod_ip_to_check}'. Bỏ qua hành động.")
                # Trả về 200 OK vì đã xử lý xong (không tìm thấy cũng là một kết quả)
                return "Target worker not found in inventory, action skipped.", 200

            try:
                command = [
                    'ansible-playbook',
                    '--become',
                    '-i', ANSIBLE_INVENTORY_PATH,
                    ANSIBLE_PLAYBOOK_PATH,
                    '--extra-vars', f'target_worker={target_worker}'
                ]

                print(f"ACTION: Đang thực thi lệnh: {' '.join(command)}")
                print(f"ACTION: Target worker: {target_worker}")
                
                # Dùng Popen để chạy playbook dưới dạng nền
                subprocess.Popen(command)
                print("ACTION: Ansible playbook đã được kích hoạt thành công.")
            except Exception as e:
                print(f"ERROR: Có lỗi khi thực thi Ansible playbook: {e}", file=sys.stderr)
                return "Error executing playbook", 500
        else:
            print(f"INFO: Mức độ nghiêm trọng là '{severity}'. Không yêu cầu hành động.")

        return "Webhook received and processed.", 200

    except Exception as e:
        print(f"ERROR: Có lỗi nghiêm trọng xảy ra khi xử lý request: {e}", file=sys.stderr)
        return "Error processing request", 500

# Chạy ứng dụng web
if __name__ == '__main__':
    print(f"INFO: Listener đang chạy tại http://0.0.0.0:5001/splunk_alert")
    print(f"INFO: Script khắc phục (Severity 1) được cấu hình tại: {REMEDIATION_SCRIPT_PATH}")
    print(f"INFO: Ansible playbook (Severity 2) được cấu hình tại: {ANSIBLE_PLAYBOOK_PATH}")
    print(f"INFO: Ansible inventory được cấu hình tại: {ANSIBLE_INVENTORY_PATH}")
    print("INFO: Nhấn CTRL+C để dừng.")
    app.run(host='0.0.0.0', port=5001, debug=False)