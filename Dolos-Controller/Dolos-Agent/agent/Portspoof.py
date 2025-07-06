from Core import Core
from log import Log
from connection import Connection
import os
import random
import time

class Portspoof(Core):
    _logged_connections = set()

    def __init__(self, sock, port, active_sock, ip):
        super().__init__(sock, port, active_sock, ip)
        self.signatures = self._load_signatures()
        self.answer = self._get_random_signature() if self.signatures else b"Fake signature"

    def _load_signatures(self):
        try:
            if os.path.exists("portspoof_signatures"):
                with open("portspoof_signatures", "rb") as f:
                    return [line.strip() for line in f if line.strip()]
            return []
        except Exception as e:
            Log.write(Log.ERROR, f"Error loading portspoof_signatures: {e}")
            return []

    def _get_random_signature(self):
        return random.choice(self.signatures) if self.signatures else b"Fake signature"

    def start(self, b, is_scan=False, scan_type=None):
        """
        Xử lý kết nối hoặc quét cổng.
        - is_scan: True nếu là quét cổng (SYN, Xmas, Null, FIN).
        - scan_type: Loại quét ('SYN', 'Xmas', 'Null', 'FIN', 'TCP Connect').
        """
        current_time = time.time()
        connection_key = (self.ip, self.port, current_time)
        
        # Xóa các bản ghi cũ
        Portspoof._logged_connections = {(ip, port, t) for ip, port, t in Portspoof._logged_connections if current_time - t < 1}
        
        # Ghi log WARN chỉ một lần
        if connection_key not in Portspoof._logged_connections:
            super().log(Log.WARNING, f"Someone connect to Portspoof ({scan_type})")
            Portspoof._logged_connections.add(connection_key)

        # Xử lý cho kết nối TCP đầy đủ
        if not is_scan and self.active_sock is not None:
            try:
                super().log(Log.INFO, f"received {b}")
                self.connection_data = b
                if not super().send(self.answer):
                    return
                super().shutdown()
            except Exception as e:
                Log.write(Log.ERROR, f"Error processing connection on port {self.port} for {self.ip}: {e}")
