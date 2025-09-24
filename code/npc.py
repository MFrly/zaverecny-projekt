from settings import *
from pygame_gui.elements import UITextBox, UITextEntryLine, UIButton
import pygame_gui

class NPC(pygame.sprite.Sprite):
    def __init__(self, pos, groups, manager):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player', 'down', '0.png')).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-60, -60)
        self.manager = manager
        self.dialog_box = None
        self.text_entry = None
        self.submit_button = None
        self.popup_active = False
    
    def interact(self):
        if not self.popup_active:
            self.popup_active = True
            self.dialog_box = UITextBox("Ahoj! Mám pro tebe otázku: Kolik je 1+1?", pygame.Rect((WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 100), (300, 60)), self.manager)
            self.text_entry = UITextEntryLine(relative_rect=pygame.Rect((WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2), (200, 50)), manager=self.manager)
            self.submit_button = UIButton(relative_rect=pygame.Rect((WINDOW_WIDTH//2 - 50, WINDOW_HEIGHT//2 + 60), (100, 40)), text='Odeslat', manager=self.manager)
    
    def handle_popup(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.submit_button:
            answer = self.text_entry.get_text()
            if answer.strip() == "2":
                print("Správně! Dobrá práce!")
            else:
                print("Špatně, zkus to příště!")
            self.popup_active = False
            self.text_entry.kill()
            self.submit_button.kill()
            self.dialog_box.kill()
    
    def update(self, dt):
        pass  # NPC zatím nemá pohyb, ale můžeš sem později přidat logiku
