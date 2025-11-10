# net_socketio.py
import socketio
import threading
import queue

# ===== SERVER =====
class CoopServer:
    def __init__(self, host="0.0.0.0", port=5001):
        self.host, self.port = host, port
        self.sio = socketio.Server(cors_allowed_origins="*")
        self.app = socketio.WSGIApp(self.sio)
        self.thread = None
        self.players = {}   # sid -> {"id": int, "x": .., "y": ..}
        self.next_id = 1

        @self.sio.event
        def connect(sid, environ):
            pid = self.next_id; self.next_id += 1
            self.players[sid] = {"id": pid, "x": 0, "y": 0}
            print(f"[SERVER] Player {pid} connected ({sid})")
            self.sio.emit("welcome", {"player_id": pid}, to=sid)
            self._broadcast_state()

        @self.sio.event
        def move(sid, data):
            if sid in self.players:
                p = self.players[sid]
                p["x"] = int(data.get("x", 0))
                p["y"] = int(data.get("y", 0))
                self._broadcast_state()

        @self.sio.event
        def disconnect(sid):
            if sid in self.players:
                print(f"[SERVER] Player {self.players[sid]['id']} disconnected")
                del self.players[sid]
                self._broadcast_state()

    def _broadcast_state(self):
        self.sio.emit("state", {"type": "state", "players": list(self.players.values())})

    def start(self):
        import eventlet
        print(f"[SERVER] Socket.IO on {self.host}:{self.port}")
        self.thread = threading.Thread(
            target=lambda: eventlet.wsgi.server(eventlet.listen((self.host, self.port)), self.app),
            daemon=True
        )
        self.thread.start()


# ===== CLIENT =====
class CoopClient:
    def __init__(self, server_url="http://127.0.0.1:5001"):
        self.server_url = server_url
        self.sio = socketio.Client(reconnection=True)
        self.player_id = None
        self.recv_queue = queue.Queue()

        @self.sio.event
        def connect():
            print("[CLIENT] Connected")

        @self.sio.event
        def welcome(data):
            self.player_id = data.get("player_id")
            print("[CLIENT] My ID:", self.player_id)

        @self.sio.event
        def state(data):
            self.recv_queue.put(data)

        @self.sio.event
        def disconnect():
            print("[CLIENT] Disconnected")

    def start(self):
        print(f"[CLIENT] Connecting to {self.server_url} ...")
        self.sio.connect(self.server_url)

    def stop(self):
        try: self.sio.disconnect()
        except: pass

    def send_pos(self, x, y):
        if self.sio.connected:
            self.sio.emit("move", {"x": int(x), "y": int(y)})

    def get_messages(self):
        out = []
        while not self.recv_queue.empty():
            out.append(self.recv_queue.get_nowait())
        return out
