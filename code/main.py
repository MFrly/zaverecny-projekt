# main.py
from settings import *
from player import Player
from npc import NPC
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites
from menu import run_menu
from pause_menu import PauseMenu
import pygame
import pygame_gui

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True
        self.exit_to_menu = False  # signál pro návrat do hlavního menu

        # GUI
        self.manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.text_entry = None
        self.dialog_box = None
        self.submit_button = None
        self.popup_active = False

        # Pauza (nově přes PauseMenu)
        self.pause = PauseMenu(self.manager)

        # groups 
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.npc_sprites = pygame.sprite.Group()

        # font pro hinty
        self.font = pygame.font.SysFont(None, 24)

        self.setup()

    def setup(self):
        map = load_pygame(join('data', 'maps', 'world.tmx'))

        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
                npc_position = (obj.x, obj.y + 150)
                self.npc = NPC(npc_position, (self.all_sprites, self.npc_sprites))

    # ====== NPC interakce ======
    def player_near_npc(self):
        for npc in self.npc_sprites:
            if self.player.hitbox_rect.colliderect(npc.hitbox_rect):
                return npc
        return None

    def check_npc_interaction(self):
        if not self.popup_active:
            npc = self.player_near_npc()
            if npc:
                self.create_dialog()

    def create_dialog(self):
        self.popup_active = True
        self.player.set_input_enabled(False)

        self.dialog_box = pygame_gui.elements.UITextBox(
            "Ahoj! Mám pro tebe otázku: Kolik je 1+1?",
            pygame.Rect((WINDOW_WIDTH//2 - 180, WINDOW_HEIGHT//2 - 110), (360, 80)),
            self.manager
        )
        self.text_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 10), (200, 40)),
            manager=self.manager
        )
        self.submit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WINDOW_WIDTH//2 - 50, WINDOW_HEIGHT//2 + 40), (100, 36)),
            text='Odeslat',
            manager=self.manager
        )

    def close_dialog(self):
        self.popup_active = False
        self.player.set_input_enabled(True)
        if self.text_entry: self.text_entry.kill(); self.text_entry = None
        if self.submit_button: self.submit_button.kill(); self.submit_button = None
        if self.dialog_box: self.dialog_box.kill(); self.dialog_box = None

    def handle_popup(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.submit_button:
            answer = self.text_entry.get_text()
            if answer.strip() == "2":
                print("Správně! Dobrá práce!")
            else:
                print("Špatně, zkus to příště!")
            self.close_dialog()

    def draw_interact_hint(self):
        if self.popup_active or self.pause.is_open():
            return
        npc = self.player_near_npc()
        if npc:
            text_surf = self.font.render("[E] Mluvit", True, (255, 255, 255))
            pos = (npc.rect.centerx - text_surf.get_width() // 2,
                   npc.rect.top - 10 - text_surf.get_height())
            offset_pos = (pos[0] + self.all_sprites.offset.x, pos[1] + self.all_sprites.offset.y)
            self.display_surface.blit(text_surf, offset_pos)

    # ====== Main loop ======
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.exit_to_menu = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e and not self.pause.is_open():
                        self.check_npc_interaction()
                    if event.key == pygame.K_ESCAPE:
                        if self.pause.is_open():
                            # stejné jako resume
                            self.pause.close()
                            self.player.set_input_enabled(True)
                        else:
                            self.pause.open()
                            self.player.set_input_enabled(False)

                # nejdřív necháme UI manager zpracovat event
                self.manager.process_events(event)

                # pokud je otevřené dialogové okno, řeš jeho eventy
                if self.popup_active:
                    self.handle_popup(event)

                # pokud je otevřené pause menu, předej mu eventy a reaguj na akci
                if self.pause.is_open():
                    action = self.pause.process_event(event)
                    if action == "resume":
                        self.pause.close()
                        self.player.set_input_enabled(True)
                    elif action == "coop_host":
                        print("CO-OP: HOST (placeholder)")
                    elif action == "coop_join":
                        print("CO-OP: JOIN (placeholder)")
                    elif action == "menu":
                        self.running = False
                        self.exit_to_menu = True
                    elif action == "quit":
                        self.running = False
                        self.exit_to_menu = False

            # UPDATE
            if not self.pause.is_open() and not self.popup_active:
                self.all_sprites.update(dt)
            self.manager.update(dt)

            # DRAW
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            if not self.pause.is_open():
                self.draw_interact_hint()

            # poloprůhledné ztmavení pod pauzou
            self.pause.draw_overlay(self.display_surface)

            self.manager.draw_ui(self.display_surface)
            pygame.display.update()

        pygame.quit()
        # run() končí, stav návratu je v self.exit_to_menu


if __name__ == '__main__':
    running = True
    while running:
        choice = run_menu()
        if choice in ('quit', None):
            break
        game = Game()
        game.run()
        if not game.exit_to_menu:
            running = False
