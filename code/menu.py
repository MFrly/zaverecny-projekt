# menu.py
import math
import random
import os
import pygame
import pygame_gui
from settings import *

def _make_nebula_surface(w: int, h: int, seed: int = 1234) -> pygame.Surface:
    rnd = random.Random(seed)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for _ in range(18):
        r = rnd.randint(120, 320)
        x = rnd.randint(-50, w + 50)
        y = rnd.randint(-50, h + 50)
        alpha = rnd.randint(18, 45)
        col = (rnd.randint(30, 70), rnd.randint(40, 90), rnd.randint(70, 140), alpha)
        pygame.draw.circle(surf, col, (x, y), r)
    blurred = pygame.Surface((w, h), pygame.SRCALPHA)
    for dx, dy, a in [(0, 0, 110), (2, 0, 60), (-2, 0, 60), (0, 2, 60), (0, -2, 60)]:
        tmp = surf.copy()
        tmp.set_alpha(a)
        blurred.blit(tmp, (dx, dy))
    return blurred

def _init_stars(count: int, w: int, h: int):
    stars = []
    for _ in range(count):
        x = random.uniform(0, w)
        y = random.uniform(0, h)
        speed = random.uniform(25, 120)
        radius = random.choice([1, 1, 1, 2])
        twinkle = random.uniform(0, math.tau)
        stars.append([x, y, speed, radius, twinkle])
    return stars

def _draw_background(screen: pygame.Surface, dt: float, stars, nebula: pygame.Surface, t: float):
    w, h = screen.get_size()
    screen.fill((10, 12, 20))
    grad = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(grad, (20, 25, 45, 110), pygame.Rect(0, 0, w, h))
    pygame.draw.rect(grad, (5, 8, 18, 180), pygame.Rect(0, h * 0.55, w, h * 0.45))
    screen.blit(grad, (0, 0))
    ox = int(math.sin(t * 0.35) * 18)
    oy = int(math.cos(t * 0.28) * 14)
    screen.blit(nebula, (ox, oy))
    screen.blit(nebula, (ox - w, oy))
    screen.blit(nebula, (ox, oy - h))
    screen.blit(nebula, (ox - w, oy - h))
    for s in stars:
        s[1] += s[2] * dt
        s[4] += dt * 3.2
        if s[1] > h:
            s[0] = random.uniform(0, w)
            s[1] = random.uniform(-30, -5)
        a = 120 + int(80 * (0.5 + 0.5 * math.sin(s[4])))
        col = (220, 230, 255, max(40, min(200, a)))
        pygame.draw.circle(screen, col, (int(s[0]), int(s[1])), s[3])
    vignette = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(vignette, (0, 0, 0, 60), pygame.Rect(0, 0, w, h))
    screen.blit(vignette, (0, 0))

def run_menu():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))
    stars = _init_stars(count=140, w=WINDOW_WIDTH, h=WINDOW_HEIGHT)
    nebula = _make_nebula_surface(WINDOW_WIDTH, WINDOW_HEIGHT, seed=777)
    t = 0.0
    title_font = pygame.font.SysFont(None, 80, bold=True)
    title_surf = title_font.render("Friendly Expedition", True, (240, 245, 255))
    title_rect = title_surf.get_rect(midtop=(WINDOW_WIDTH // 2, 70))
    glow_surf = pygame.Surface((title_rect.width + 60, title_rect.height + 30), pygame.SRCALPHA)
    pygame.draw.ellipse(glow_surf, (120, 160, 255, 55), glow_surf.get_rect())
    glow_rect = glow_surf.get_rect(center=(title_rect.centerx, title_rect.centery + 10))

    btn_w, btn_h = 280, 48
    # PŘIDÁNO: Tlačítko Pokračovat (aby load fungoval z menu)
    continue_btn = pygame_gui.elements.UIButton(pygame.Rect(WINDOW_WIDTH // 2 - btn_w // 2, 220, btn_w, btn_h), "Pokračovat", manager)
    start_btn = pygame_gui.elements.UIButton(pygame.Rect(WINDOW_WIDTH // 2 - btn_w // 2, 280, btn_w, btn_h), "Nová hra", manager)
    coop_btn = pygame_gui.elements.UIButton(pygame.Rect(WINDOW_WIDTH // 2 - btn_w // 2, 340, btn_w, btn_h), "Co-op", manager)
    quit_btn = pygame_gui.elements.UIButton(pygame.Rect(WINDOW_WIDTH // 2 - btn_w // 2, 400, btn_w, btn_h), "Konec", manager)
    name_entry = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect(WINDOW_WIDTH // 2 - 140, 170, 280, 40), manager=manager)
    name_entry.set_text("Hráč")

    coop_win = None
    selection = ("quit", None)
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        t += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                selection = ("quit", None); running = False
            
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == continue_btn:
                    selection = ("load", None); running = False
                elif event.ui_element == start_btn:
                    selection = ("start", None); running = False
                elif event.ui_element == quit_btn:
                    selection = ("quit", None); running = False
                elif event.ui_element == coop_btn:
                    if coop_win is None:
                        coop_win = pygame_gui.elements.UIWindow(pygame.Rect(WINDOW_WIDTH // 2 - 220, WINDOW_HEIGHT // 2 - 160, 440, 320), manager, "Co-op")
                        host_btn = pygame_gui.elements.UIButton(pygame.Rect(20, 40, 180, 40), "Host", manager, container=coop_win)
                        join_btn = pygame_gui.elements.UIButton(pygame.Rect(220, 40, 180, 40), "Join", manager, container=coop_win)
                        ip_entry = pygame_gui.elements.UITextEntryLine(pygame.Rect(20, 130, 380, 36), manager, container=coop_win)
                        ip_entry.set_text("127.0.0.1")
                        connect_btn = pygame_gui.elements.UIButton(pygame.Rect(20, 180, 380, 40), "Připojit (Join)", manager, container=coop_win)

                if coop_win:
                    if event.ui_element == host_btn: selection = ("coop_host", None); running = False
                    if event.ui_element == join_btn or event.ui_element == connect_btn:
                        selection = ("coop_join", ip_entry.get_text().strip()); running = False

            manager.process_events(event)
        
        manager.update(dt)
        _draw_background(screen, dt, stars, nebula, t)
        screen.blit(glow_surf, glow_rect)
        screen.blit(title_surf, title_rect)
        manager.draw_ui(screen)
        pygame.display.update()

    return {"action": selection[0], "player_name": name_entry.get_text().strip(), "ip": selection[1]}