# main.py
from settings import *
from player import Player
from npc import NPC
from sprites import *  # Sprite, CollisionSprite, KeyPart
from pytmx.util_pygame import load_pygame
from groups import AllSprites
from menu import run_menu
from pause_menu import PauseMenu

from database import init_db, save_player, load_player

from dialog_system import DialogSystem
from network_system import NetworkSystem

import pygame
import pygame_gui


class Game:
    def __init__(self, player_name="Hráč"):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Survivor")
        self.clock = pygame.time.Clock()
        self.running = True
        self.exit_to_menu = False
        self.player_name = player_name

        # DB init
        init_db()

        # GUI
        self.manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.pause = PauseMenu(self.manager)

        # Skupiny
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()
        self.npc_sprites = pygame.sprite.Group()

        # Systémy
        self.dialog = DialogSystem(self.manager)
        self.net = NetworkSystem(self.all_sprites)

        # Fonty
        self.font = pygame.font.SysFont(None, 24)
        self.name_font = pygame.font.SysFont(None, 20)

        # Asset klíče (fallback když nenajde soubor)
        self.key_img = self.load_key_image()

        # Svět
        self.setup()

    # ---------- assety ----------
    def load_key_image(self) -> pygame.Surface:
        path = join("data", "graphics", "items", "key_part.png")
        try:
            return pygame.image.load(path).convert_alpha()
        except Exception:
            surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            surf.fill((255, 220, 0))
            return surf

    # ---------- klíče ----------
    def spawn_keys(self):
        """Vytvoří 3 části klíče poblíž hráče (aby nebyly mimo hratelnou část)."""
        # Když už má master key, nespawnuj nic
        if getattr(self.player, "has_master_key", False):
            return

        # Když už má všechny 3 části, taky nespawnuj (ať se neduplikují)
        if len(getattr(self.player, "key_parts", set())) >= 3:
            return

        px, py = self.player.rect.center

        positions = [
            (px - 250, py + 120),  # část 1
            (px + 300, py - 80),   # část 2
            (px + 100, py + 320),  # část 3
        ]

        # spawnuj jen ty části, které hráč ještě nemá
        already = getattr(self.player, "key_parts", set())
        for part_id, pos in enumerate(positions, start=1):
            if part_id in already:
                continue
            KeyPart(pos, part_id, self.key_img, [self.all_sprites, self.item_sprites])

        print("Spawned key parts at:", [(k.part_id, k.rect.center) for k in self.item_sprites])

    def check_key_pickup(self):
        """Kolize přes player.hitbox_rect (a key.hitbox_rect pokud existuje)."""
        if not hasattr(self, "player"):
            return

        for key in list(self.item_sprites):
            key_hitbox = getattr(key, "hitbox_rect", key.rect)
            if self.player.hitbox_rect.colliderect(key_hitbox):
                self.player.key_parts.add(key.part_id)
                key.kill()

    # ---------- NPC text podle klíčů ----------
    def get_npc_key_dialog_lines(self):
        have = len(self.player.key_parts)
        missing = 3 - have

        if self.player.has_master_key:
            return [
                "Výborně! Klíč je hotový.",
                "Brána by teď měla jít otevřít. Pokračuj dál."
            ]

        if have == 0:
            return [
                "Temnota se šíří lesem...",
                "Najdi tři části klíče a vrať se ke mně."
            ]

        if have < 3:
            return [f"Už máš {have}/3 části klíče. Najdi zbytek!"]

        return ["Skvěle! Máš všechno. Spojím ti je v Master Key! Znovu se mnou promluv."]

    def try_craft_master_key(self):
        """Když má hráč 3 části a mluví s NPC, složíme klíč."""
        if not self.player.has_master_key and len(self.player.key_parts) == 3:
            self.player.has_master_key = True
            self.player.key_parts.clear()

            # když se složí klíč, smažeme případné zbývající itemy na mapě
            for key in list(self.item_sprites):
                key.kill()

    # ---------- uložení / načtení ----------
    def load_player_progress(self):
        data = load_player(self.player_name)
        if data:
            self.player.key_parts = data["key_parts"]
            self.player.has_master_key = data["has_master_key"]
            print("Loaded player:", self.player_name, data)
        else:
            print("No save found for:", self.player_name)

    def save_player_progress(self):
        try:
            save_player(self.player_name, self.player.key_parts, self.player.has_master_key)
            print("Saved player:", self.player_name)
        except Exception as e:
            print("SAVE ERROR:", e)

    # ---------- svět / mapa ----------
    def setup(self, map_path="data/maps/world.tmx"):
        # 1. Načtení mapy
        try:
            tmx = load_pygame(join(map_path))
        except Exception as e:
            print(f"CHYBA: Nepodařilo se načíst mapu {map_path}: {e}")
            return

        # 2. Reset logiky
        self.enemy_spawn_positions = []
        self.exit_rects = []
        self.collision_sprites.empty()
        self.item_sprites.empty()
        self.npc_sprites.empty()

        # 3. Vyčištění grafiky (ZACHOVÁNÍ OSTATNÍCH HRÁČŮ)
        for sprite in self.all_sprites:
            # Zjistíme, zda sprite patří některému ze vzdálených hráčů
            is_remote = any(sprite == remote for remote in self.net.remote_players.values())
            
            # Smažeme jen pokud to není náš hráč A ZÁROVEŇ to není vzdálený hráč
            if sprite != self.player and not is_remote:
                sprite.kill()

        # 4. Načtení vrstev
        try:
            for x, y, image in tmx.get_layer_by_name("Ground").tiles():
                Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)
        except ValueError: pass

        try:
            for obj in tmx.get_layer_by_name("Objects"):
                CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))
        except ValueError: pass

        try:
            for obj in tmx.get_layer_by_name("Collisions"):
                CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)
        except ValueError: pass

        # 5. Entity (Hráč, NPC, atd.)
        player_spawned = False
        try:
            for obj in tmx.get_layer_by_name("Entities"):
                obj_name = str(obj.name).lower() if obj.name else ""

                if obj_name == "player":
                    player_spawned = True
                    if hasattr(self, "player") and self.player:
                        self.player.rect.center = (obj.x, obj.y)
                        self.player.hitbox_rect.center = (obj.x, obj.y)
                    else:
                        self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites, name=self.player_name)
                        self.player.key_parts = set()
                        self.player.has_master_key = False
                        self.load_player_progress()

                elif obj_name == "enemy":
                    self.enemy_spawn_positions.append((obj.x, obj.y))
        except ValueError: pass

        if player_spawned:
            self.spawn_entities_at_enemy_spots()
    def change_level(self, new_map):
        print(f"Přechod do další úrovně: {new_map}")
        
        # 1. Vyčistíme všechny sprity kromě síťových entit (pokud chceš zachovat připojení)
        for sprite in self.all_sprites:
            sprite.kill()
        
        # 2. Znovu zavoláme setup s novou cestou k mapě
        # Ujisti se, že setup přijímá parametr map_path
        self.setup(new_map)

    def spawn_entities_at_enemy_spots(self):
        import random
        # Zamícháme seznam pozic, aby to bylo pokaždé jinak
        spots = self.enemy_spawn_positions.copy()
        random.shuffle(spots)

        # 1. Spawn NPC na první náhodný spot
        npc_pos = spots.pop(0)
        self.npc = NPC(npc_pos, (self.all_sprites, self.npc_sprites), npc_id="villager_1")

        # 2. Spawn zbývajících klíčů na další spoty
        # Zjistíme, které části klíče hráč ještě NEMÁ
        already_have = getattr(self.player, "key_parts", set())
        needed_ids = [1, 2, 3]
        for part_id in already_have:
            if part_id in needed_ids:
                needed_ids.remove(part_id)

        # Pokud hráč už má Master Key, nepotřebuje žádné části
        if getattr(self.player, "has_master_key", False):
            needed_ids = []

        # Rozmístíme klíče na zbývající spoty
        for part_id in needed_ids:
            if spots:
                pos = spots.pop(0)
                KeyPart(pos, part_id, self.key_img, [self.all_sprites, self.item_sprites])
            else:
                print(f"Nedostatek 'Enemy' bodů v mapě pro spawn klíče {part_id}")

        print(f"Rozmístěno na 'Enemy' body: NPC na {npc_pos}, klíče na zbývající body.")
    # ---------- NPC blízkost ----------
    def player_near_npc(self):
        for npc in self.npc_sprites:
            if self.player.hitbox_rect.colliderect(npc.hitbox_rect):
                return npc
        return None

    # ---------- hint ----------
    def draw_interact_hint(self):
        if self.dialog.is_active() or self.pause.is_open():
            return

        npc = self.player_near_npc()
        if npc:
            text_surf = self.font.render("[E] Mluvit", True, (255, 255, 255))
            pos = (
                npc.rect.centerx - text_surf.get_width() // 2,
                npc.rect.top - 10 - text_surf.get_height(),
            )
            offset_pos = (
                int(pos[0] + self.all_sprites.offset.x),
                int(pos[1] + self.all_sprites.offset.y),
            )
            self.display_surface.blit(text_surf, offset_pos)

    def draw_nameplates(self):
        entities = [self.player]
        entities.extend(self.net.remote_players.values())

        for ent in entities:
            if not hasattr(ent, "name"):
                continue
            text_surf = self.name_font.render(ent.name, True, (255, 255, 0))
            x = ent.rect.centerx - text_surf.get_width() // 2
            y = ent.rect.top - text_surf.get_height() - 4
            offset_pos = (
                int(x + self.all_sprites.offset.x),
                int(y + self.all_sprites.offset.y),
            )
            self.display_surface.blit(text_surf, offset_pos)

    # ---------- hlavní smyčka ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_player_progress()
                    self.running = False
                    self.exit_to_menu = False

                if event.type == pygame.KEYDOWN:
                    # E = Interakce
                    if event.key == pygame.K_e:
                        if not self.pause.is_open() and not self.dialog.is_active():
                            npc = self.player_near_npc()
                            if npc:
                                if npc.npc_id == "villager_1":
                                    self.try_craft_master_key()
                                    lines = self.get_npc_key_dialog_lines()
                                    self.dialog.start_custom_dialog(self.player, lines)
                                else:
                                    self.dialog.start_dialog(self.player, npc)

                    # ENTER = Další dialog
                    if event.key == pygame.K_RETURN and self.dialog.is_active():
                        self.dialog.next_dialog(self.player)

                    # --- LOGIKA TELEPORTU (Y/N) ---
                    if self.dialog.is_active() and getattr(self.player, "has_master_key", False):
                        if event.key == pygame.K_y:
                            print("Teleportuji do Levelu 2...")
                            self.dialog.active = False
                            self.player.set_input_enabled(True)
                            
                            # Načtení nové mapy
                            self.setup("data/maps/l2_world.tmx")
                            
                            # OKAMŽITÁ SYNCHRONIZACE: Oznámíme serveru novou pozici v nové mapě
                            self.net.tick(self.player)
                        
                        elif event.key == pygame.K_n:
                            self.dialog.active = False
                            self.player.set_input_enabled(True)

                    # ESC = Pauza
                    if event.key == pygame.K_ESCAPE:
                        if self.pause.is_open():
                            self.pause.close()
                            self.player.set_input_enabled(True)
                        else:
                            self.pause.open()
                            self.player.set_input_enabled(False)

                self.manager.process_events(event)

                # Pauza akce
                if self.pause.is_open():
                    action = self.pause.process_event(event)
                    if action == "resume":
                        self.pause.close()
                        self.player.set_input_enabled(True)
                    elif action == "menu":
                        self.save_player_progress(); self.running = False; self.exit_to_menu = True
                    elif action == "quit":
                        self.save_player_progress(); self.running = False; self.exit_to_menu = False
                    elif isinstance(action, tuple):
                        name, payload = action
                        if name == "coop_host": self.net.host(); self.pause.close(); self.player.set_input_enabled(True)
                        elif name == "coop_join": self.net.join(payload or "127.0.0.1"); self.pause.close(); self.player.set_input_enabled(True)

            # --- UPDATE ---
            if not self.pause.is_open() and not self.dialog.is_active():
                self.net.tick(self.player)
                self.all_sprites.update(dt)
                self.check_key_pickup()

            self.manager.update(dt)

            # --- KRESLENÍ ---
            self.display_surface.fill("black")
            
            # Vykreslení světa centrovaného na hráče
            self.all_sprites.draw(self.player.rect.center)
            
            # Vykreslení jmenovek (pro nás i vzdálené hráče)
            self.draw_nameplates()

            if not self.pause.is_open():
                self.draw_interact_hint()

            self.pause.draw_overlay(self.display_surface)
            self.manager.draw_ui(self.display_surface)
            pygame.display.update()

        self.save_player_progress()
        self.net.shutdown()
        pygame.quit()

if __name__ == "__main__":
    running = True
    while running:
        # 1. Spustíme menu a získáme data (akce, jméno, ip)
        choice = run_menu() 
        
        # Pokud menu vrátí quit nebo nic, ukončíme aplikaci
        if not choice or choice.get("action") == "quit":
            break

        player_name = choice.get("player_name", "Hráč")
        action = choice.get("action")
        target_ip = choice.get("ip", "127.0.0.1")

        # 2. Vytvoříme instanci hry
        game = Game(player_name)

        # 3. REAKCE NA VOLBU Z MENU
        if action == "coop_host":
            game.net.host()  # Spustí server i klienta
        elif action == "coop_join":
            game.net.join(target_ip)  # Připojí se k zadané IP
        elif action == "load":
            # Pokud máš metodu load_player_progress, můžeš ji vynutit zde
            # ale většinou ji volá setup() automaticky
            pass

        # 4. Spuštění samotné herní smyčky
        game.run()

        # Pokud hráč vyskočil do menu (exit_to_menu), smyčka while running 
        # se zopakuje a znovu ukáže menu. Pokud zavřel křížkem, running bude False.
        if not getattr(game, "exit_to_menu", False):
            running = False