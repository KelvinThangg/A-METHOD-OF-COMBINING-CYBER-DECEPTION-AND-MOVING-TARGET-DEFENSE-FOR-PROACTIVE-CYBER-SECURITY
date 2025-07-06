from contextlib import contextmanager
from Core import Core
from log import Log
import subprocess
import sqlite3
import time

@contextmanager
def db_helper(path):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    yield cursor
    try:
        conn.commit()
    finally:
        conn.close()

class Invisiport(Core):
    PORT = 443
    _logged_connections = set()

    def __init__(self, sock, port, active_sock, ip):
        super().__init__(sock, port, active_sock, ip)
        self.__startup_blacklist()

    def __startup_blacklist(self):
        with db_helper('invisiport_blacklist.db') as c:
            try:
                c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='blacklist'")
                if c.fetchall()[0][0] == 0:
                    c.execute('''CREATE TABLE blacklist (
                        ip TEXT NOT NULL,
                        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(ip))''')
            except Exception as e:
                super().log(Log.WARNING, f"Exception occurred: {e}")

    def __add_blacklist(self, ip):
        with db_helper('invisiport_blacklist.db') as c:
            try:
                c.execute("INSERT INTO blacklist (ip) VALUES(?)", (ip,))
                super().log(Log.INFO, f"Add IP {ip} to blacklist")
            except Exception as e:
                super().log(Log.WARNING, f"Exception occurred: {e}")

    def __check_blacklist(self, ip):
        with db_helper('invisiport_blacklist.db') as c:
            try:
                c.execute("SELECT ip FROM blacklist WHERE ip=?", (ip,))
                return bool(c.fetchone())
            except Exception as e:
                super().log(Log.WARNING, f"Exception occurred: {e}")
                return False

    def __blacklist(self, ip, port, scan_type):
        if self.__check_blacklist(ip):
            return

        current_time = time.time()
        connection_key = (ip, port, current_time)
        if connection_key not in Invisiport._logged_connections:
            super().log(Log.WARNING, f"Someone connect to Invisiport ({scan_type} scan)")
            Invisiport._logged_connections.add(connection_key)

        params = f"iptables -A INPUT -s {ip} -p tcp ! --destination-port {self.PORT} -j DROP"
        try:
            subprocess.run(params, shell=True, check=True)
            super().log(Log.INFO, f"Add rule to block IP {ip} in iptables")
        except Exception as e:
            Log.write(Log.ERROR, f"Error blocking IP {ip}: {e}")

        params = f"iptables -t nat -A PREROUTING -s {ip} -p tcp --dport {port} -j REDIRECT --to-port {self.PORT}"
        try:
            subprocess.run(params, shell=True, check=True)
            super().log(Log.INFO, f"Add rule to redirect packet from IP {ip} to port {self.PORT}")
        except Exception as e:
            Log.write(Log.ERROR, f"Error redirecting packet for IP {ip}: {e}")

        self.__add_blacklist(ip)

    def start(self, b, is_scan=False, scan_type=None):
        current_time = time.time()
        connection_key = (self.ip, self.port, current_time)
        
        # Xóa các bản ghi cũ
        Invisiport._logged_connections = {(ip, port, t) for ip, port, t in Invisiport._logged_connections if current_time - t < 1}
        
        # Thực hiện blacklist cho mọi loại quét hoặc kết nối
        self.__blacklist(self.ip, self.port, scan_type or "TCP Connect")

        # Xử lý cho kết nối TCP đầy đủ
        if not is_scan and self.active_sock is not None:
            try:
                super().log(Log.INFO, f"received {b}")
                super().shutdown()
            except Exception as e:
                Log.write(Log.ERROR, f"Error processing connection on port {self.port} for {self.ip}: {e}")
        else:
            super().shutdown()
