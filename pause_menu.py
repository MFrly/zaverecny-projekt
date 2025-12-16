# pause_menu.py
import pygame
import pygame_gui
from settings import *

class PauseMenu:
    def __init__(self, manager: pygame_gui.UIManager):
        self.manager = manager
        self._open = False
        self.window = None
        self.btn_resume = self.btn_coop = self.btn_menu = self.btn_quit = None

        # co-op okno
        self.coop_window = None
        self.btn_host = self.btn_join = None
        self.ip_entry = None
        self.btn_connect = None

    def open(self):
        if self._open: return
        self._open = True
        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(WINDOW_WIDTH//2 - 220, WINDOW_HEIGHT//2 - 160, 440, 320),
            manager=self.manager, window_display_title="Pauza", resizable=False
        )
        self.btn_resume = pygame_gui.elements.UIButton(pygame.Rect(30,40,380,40), "Pokračovat", self.manager, container=self.window)
        self.btn_coop   = pygame_gui.elements.UIButton(pygame.Rect(30,100,380,40), "Co-op", self.manager, container=self.window)
        self.btn_menu   = pygame_gui.elements.UIButton(pygame.Rect(30,160,380,40), "Hlavní menu", self.manager, container=self.window)
        self.btn_quit   = pygame_gui.elements.UIButton(pygame.Rect(30,220,380,40), "Konec", self.manager, container=self.window)

    def close(self):
        if self.coop_window:
            self.coop_window.kill()
            self.coop_window = None
            self.btn_host = self.btn_join = self.ip_entry = self.btn_connect = None
        if self.window:
            self.window.kill()
            self.window = None
        self.btn_resume = self.btn_coop = self.btn_menu = self.btn_quit = None
        self._open = False

    def is_open(self) -> bool:
        return self._open

    def _open_coop(self):
        if self.coop_window: return
        self.coop_window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(self.window.rect.left + 20, self.window.rect.top + 20, 400, 240),
            manager=self.manager, window_display_title="Co-op", resizable=False
        )
        self.btn_host = pygame_gui.elements.UIButton(pygame.Rect(20,40,160,40), "Host", self.manager, container=self.coop_window)
        self.btn_join = pygame_gui.elements.UIButton(pygame.Rect(200,40,160,40), "Join", self.manager, container=self.coop_window)
        pygame_gui.elements.UILabel(pygame.Rect(20,100,360,24), "IP adresa serveru (pro Join):", self.manager, container=self.coop_window)
        self.ip_entry = pygame_gui.elements.UITextEntryLine(pygame.Rect(20,130,360,36), self.manager, container=self.coop_window)
        self.ip_entry.set_text("127.0.0.1")
        self.btn_connect = pygame_gui.elements.UIButton(pygame.Rect(20,175,360,36), "Připojit (Join)", self.manager, container=self.coop_window)

    def process_event(self, event):
        if not self._open:
            return None

        if event.type == pygame_gui.UI_BUTTON_PRESSED and self.window is not None:
            if event.ui_element == self.btn_resume:
                return "resume"
            elif event.ui_element == self.btn_coop:
                self._open_coop()
            elif event.ui_element == self.btn_menu:
                return "menu"
            elif event.ui_element == self.btn_quit:
                return "quit"

        # co-op akce
        if self.coop_window is not None and event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_host:
                return ("coop_host", None)
            if event.ui_element == self.btn_join or event.ui_element == self.btn_connect:
                ip = self.ip_entry.get_text().strip() if self.ip_entry else "127.0.0.1"
                return ("coop_join", ip)

        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.coop_window:
                self.coop_window.kill()
                self.coop_window = None
                self.btn_host = self.btn_join = self.ip_entry = self.btn_connect = None
            elif event.ui_element == self.window:
                return "resume"

        return None

    def draw_overlay(self, surface: pygame.Surface, alpha: int = 120):
        if not self._open: return
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,alpha))
        surface.blit(overlay, (0,0))
