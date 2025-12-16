# main.py
from settings import *
from player import Player
from npc import NPC
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites
from menu import run_menu
from pause_menu import PauseMenu
from remote_player import RemotePlayer
from net_socketio import CoopServer, CoopClient
from dialogues import NPC_DIALOGUES


import pygame
import pygame_gui
import time


class Game:
    def __init__(self, player_name="Hráč"):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True
        self.exit_to_menu = False  # signál pro návrat do hlavního menu
        self.player_name = player_name

        #Dialogové okno
        self.active_dialogue = None
        self.dialog_index = 0
        self.current_npc = None


        # GUI
        self.manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.text_entry = None
        self.dialog_box = None
        self.submit_button = None
        self.popup_active = False

        # Pauza (oddělené menu)
        self.pause = PauseMenu(self.manager)

        # Skupiny
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.npc_sprites = pygame.sprite.Group()

        # Font pro hinty
        self.font = pygame.font.SysFont(None, 24)
        self.name_font = pygame.font.SysFont(None, 20)

        # Síť (Socket.IO)
        self.server = None                 # CoopServer (jen když hostuji)
        self.client = None                 # CoopClient (host i join)
        self.remote_players = {}           # pid -> RemotePlayer
        self.last_send = 0.0
        self.send_rate = 1 / 15            # posílání pozice ~15×/s

        self.setup()

    # ---------- svět / mapa ----------
    def setup(self):
        tmx = load_pygame(join('data', 'maps', 'world.tmx'))

        for x, y, image in tmx.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        for obj in tmx.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in tmx.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in tmx.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y),self.all_sprites,self.collision_sprites,name=self.player_name)

                npc_position = (obj.x, obj.y + 150)
                self.npc = NPC(npc_position,(self.all_sprites, self.npc_sprites),npc_id="villager")


    # ---------- síť: pomocné ----------
    def _net_shutdown(self):
        if self.client:
            self.client.stop()
            self.client = None
        # server běží v daemon vlákně, explicitní stop není nutný (ukončí se s procesem)
        self.remote_players.clear()

    def _net_tick(self):
        """Přijmi stavy ostatních hráčů a pošli vlastní pozici."""
        # Příjem
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
                        # vynech vlastní entitu (tu máš lokálně jako Player)
                        if my_id is not None and pid == my_id:
                            continue

                        x, y = int(p.get("x", 0)), int(p.get("y", 0))
                        if pid not in self.remote_players:
                            self.remote_players[pid] = RemotePlayer(pid, (x, y), self.all_sprites)
                        else:
                            self.remote_players[pid].set_pos(x, y)

                    # Odstranění hráčů, kteří zmizeli
                    for pid in list(self.remote_players.keys()):
                        if pid not in alive or (my_id is not None and pid == my_id):
                            self.remote_players[pid].kill()
                            del self.remote_players[pid]

        # Odeslání mojí pozice
        if self.client and hasattr(self, "player"):
            now = time.time()
            if now - self.last_send >= self.send_rate:
                self.last_send = now
                self.client.send_pos(self.player.rect.centerx, self.player.rect.centery)

    # ---------- NPC interakce ----------
    def check_npc_interaction(self):
        if not self.popup_active:
            npc = self.player_near_npc()
            if npc:
                self.start_dialog(npc)

    def start_dialog(self, npc):
        self.popup_active = True
        self.player.set_input_enabled(False)

        self.current_npc = npc
        self.active_dialogue = NPC_DIALOGUES.get(npc.npc_id, [])
        self.dialog_index = 0

        self.show_dialog_line()

    def show_dialog_line(self):
        if self.dialog_box:
            self.dialog_box.kill()

        text = self.active_dialogue[self.dialog_index]
        self.dialog_box = pygame_gui.elements.UITextBox(
            text,
            pygame.Rect(WINDOW_WIDTH//2 - 220, WINDOW_HEIGHT - 180, 440, 100),
            self.manager
    )
        
    def next_dialog(self):
        self.dialog_index += 1
        if self.dialog_index >= len(self.active_dialogue):
            self.end_dialog()
        else:
            self.show_dialog_line()

    def end_dialog(self):
        self.popup_active = False
        self.player.set_input_enabled(True)
        self.active_dialogue = None
        self.dialog_index = 0
        self.current_npc = None

        if self.dialog_box:
            self.dialog_box.kill()
            self.dialog_box = None

    def create_dialog(self):
        self.popup_active = True
        self.player.set_input_enabled(False)

        self.dialog_box = pygame_gui.elements.UITextBox(
            "Ahoj! Mám pro tebe otázku: Kolik je 1+1?",
            pygame.Rect((WINDOW_WIDTH // 2 - 180, WINDOW_HEIGHT // 2 - 110), (360, 80)),
            self.manager
        )
        self.text_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 10), (200, 40)),
            manager=self.manager
        )
        self.submit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT // 2 + 40), (100, 36)),
            text='Odeslat',
            manager=self.manager
        )

    def close_dialog(self):
        self.popup_active = False
        self.player.set_input_enabled(True)
        if self.text_entry:
            self.text_entry.kill(); self.text_entry = None
        if self.submit_button:
            self.submit_button.kill(); self.submit_button = None
        if self.dialog_box:
            self.dialog_box.kill(); self.dialog_box = None

    def handle_popup(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.submit_button:
            answer = self.text_entry.get_text()
            print("Správně! Dobrá práce!" if answer.strip() == "2" else "Špatně, zkus to příště!")
            self.close_dialog()

    def player_near_npc(self):
        for npc in self.npc_sprites:
            if self.player.hitbox_rect.colliderect(npc.hitbox_rect):
                return npc
        return None

    def draw_interact_hint(self):
        if self.popup_active or self.pause.is_open():
            return
        npc = self.player_near_npc()
        if npc:
            text_surf = self.font.render("[E] Mluvit", True, (255, 255, 255))
            pos = (
                npc.rect.centerx - text_surf.get_width() // 2,
                npc.rect.top - 10 - text_surf.get_height()
            )
            offset_pos = (
                int(pos[0] + self.all_sprites.offset.x),
                int(pos[1] + self.all_sprites.offset.y)
            )
            self.display_surface.blit(text_surf, offset_pos)

    def draw_nameplates(self):
        # lokální hráč
        entities = [self.player]

        # remote hráči (pokud nějaký co-op běží)
        if hasattr(self, "remote_players"):
            entities.extend(self.remote_players.values())

        for ent in entities:
            if not hasattr(ent, "name"):
                continue
            text_surf = self.name_font.render(ent.name, True, (255, 255, 0))
            x = ent.rect.centerx - text_surf.get_width() // 2
            y = ent.rect.top - text_surf.get_height() - 4  # těsně nad hlavou

            # posun podle kamery (stejná logika jako u [E] Mluvit)
            offset_pos = (
                int(x + self.all_sprites.offset.x),
                int(y + self.all_sprites.offset.y)
            )
            self.display_surface.blit(text_surf, offset_pos)


    # ---------- hlavní smyčka ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.exit_to_menu = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.popup_active:
                        self.next_dialog()
                        

                    if event.key == pygame.K_ESCAPE:
                        if self.pause.is_open():
                            # stejné jako „Pokračovat“
                            self.pause.close()
                            self.player.set_input_enabled(True)
                        else:
                            self.pause.open()
                            self.player.set_input_enabled(False)

                # UI manager
                self.manager.process_events(event)

                # Dialog okno
                if self.popup_active:
                    self.handle_popup(event)

                # Pauza – zpracuj akce
                if self.pause.is_open():
                    action = self.pause.process_event(event)
                    if action == "resume":
                        self.pause.close()
                        self.player.set_input_enabled(True)

                    elif action == "menu":
                        self.running = False
                        self.exit_to_menu = True

                    elif action == "quit":
                        self.running = False
                        self.exit_to_menu = False

                    elif isinstance(action, tuple):
                        name, payload = action
                        if name == "coop_host":
                            print("CO-OP: HOST – spouštím server i lokální klient")
                            self._net_shutdown()
                            self.server = CoopServer(); self.server.start()
                            time.sleep(0.3)  # krátká prodleva pro start serveru
                            self.client = CoopClient("http://127.0.0.1:5001"); self.client.start()
                            self.pause.close(); self.player.set_input_enabled(True)

                        elif name == "coop_join":
                            ip = payload or "127.0.0.1"
                            print(f"CO-OP: JOIN {ip}")
                            self._net_shutdown()
                            self.client = CoopClient(f"http://{ip}:5001"); self.client.start()
                            self.pause.close(); self.player.set_input_enabled(True)

            # Síť pouze mimo pauzu a mimo dialog
            if not self.pause.is_open() and not self.popup_active:
                self._net_tick()

            # Update světa
            if not self.pause.is_open() and not self.popup_active:
                self.all_sprites.update(dt)
            self.manager.update(dt)

            # Kreslení
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            if not self.pause.is_open():
                self.draw_interact_hint()

            # Ztmavení pod pauzou
            self.pause.draw_overlay(self.display_surface)

            self.manager.draw_ui(self.display_surface)
            pygame.display.update()

        pygame.quit()
        self._net_shutdown()


if __name__ == '__main__':
    running = True
    while running:
        choice = run_menu()
        if not isinstance(choice, dict):
            break

        player_name = choice.get("player_name", "Hráč")
        action = choice.get("action")
        if action in ('quit', None):
            break

        # Start hry (Co-op lze spustit kdykoliv z pauzy; tady necháme single)
        game = Game(player_name)

        game.run()

        if not game.exit_to_menu:
            running = False
