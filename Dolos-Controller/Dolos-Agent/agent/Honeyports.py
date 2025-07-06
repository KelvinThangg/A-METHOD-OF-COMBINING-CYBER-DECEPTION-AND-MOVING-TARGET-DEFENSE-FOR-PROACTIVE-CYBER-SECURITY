from Core import Core
from log import Log
import subprocess
import time

class Honeyports(Core):
    MSG = b""
    _logged_connections = set()

    def __init__(self, sock, port, active_sock, ip):
        super().__init__(sock, port, active_sock, ip)

    def start(self, b, is_scan=False, scan_type=None):
        current_time = time.time()
        connection_key = (self.ip, self.port, current_time)
        
        # Xóa các bản ghi cũ
        Honeyports._logged_connections = {(ip, port, t) for ip, port, t in Honeyports._logged_connections if current_time - t < 1}
        
        # Ghi log và chặn IP
        if connection_key not in Honeyports._logged_connections:
            super().log(Log.WARNING, f"Someone connect to Honeyport ({scan_type} scan)")
            self.__blacklist(self.ip)
            Honeyports._logged_connections.add(connection_key)

        # Xử lý cho kết nối TCP đầy đủ
        if not is_scan and self.active_sock is not None:
            try:
                if self.MSG:
                    super().send(self.MSG)
                super().log(Log.INFO, f"received {b}")
                super().shutdown()
            except Exception as e:
                Log.write(Log.ERROR, f"Error processing connection on port {self.port} for {self.ip}: {e}")

    def __blacklist(self, ip):
        params = ['iptables', '-A', 'INPUT', '-s', ip, '-j', 'REJECT']
        try:
            subprocess.run(params, check=True)
            super().log(Log.INFO, f"Add rule to block IP {ip} in iptables")
        except Exception as e:
            Log.write(Log.ERROR, f"Error blocking IP {ip}: {e}")
