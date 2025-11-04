# pause_menu.py
import pygame
import pygame_gui
from settings import *

class PauseMenu:
    """
    Jednoduché pauzovací menu oddělené od Game.
    API:
      - open(), close(), is_open()
      - process_event(event) -> action string nebo None
      - draw_overlay(surface) – poloprůhledné ztmavení za oknem
    Action hodnoty:
      'resume' | 'coop_host' | 'coop_join' | 'menu' | 'quit'
    """
    def __init__(self, manager: pygame_gui.UIManager):
        self.manager = manager
        self._open = False

        self.window = None
        self.btn_resume = None
        self.btn_coop = None
        self.btn_menu = None
        self.btn_quit = None

        # Co-op sub-okno
        self.coop_window = None
        self.btn_host = None
        self.btn_join = None

        # (volitelné) budoucí IP input by šel přidat sem

    # ---------- lifecycle ----------
    def open(self):
        if self._open:
            return
        self._open = True

        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(WINDOW_WIDTH // 2 - 220, WINDOW_HEIGHT // 2 - 160, 440, 320),
            manager=self.manager,
            window_display_title="Pauza",
            resizable=False
        )
        self.btn_resume = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(30, 40, 380, 40),
            text="Pokračovat",
            manager=self.manager, container=self.window
        )
        self.btn_coop = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(30, 100, 380, 40),
            text="Co-op",
            manager=self.manager, container=self.window
        )
        self.btn_menu = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(30, 160, 380, 40),
            text="Hlavní menu",
            manager=self.manager, container=self.window
        )
        self.btn_quit = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(30, 220, 380, 40),
            text="Konec",
            manager=self.manager, container=self.window
        )

    def close(self):
        # zavřít co-op sub-okno (pokud je)
        if self.coop_window is not None:
            self.coop_window.kill()
            self.coop_window = None
            self.btn_host = None
            self.btn_join = None

        # zavřít hlavní okno
        if self.window is not None:
            self.window.kill()
            self.window = None

        self.btn_resume = self.btn_coop = self.btn_menu = self.btn_quit = None
        self._open = False

    def is_open(self) -> bool:
        return self._open

    # ---------- UI helpery ----------
    def _open_coop_submenu(self):
        if self.coop_window is not None:
            return
        self.coop_window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(self.window.rect.left + 20, self.window.rect.top + 20, 400, 220),
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

    # ---------- event handling ----------
    def process_event(self, event) -> str | None:
        """
        Zpracuje pygame/pygame_gui eventy. Pokud uživatel zvolí akci,
        vrátí řetězec ('resume'/'coop_host'/'coop_join'/'menu'/'quit'), jinak None.
        """
        if not self._open:
            return None

        # kliknutí na tlačítka v hlavním pauz okně
        if event.type == pygame_gui.UI_BUTTON_PRESSED and self.window is not None:
            if event.ui_element == self.btn_resume:
                return "resume"
            elif event.ui_element == self.btn_coop:
                self._open_coop_submenu()
            elif event.ui_element == self.btn_menu:
                return "menu"
            elif event.ui_element == self.btn_quit:
                return "quit"

        # kliknutí v co-op sub-okně
        if self.coop_window is not None and event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_host:
                return "coop_host"
            elif event.ui_element == self.btn_join:
                return "coop_join"

        # zavírání oken křížkem
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.coop_window:
                self.coop_window.kill()
                self.coop_window = None
                self.btn_host = None
                self.btn_join = None
            elif event.ui_element == self.window:
                # zavření hlavního okna -> stejné jako "resume"
                return "resume"

        return None

    # ---------- kreslení ----------
    def draw_overlay(self, surface: pygame.Surface, alpha: int = 120):
        """
        Jemné ztmavení pozadí pod pauz oknem.
        Volitelné – lze volat i když PauseMenu není open (pak nic nedělá).
        """
        if not self._open:
            return
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        surface.blit(overlay, (0, 0))
