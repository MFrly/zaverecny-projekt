# main.py
from settings import *
from player import Player
from npc import NPC
from sprites import *  # očekává: Sprite, CollisionSprite, KeyPart
from pytmx.util_pygame import load_pygame
from groups import AllSprites
from menu import run_menu
from pause_menu import PauseMenu

from dialog_system import DialogSystem
from network_system import NetworkSystem

import pygame
import pygame_gui


class Game:
    def __init__(self, player_name="Hráč"):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True
        self.exit_to_menu = False
        self.player_name = player_name

        # GUI
        self.manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.pause = PauseMenu(self.manager)

        # Skupiny (POZOR: nedělej AllSprites 2x)
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

        # Assety (klíče)
        self.key_img = self.load_key_image()

        # Svět
        self.setup()

    # ---------- assety ----------
    def load_key_image(self) -> pygame.Surface:
        """
        Zkusí načíst obrázek klíče. Když soubor neexistuje, vytvoří náhradní Surface,
        aby hra nespadla a klíče šly aspoň testovat.
        """
        # UPRAV si cestu podle toho, kde obrázek opravdu máš:
        path = join('data', 'images', 'items', 'key_part.png')
        try:
            surf = pygame.image.load(path).convert_alpha()
            return surf
        except Exception:
            # fallback – žlutý čtverec
            surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            surf.fill((255, 220, 0))
            return surf

    # ---------- klíče ----------
    def spawn_keys(self):
        """
        Vytvoří 3 části klíče. Tohle se volá JEDNOU v setup().
        """
        KeyPart((300, 400), 1, self.key_img, [self.all_sprites, self.item_sprites])
        KeyPart((900, 250), 2, self.key_img, [self.all_sprites, self.item_sprites])
        KeyPart((1200, 800), 3, self.key_img, [self.all_sprites, self.item_sprites])

    def check_key_pickup(self):
        """
        Kolize hráče s klíči. Klíče se po sebrání smažou (dokill=True)
        a uloží se do inventáře hráče.
        """
        if not hasattr(self, "player"):
            return

        hits = pygame.sprite.spritecollide(self.player, self.item_sprites, dokill=True)
        if not hits:
            return

        # inventář na hráči (Set je ideální)
        if not hasattr(self.player, "keys_collected"):
            self.player.keys_collected = set()

        for item in hits:
            # čekáme, že KeyPart má atribut part_id (doporučeno níže ve sprites.py)
            part_id = getattr(item, "part_id", None)
            if part_id is None:
                # fallback – když by se to jmenovalo jinak
                part_id = getattr(item, "id", None)

            if part_id is not None:
                self.player.keys_collected.add(part_id)

    # ---------- svět / mapa ----------
    def setup(self):
        tmx = load_pygame(join('data', 'maps', 'world.tmx'))

        # Tiles
        for x, y, image in tmx.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        # Objects (kolizní sprity s obrázkem)
        for obj in tmx.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        # Collisions (neviditelné hitboxy)
        for obj in tmx.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        # Entities
        for obj in tmx.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player(
                    (obj.x, obj.y),
                    self.all_sprites,
                    self.collision_sprites,
                    name=self.player_name
                )

                # inventář pro klíče (aby to bylo vždy připravené)
                self.player.keys_collected = set()

                npc_position = (obj.x, obj.y + 150)
                self.npc = NPC(npc_position, (self.all_sprites, self.npc_sprites), npc_id="villager_1")

        # Klíče (po vytvoření hráče, ať hned funguje pickup)
        self.spawn_keys()

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
                npc.rect.top - 10 - text_surf.get_height()
            )
            offset_pos = (
                int(pos[0] + self.all_sprites.offset.x),
                int(pos[1] + self.all_sprites.offset.y)
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
                    # E = start NPC dialog
                    if event.key == pygame.K_e:
                        if not self.pause.is_open() and not self.dialog.is_active():
                            npc = self.player_near_npc()
                            if npc:
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
                        self.running = False
                        self.exit_to_menu = True

                    elif action == "quit":
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

                #  kontrola sebrání klíčů
                self.check_key_pickup()

            self.manager.update(dt)

            # kreslení
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            self.draw_nameplates()

            if not self.pause.is_open():
                self.draw_interact_hint()

            self.pause.draw_overlay(self.display_surface)
            self.manager.draw_ui(self.display_surface)
            pygame.display.update()

        pygame.quit()
        self.net.shutdown()


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

        game = Game(player_name)
        game.run()

        if not game.exit_to_menu:
            running = False
