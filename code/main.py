# main.py
from settings import *
from player import Player
from npc import NPC
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites
from menu import run_menu
import pygame
import pygame_gui

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True
        self.exit_to_menu = False   # ← signál pro návrat do hlavního menu

        # GUI
        self.manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.text_entry = None
        self.dialog_box = None
        self.submit_button = None
        self.popup_active = False

        # Pauza
        self.paused = False
        self.pause_window = None
        self.btn_resume = None
        self.btn_coop = None
        self.btn_menu = None
        self.btn_quit = None
        self.coop_window = None
        self.btn_host = None
        self.btn_join = None

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.npc_sprites = pygame.sprite.Group()

        # pomocný font (hinty)
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
        if self.popup_active or self.paused:
            return
        npc = self.player_near_npc()
        if npc:
            text_surf = self.font.render("[E] Mluvit", True, (255, 255, 255))
            pos = (npc.rect.centerx - text_surf.get_width() // 2,
                   npc.rect.top - 10 - text_surf.get_height())
            offset_pos = (pos[0] + self.all_sprites.offset.x, pos[1] + self.all_sprites.offset.y)
            self.display_surface.blit(text_surf, offset_pos)

    # ====== Pauza (ESC) ======
    def open_pause_menu(self):
        if self.paused:
            return
        self.paused = True
        self.player.set_input_enabled(False)

        self.pause_window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(WINDOW_WIDTH//2 - 220, WINDOW_HEIGHT//2 - 160, 440, 320),
            manager=self.manager, window_display_title="Pauza", resizable=False
        )
        self.btn_resume = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(30, 40, 380, 40),
            text="Pokračovat",
            manager=self.manager, container=self.pause_window
        )
        self.btn_coop = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(30, 100, 380, 40),
            text="Co-op",
            manager=self.manager, container=self.pause_window
        )
        self.btn_menu = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(30, 160, 380, 40),
            text="Hlavní menu",
            manager=self.manager, container=self.pause_window
        )
        self.btn_quit = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(30, 220, 380, 40),
            text="Konec",
            manager=self.manager, container=self.pause_window
        )

    def close_pause_menu(self):
        self.paused = False
        self.player.set_input_enabled(True)

        # zavřít případné co-op okno
        if self.coop_window is not None:
            self.coop_window.kill()
            self.coop_window = None
            self.btn_host = None
            self.btn_join = None

        if self.pause_window is not None:
            self.pause_window.kill()
            self.pause_window = None
        self.btn_resume = self.btn_coop = self.btn_menu = self.btn_quit = None

    def open_coop_submenu(self, parent_window):
        if self.coop_window is None:
            self.coop_window = pygame_gui.elements.UIWindow(
                rect=pygame.Rect(parent_window.rect.left + 20, parent_window.rect.top + 20, 400, 220),
                manager=self.manager, window_display_title="Co-op", resizable=False
            )
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(20, 20, 360, 30),
                text="Vyber režim:",
                manager=self.manager, container=self.coop_window
            )
            self.btn_host = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(20, 70, 160, 40),
                text="Host",
                manager=self.manager, container=self.coop_window
            )
            self.btn_join = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(200, 70, 160, 40),
                text="Join",
                manager=self.manager, container=self.coop_window
            )
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(20, 130, 360, 70),
                text="<font size=2>Implementaci přidáme později. Tohle je jen UI.</font>",
                manager=self.manager, container=self.coop_window
            )

    def handle_pause_event(self, event):
        # kliknutí na hlavní pauzovací menu
        if event.type == pygame_gui.UI_BUTTON_PRESSED and self.pause_window is not None:
            if event.ui_element == self.btn_resume:
                self.close_pause_menu()
            elif event.ui_element == self.btn_coop:
                self.open_coop_submenu(self.pause_window)
            elif event.ui_element == self.btn_menu:
                # návrat do hlavního menu
                self.running = False
                self.exit_to_menu = True
            elif event.ui_element == self.btn_quit:
                # ukončit hru úplně
                self.running = False
                self.exit_to_menu = False

        # kliknutí v co-op sub-okně
        if self.coop_window is not None and event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_host:
                print("CO-OP: HOST (placeholder)")
            elif event.ui_element == self.btn_join:
                print("CO-OP: JOIN (placeholder)")

        # zavření oken křížkem
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.coop_window:
                self.coop_window.kill(); self.coop_window = None; self.btn_host = None; self.btn_join = None
            elif event.ui_element == self.pause_window:
                # zavření hlavního pauz okna = pokračovat
                self.close_pause_menu()

    # ====== Main loop ======
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.exit_to_menu = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e and not self.paused:
                        self.check_npc_interaction()
                    if event.key == pygame.K_ESCAPE:
                        if self.paused:
                            self.close_pause_menu()
                        else:
                            self.open_pause_menu()

                self.manager.process_events(event)

                if self.popup_active:
                    self.handle_popup(event)
                if self.paused:
                    self.handle_pause_event(event)

            # UPDATE
            if not self.paused and not self.popup_active:
                self.all_sprites.update(dt)
            self.manager.update(dt)

            # DRAW
            self.display_surface.fill('black')
            # Kamera i při pauze drží hráče uprostřed
            self.all_sprites.draw(getattr(self.player, 'rect', pygame.Rect(0,0,0,0)).center if hasattr(self, 'player') else (0,0))
            if not self.paused:
                self.draw_interact_hint()
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
        # single / co-op volby zatím spouští stejnou hru
        game = Game()
        game.run()
        if not game.exit_to_menu:
            # hráč zvolil „Konec“ ve hře → skončit appku
            running = False

