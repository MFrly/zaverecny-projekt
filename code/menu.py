# menu.py
import pygame, pygame_gui
from settings import *

def run_menu():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Survivor — Menu")
    clock = pygame.time.Clock()
    manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))

    btn_w, btn_h = 280, 48
    title = pygame_gui.elements.UILabel(pygame.Rect(0,80,WINDOW_WIDTH,60), "<font size=6><b>SURVIVOR</b></font>", manager)
    start_btn = pygame_gui.elements.UIButton(pygame.Rect(WINDOW_WIDTH//2-btn_w//2,220,btn_w,btn_h), "Start", manager)
    coop_btn  = pygame_gui.elements.UIButton(pygame.Rect(WINDOW_WIDTH//2-btn_w//2,280,btn_w,btn_h), "Co-op", manager)
    quit_btn  = pygame_gui.elements.UIButton(pygame.Rect(WINDOW_WIDTH//2-btn_w//2,340,btn_w,btn_h), "Konec", manager)

    coop_win = None
    host_btn = join_btn = None
    ip_entry = None
    connect_btn = None

    selection = ("quit", None)
    running = True

    while running:
        dt = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                selection = ("quit", None); running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    selection = ("start", None); running = False
                if event.key == pygame.K_ESCAPE:
                    selection = ("quit", None); running = False

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == start_btn:
                    selection = ("start", None); running = False
                elif event.ui_element == quit_btn:
                    selection = ("quit", None); running = False
                elif event.ui_element == coop_btn:
                    if coop_win is None:
                        coop_win = pygame_gui.elements.UIWindow(
                            rect=pygame.Rect(WINDOW_WIDTH//2-220, WINDOW_HEIGHT//2-160, 440, 320),
                            manager=manager, window_display_title="Co-op", resizable=False
                        )
                        host_btn = pygame_gui.elements.UIButton(pygame.Rect(20,40,180,40), "Host", manager, container=coop_win)
                        join_btn = pygame_gui.elements.UIButton(pygame.Rect(220,40,180,40), "Join", manager, container=coop_win)
                        pygame_gui.elements.UILabel(pygame.Rect(20,100,400,30), "IP adresa serveru (pro Join):", manager, container=coop_win)
                        ip_entry = pygame_gui.elements.UITextEntryLine(pygame.Rect(20,130,380,36), manager, container=coop_win)
                        ip_entry.set_text("127.0.0.1")
                        connect_btn = pygame_gui.elements.UIButton(pygame.Rect(20,180,380,40), "Připojit (Join)", manager, container=coop_win)

                elif coop_win is not None and event.ui_element == host_btn:
                    selection = ("coop_host", None); running = False
                elif coop_win is not None and (event.ui_element == join_btn or event.ui_element == connect_btn):
                    ip = ip_entry.get_text().strip() if ip_entry else "127.0.0.1"
                    selection = ("coop_join", ip); running = False

            if event.type == pygame_gui.UI_WINDOW_CLOSE and coop_win is not None:
                if event.ui_element == coop_win:
                    coop_win.kill(); coop_win = None
                    host_btn = join_btn = ip_entry = connect_btn = None

            manager.process_events(event)

        manager.update(dt)
        screen.fill((15,18,32))
        manager.draw_ui(screen)
        pygame.display.update()

    return selection
