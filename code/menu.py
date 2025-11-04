import pygame
import pygame_gui
from settings import *

class Star:
    def __init__(self, w, h):
        import random
        self.w, self.h = w, h
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.speed = random.uniform(20, 60)
        self.size = random.randint(1, 2)

    def update(self, dt):
        self.y += self.speed * dt
        if self.y > self.h: self.y = 0
        self.x += 0.5 * dt
        if self.x > self.w: self.x = 0

    def draw(self, surf):
        surf.fill((255, 255, 255), (int(self.x), int(self.y), self.size, self.size))

def draw_vertical_gradient(surf, top_color, bottom_color):
    h = surf.get_height()
    for y in range(h):
        t = y / (h - 1)
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (surf.get_width(), y))

def run_menu():
    """
    Vrací:
      - 'start'       → singleplayer start
      - 'coop_host'   → host co-op (zatím placeholder)
      - 'coop_join'   → join co-op (zatím placeholder)
      - 'quit'        → ukončit aplikaci
    """
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Survivor — Menu")
    clock = pygame.time.Clock()

    manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))

    title = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(0, 80, WINDOW_WIDTH, 80),
        text="<font size=6><b>SURVIVOR</b></font>",
        manager=manager
    )

    btn_width, btn_height = 280, 48
    start_btn = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(WINDOW_WIDTH//2 - btn_width//2, 220, btn_width, btn_height),
        text="Start",
        manager=manager
    )
    coop_btn = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(WINDOW_WIDTH//2 - btn_width//2, 280, btn_width, btn_height),
        text="Co-op",
        manager=manager
    )
    quit_btn = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(WINDOW_WIDTH//2 - btn_width//2, 340, btn_width, btn_height),
        text="Konec",
        manager=manager
    )
    credits = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(0, WINDOW_HEIGHT - 40, WINDOW_WIDTH, 30),
        text="<font size=2>© 2025 tvoje studio · [E] interakce · [Esc] pauza</font>",
        manager=manager
    )

    # Co-op okno
    coop_window = None
    host_btn = None
    join_btn = None

    starfield = [Star(WINDOW_WIDTH, WINDOW_HEIGHT) for _ in range(120)]
    bg_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    fade_alpha = 255

    running = True
    selection = None

    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                selection = 'quit'

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    selection = 'start'; running = False
                if event.key == pygame.K_ESCAPE:
                    selection = 'quit'; running = False

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == start_btn:
                    selection = 'start'; running = False
                elif event.ui_element == coop_btn:
                    if coop_window is None:
                        coop_window = pygame_gui.elements.UIWindow(
                            rect=pygame.Rect(WINDOW_WIDTH//2 - 220, WINDOW_HEIGHT//2 - 150, 440, 260),
                            manager=manager, window_display_title="Co-op", resizable=False
                        )
                        pygame_gui.elements.UILabel(
                            relative_rect=pygame.Rect(20, 20, 400, 30),
                            text="Vyber režim:",
                            manager=manager, container=coop_window
                        )
                        host_btn = pygame_gui.elements.UIButton(
                            relative_rect=pygame.Rect(20, 70, 180, 40),
                            text="Host (vytvořit hru)",
                            manager=manager, container=coop_window
                        )
                        join_btn = pygame_gui.elements.UIButton(
                            relative_rect=pygame.Rect(220, 70, 180, 40),
                            text="Join (připojit se)",
                            manager=manager, container=coop_window
                        )
                        pygame_gui.elements.UILabel(
                            relative_rect=pygame.Rect(20, 130, 400, 100),
                            text="<font size=2>Co-op implementujeme později. Tohle je jen UI.</font>",
                            manager=manager, container=coop_window
                        )
                elif coop_window is not None and event.ui_element == host_btn:
                    selection = 'coop_host'; running = False
                elif coop_window is not None and event.ui_element == join_btn:
                    selection = 'coop_join'; running = False
                elif event.ui_element == quit_btn:
                    selection = 'quit'; running = False

            if event.type == pygame_gui.UI_WINDOW_CLOSE and coop_window is not None:
                if event.ui_element == coop_window:
                    coop_window.kill(); coop_window = None; host_btn = None; join_btn = None

            manager.process_events(event)

        for s in starfield: s.update(dt)
        manager.update(dt)

        if fade_alpha > 0:
            fade_alpha = max(0, fade_alpha - 600 * dt)

        draw_vertical_gradient(bg_surface, (9, 11, 25), (24, 29, 54))
        for s in starfield: s.draw(bg_surface)

        screen.blit(bg_surface, (0, 0))
        manager.draw_ui(screen)

        if fade_alpha > 0:
            fade_surface.fill((0, 0, 0, int(fade_alpha)))
            screen.blit(fade_surface, (0, 0))

        pygame.display.update()

    return selection or 'quit'
