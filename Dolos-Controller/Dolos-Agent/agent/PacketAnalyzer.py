import json
import logging
import socket
import threading
import time
from datetime import datetime
from scapy.all import *
import types
import sys
import select

# Mô phỏng module log
class Log:
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    _lock = threading.Lock()

    @staticmethod
    def write(level, message):
        with Log._lock:
            timestamp = datetime.now().strftime("%Y/%m/%d:%H:%M:%S")
            level_str = {Log.DEBUG: "DBG", Log.INFO: "INF", Log.WARNING: "WAR",
                         Log.ERROR: "ERR", Log.CRITICAL: "CRT"}.get(level, "???")
            log_message = f"{timestamp} [{level_str}] :: {message}"
            logging.getLogger().log(level, log_message)

# Mô phỏng module connection
class Connection:
    @staticmethod
    def shutdown(sock, active_sock):
        try:
            if active_sock is not None and hasattr(active_sock, 'fileno') and active_sock.fileno() != -1:
                active_sock.close()
        except Exception as e:
            Log.write(Log.ERROR, f"Error shutting down socket: {e}")

    @staticmethod
    def send(sock, active_sock, data, length):
        try:
            if active_sock is not None and hasattr(active_sock, 'fileno') and active_sock.fileno() != -1:
                active_sock.setblocking(False)
                ready = select.select([], [active_sock], [], 0.1)[1]
                if not ready:
                    raise socket.error("Socket not writable")
                active_sock.send(data)
        except socket.timeout:
            raise
        except socket.error as e:
            raise
        except Exception as e:
            raise

# Gắn module log và connection vào global namespace trước các import khác
log_module = types.ModuleType('log')
log_module.Log = Log
sys.modules['log'] = log_module

connection_module = types.ModuleType('connection')
connection_module.Connection = Connection
sys.modules['connection'] = connection_module

# Bây giờ mới import các module khác
from Portspoof import Portspoof
from Honeyports import Honeyports
from Invisiport import Invisiport

# >>> THAY ĐỔI DUY NHẤT TRONG FILE PYTHON
# Cấu hình logging để ghi vào đường dẫn tuyệt đối /var/log/dolos.log
logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s',
    handlers=[
        logging.FileHandler('/var/log/dolos.log'), # Sửa từ 'dolos.log' thành '/var/log/dolos.log'
        logging.StreamHandler()
    ]
)

# Đọc file cấu hình dolos.conf
def load_config(file_path):
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        Log.write(Log.INFO, f"Loaded configuration from {file_path}: {config}")
        return config
    except json.JSONDecodeError as e:
        Log.write(Log.ERROR, f"Invalid JSON in config file {file_path}: {e}")
        return {}
    except FileNotFoundError:
        Log.write(Log.ERROR, f"Config file {file_path} not found")
        return {}
    except Exception as e:
        Log.write(Log.ERROR, f"Error reading config file {file_path}: {e}")
        return {}

# Tái tạo socket nếu không hợp lệ
def create_socket(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', port))
        return sock
    except Exception as e:
        Log.write(Log.ERROR, f"Failed to create socket for port {port}: {e}")
        return None

# Xử lý kết nối cho mỗi cổng
def handle_connection(sock, port, module_class):
    lock = threading.Lock()
    try:
        sock.listen(5)
        Log.write(Log.INFO, f"Listening on port {port} for {module_class.__name__}")
        while True:
            try:
                if sock.fileno() == -1:
                    Log.write(Log.ERROR, f"Socket on port {port} is invalid, recreating...")
                    sock = create_socket(port)
                    if sock is None:
                        break
                    sock.listen(5)
                sock.settimeout(5.0)
                with lock:
                    active_sock, addr = sock.accept()
                    ip = addr[0]
                    current_time = time.time()
                    Log.write(Log.DEBUG, f"Connection from {ip} to port {port}")
                    try:
                        # Kiểm tra xem kết nối đã được xử lý chưa
                        if not any(ip == h_ip and port == h_port and current_time - t < 0.5
                                   for h_ip, h_port, t in handled_connections):
                            module_instance = module_class(sock, port, active_sock, ip)
                            module_instance.start(b"", is_scan=False, scan_type="TCP Connect")
                            handled_connections.add((ip, port, current_time))
                    except Exception as e:
                        Log.write(Log.ERROR, f"Error processing module {module_class.__name__} on port {port} for {ip}: {e}")
                    finally:
                        Connection.shutdown(None, active_sock)
            except socket.timeout:
                continue
            except socket.error as e:
                Log.write(Log.ERROR, f"Socket error on port {port}: {e}")
                if e.errno == 9:
                    Log.write(Log.ERROR, f"Socket on port {port} is invalid, recreating...")
                    sock = create_socket(port)
                    if sock is None:
                        break
                    sock.listen(5)
            except Exception as e:
                Log.write(Log.ERROR, f"Unexpected error on port {port}: {e}")
    except Exception as e:
        Log.write(Log.ERROR, f"Failed to listen on port {port}: {e}")
    finally:
        Connection.shutdown(sock, None)

# Tạo socket và chạy module
def start_module_ports(ports, module_class):
    for port in ports:
        sock = create_socket(port)
        if sock:
            threading.Thread(target=handle_connection, args=(sock, port, module_class), daemon=True).start()

# Phát hiện quét cổng và chuyển hướng tới module
def packet_callback(packet):
    if packet.haslayer(TCP):
        src_ip = packet[IP].src
        dst_port = packet[TCP].dport
        current_time = time.time()
        flags = packet[TCP].flags

        # Kiểm tra xem gói đã được xử lý chưa
        if any(src_ip == h_ip and dst_port == h_port and current_time - t < 0.5
               for h_ip, h_port, t in handled_connections):
            return

        # Xác định loại quét dựa trên cờ TCP
        scan_type = None
        if flags == 'S':
            scan_type = "SYN"
        elif flags == 'FPU':
            scan_type = "Xmas"
        elif flags == 'F':
            scan_type = "FIN"
        elif flags == 0:
            scan_type = "Null"

        # Kiểm tra cổng thuộc module nào
        module_class = None
        for tool in config.values():
            if 'ports' in tool and dst_port in tool['ports']:
                module_name = tool.get('file')
                module_class = module_map.get(module_name)
                Log.write(Log.DEBUG, f"Port {dst_port} mapped to module {module_name}")
                break

        # Chuyển hướng tới module nếu tìm thấy
        if module_class and scan_type:
            try:
                module_instance = module_class(None, dst_port, None, src_ip)
                module_instance.start(b"", is_scan=True, scan_type=scan_type)
                handled_connections.add((src_ip, dst_port, current_time))
            except Exception as e:
                Log.write(Log.ERROR, f"Error processing {scan_type} scan for {module_class.__name__} on port {dst_port}: {e}")

        # Theo dõi gói quét
        if src_ip not in scan_tracker:
            scan_tracker[src_ip] = {'ports': [], 'last_log': 0}
        scan_tracker[src_ip]['ports'].append((current_time, dst_port))

        # Loại bỏ các bản ghi cũ
        scan_tracker[src_ip]['ports'] = [(t, p) for t, p in scan_tracker[src_ip]['ports'] if current_time - t < 10]

        # Ghi log nếu quét nhiều cổng không thuộc module
        if not module_class:
            if (len(set(p for t, p in scan_tracker[src_ip]['ports'])) > 5 and
                    current_time - scan_tracker[src_ip]['last_log'] > 10):
                Log.write(Log.WARNING, f"Detected port scanning from {src_ip} (multiple ports)")
                scan_tracker[src_ip]['last_log'] = current_time

# Theo dõi gói quét, kết nối đã xử lý và cấu hình toàn cục
scan_tracker = {}
handled_connections = set()
config = {}
module_map = {
    "Portspoof": Portspoof,
    "Honeyports": Honeyports,
    "Invisiport": Invisiport
}

def main():
    global config
    config = load_config('dolos.conf')
    if not config:
        Log.write(Log.ERROR, "No valid configuration found. Exiting.")
        return

    for tool in config.values():
        module_name = tool.get('file')
        ports = tool.get('ports', [])
        if module_name in module_map and ports:
            start_module_ports(ports, module_map[module_name])
        else:
            Log.write(Log.WARNING, f"Invalid module {module_name} or no ports defined")

    Log.write(Log.INFO, "Starting port scan detection...")
    sniff(prn=packet_callback, filter="tcp", store=0)

if __name__ == "__main__":
    main()
