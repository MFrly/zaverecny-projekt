# network_system.py
import time

from remote_player import RemotePlayer
from net_socketio import CoopServer, CoopClient


class NetworkSystem:
    """Socket.IO co-op: server/klient + remote hráči."""

    def __init__(self, all_sprites):
        self.all_sprites = all_sprites

        self.server = None
        self.client = None
        self.remote_players = {}

        self.last_send = 0.0
        self.send_rate = 1 / 15

    def shutdown(self):
        if self.client:
            self.client.stop()
            self.client = None
        self.remote_players.clear()

    def host(self):
        print("CO-OP: HOST – spouštím server i lokální klient")
        self.shutdown()
        self.server = CoopServer()
        self.server.start()
        time.sleep(0.3)
        self.client = CoopClient("http://127.0.0.1:5001")
        self.client.start()

    def join(self, ip: str):
        print(f"CO-OP: JOIN {ip}")
        self.shutdown()
        self.client = CoopClient(f"http://{ip}:5001")
        self.client.start()

    def tick(self, player):
        # příjem
        if self.client:
            for msg in self.client.get_messages():
                if msg.get("type") == "state":
                    players = msg.get("players", [])
                    my_id = self.client.player_id
                    alive = set()

                    for p in players:
                        pid = p.get("id")
                        if pid is None:
                            continue

                        alive.add(pid)

                        # přeskoč vlastní entitu
                        if my_id is not None and pid == my_id:
                            continue

                        x, y = int(p.get("x", 0)), int(p.get("y", 0))
                        if pid not in self.remote_players:
                            self.remote_players[pid] = RemotePlayer(pid, (x, y), self.all_sprites)
                        else:
                            self.remote_players[pid].set_pos(x, y)

                    # odstraň zmizelé
                    for pid in list(self.remote_players.keys()):
                        if pid not in alive or (my_id is not None and pid == my_id):
                            self.remote_players[pid].kill()
                            del self.remote_players[pid]

        # odesílání
        if self.client and player is not None:
            now = time.time()
            if now - self.last_send >= self.send_rate:
                self.last_send = now
                self.client.send_pos(player.rect.centerx, player.rect.centery)
