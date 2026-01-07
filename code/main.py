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
            return [
                f"Už máš {have}/3 části klíče.",
                f"Ještě ti chybí {missing}."
            ]

        return [
            "Skvěle! Máš všechny tři části!",
            "Spojím je v jeden klíč..."
        ]

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
    def setup(self):
        tmx = load_pygame(join("data", "maps", "world.tmx"))

        # Tiles
        for x, y, image in tmx.get_layer_by_name("Ground").tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        # Objects (kolizní sprity s obrázkem)
        for obj in tmx.get_layer_by_name("Objects"):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        # Collisions (neviditelné hitboxy)
        for obj in tmx.get_layer_by_name("Collisions"):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        # Entities
        player_spawned = False
        for obj in tmx.get_layer_by_name("Entities"):
            if obj.name == "Player":
                player_spawned = True

                self.player = Player(
                    (obj.x, obj.y),
                    self.all_sprites,
                    self.collision_sprites,
                    name=self.player_name,
                )

                # jistota
                if not hasattr(self.player, "key_parts"):
                    self.player.key_parts = set()
                if not hasattr(self.player, "has_master_key"):
                    self.player.has_master_key = False

                # načti progress z DB
                self.load_player_progress()

                npc_position = (obj.x, obj.y + 150)
                self.npc = NPC(npc_position, (self.all_sprites, self.npc_sprites), npc_id="villager_1")

                # klíče spawn až po hráči a až po loadu (aby se nespawnovaly duplicitně)
                self.spawn_keys()

        if not player_spawned:
            raise RuntimeError("V layeru 'Entities' chybí objekt s name == 'Player'.")

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
                    # uložit i při zavření okna
                    self.save_player_progress()
                    self.running = False
                    self.exit_to_menu = False

                if event.type == pygame.KEYDOWN:
                    # E = start NPC dialog
                    if event.key == pygame.K_e:
                        if not self.pause.is_open() and not self.dialog.is_active():
                            npc = self.player_near_npc()
                            if npc:
                                if npc.npc_id == "villager_1" and hasattr(self.dialog, "start_custom_dialog"):
                                    # nejdřív případně slož klíč, pak vyrob text
                                    self.try_craft_master_key()
                                    lines = self.get_npc_key_dialog_lines()
                                    self.dialog.start_custom_dialog(self.player, lines)
                                else:
                                    self.dialog.start_dialog(self.player, npc)

                    # Enter = další věta dialogu
                    if event.key == pygame.K_RETURN and self.dialog.is_active():
                        self.dialog.next_dialog(self.player)

                    # ESC = pauza
                    if event.key == pygame.K_ESCAPE:
                        if self.pause.is_open():
                            self.pause.close()
                            self.player.set_input_enabled(True)
                        else:
                            self.pause.open()
                            self.player.set_input_enabled(False)

                # UI
                self.manager.process_events(event)

                # Pauza – akce
                if self.pause.is_open():
                    action = self.pause.process_event(event)

                    if action == "resume":
                        self.pause.close()
                        self.player.set_input_enabled(True)

                    elif action == "menu":
                        # uložit při návratu do menu
                        self.save_player_progress()
                        self.running = False
                        self.exit_to_menu = True

                    elif action == "quit":
                        # uložit při quit
                        self.save_player_progress()
                        self.running = False
                        self.exit_to_menu = False

                    elif isinstance(action, tuple):
                        name, payload = action

                        if name == "coop_host":
                            self.net.host()
                            self.pause.close()
                            self.player.set_input_enabled(True)

                        elif name == "coop_join":
                            ip = payload or "127.0.0.1"
                            self.net.join(ip)
                            self.pause.close()
                            self.player.set_input_enabled(True)

            # update jen mimo pauzu a dialog
            if not self.pause.is_open() and not self.dialog.is_active():
                self.net.tick(self.player)
                self.all_sprites.update(dt)
                self.check_key_pickup()

            self.manager.update(dt)

            # kreslení
            self.display_surface.fill("black")
            self.all_sprites.draw(self.player.rect.center)
            self.draw_nameplates()

            if not self.pause.is_open():
                self.draw_interact_hint()

            self.pause.draw_overlay(self.display_surface)
            self.manager.draw_ui(self.display_surface)
            pygame.display.update()

        # poslední save jako pojistka
        self.save_player_progress()

        pygame.quit()
        self.net.shutdown()


if __name__ == "__main__":
    running = True
    while running:
        choice = run_menu()
        if not isinstance(choice, dict):
            break

        player_name = choice.get("player_name", "Hráč")
        action = choice.get("action")
        if action in ("quit", None):
            break

        game = Game(player_name)
        game.run()

        if not game.exit_to_menu:
            running = False
