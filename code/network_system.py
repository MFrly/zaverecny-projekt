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
        print("SÍŤ: Spouštím HOST režim...")
        self.shutdown()
        self.server = CoopServer()
        self.server.start()
        # Malá pauza, aby server stihl naskočit, než se k němu klient připojí
        time.sleep(0.5) 
        self.client = CoopClient("http://127.0.0.1:5001")
        self.client.start()

    def join(self, ip: str):
        print(f"SÍŤ: Připojuji se k {ip}...")
        self.shutdown()
        # Pokud uživatel nezadal IP, zkusíme localhost
        target_ip = ip if ip else "127.0.0.1"
        self.client = CoopClient(f"http://{target_ip}:5001")
        self.client.start()

    def tick(self, player):
        # příjem dat od ostatních
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
                        status = p.get("status", "down") # <-- Změna zde: získáme směr z dat

                        if pid not in self.remote_players:
                            self.remote_players[pid] = RemotePlayer(pid, (x, y), self.all_sprites)
                        else:
                            # Změna zde: voláme set_state místo set_pos, aby se spustila animace
                            self.remote_players[pid].set_state(x, y, status)

                    # odstraň zmizelé hráče
                    for pid in list(self.remote_players.keys()):
                        if pid not in alive or (my_id is not None and pid == my_id):
                            self.remote_players[pid].kill()
                            del self.remote_players[pid]

        # odesílání tvých dat na server
        if self.client and player is not None:
            now = time.time()
            if now - self.last_send >= self.send_rate:
                self.last_send = now
                # Změna zde: do balíčku přidáme tvůj aktuální status (směr)
                self.client.sio.emit('move', {
                    'x': player.hitbox_rect.centerx,
                    'y': player.hitbox_rect.centery,
                    'status': player.status
                })

        # odesílání
        if self.client and player is not None:
            now = time.time()
            if now - self.last_send >= self.send_rate:
                self.last_send = now
        # Přidáme status do odesílaných dat
                self.client.sio.emit('move', {
                'x': player.hitbox_rect.centerx,
                'y': player.hitbox_rect.centery,
                'status': player.status  # TADY přidáváme informaci o animaci
                })