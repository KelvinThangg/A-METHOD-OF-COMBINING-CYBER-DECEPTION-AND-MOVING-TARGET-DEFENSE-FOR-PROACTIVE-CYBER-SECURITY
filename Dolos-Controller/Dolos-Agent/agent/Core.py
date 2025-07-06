from log import Log
from connection import Connection
import socket
import select

class Core:
    def __init__(self, sock, port, active_sock, ip):
        self._sock = sock
        self._port = port
        self._active_sock = active_sock
        self._ip = ip
        self._connection_data = b""
        self._active = True

    @property
    def sock(self):
        return self._sock

    @sock.setter
    def sock(self, val):
        self._sock = val

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, val):
        self._port = val

    @property
    def active_sock(self):
        return self._active_sock

    @active_sock.setter
    def active_sock(self, val):
        self._active_sock = val

    @property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, val):
        self._ip = val

    @property
    def connection_data(self):
        return self._connection_data

    @connection_data.setter
    def connection_data(self, val):
        self._connection_data += val

    def log(self, lv, s):
        Log.write(lv, "[{}::{}]: {}".format(self.ip, self.port, s))

    def shutdown(self):
        if not self._active:
            return
        self._active = False
        try:
            Connection.shutdown(self.sock, self.active_sock)
            self.log(Log.DEBUG, f"Socket closed for {self.ip}:{self.port}")
        except Exception as e:
            self.log(Log.WARNING, f"Error shutting down socket: {e}")

    def send(self, data):
        if not self._active or self.active_sock is None:
            self.log(Log.WARNING, "Attempted to send on inactive/closed socket")
            return False
        try:
            self.active_sock.setblocking(False)
            ready = select.select([], [self.active_sock], [], 0.1)[1]
            if not ready:
                self.log(Log.WARNING, "Socket not writable")
                self.shutdown()
                return False
            Connection.send(self.sock, self.active_sock, data, len(data))
            self.log(Log.DEBUG, f"Sent to {self.ip}:{self.port}: {data[:100]}...")
            return True
        except socket.error as e:
            self.log(Log.ERROR, f"Error sending data to {self.ip}:{self.port}: {e}")
            self.shutdown()
            return False
        except Exception as e:
            self.log(Log.ERROR, f"Unexpected error sending data to {self.ip}:{self.port}: {e}")
            self.shutdown()
            return False
