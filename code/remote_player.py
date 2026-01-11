import pygame
import os
from os.path import join
from settings import *

class RemotePlayer(pygame.sprite.Sprite):
    def __init__(self, player_id, pos, groups, name=None):
        super().__init__(groups)
        self.player_id = player_id
        self.name = name or f"Player {player_id}"
        
        self.import_assets()
        self.status = 'down'
        self.frame_index = 0
        
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        self.target_pos = pygame.Vector2(pos)

    def import_assets(self):
        # Základní animace, které MUSÍ existovat
        self.animations = {
            'up': [], 'down': [], 'left': [], 'right': [], 
            'up_idle': [], 'down_idle': [], 'left_idle': [], 'right_idle': []
        }
        
        # OPRAVA: Zkontroluj, zda tato cesta přesně odpovídá tvé struktuře složek!
        path = join('images', 'player') 
        
        for animation in self.animations.keys():
            full_path = join(path, animation)
            
            # Pokud složka existuje, načti obrázky
            if os.path.exists(full_path):
                for img in sorted(os.listdir(full_path)):
                    if img.endswith('.png'):
                        surf = pygame.image.load(join(full_path, img)).convert_alpha()
                        self.animations[animation].append(surf)
            
            # OPRAVA: Pokud složka (např. 'down_idle') neexistuje, 
            # zkus použít obrázek ze základní složky ('down')
            if not self.animations[animation]:
                base_move = animation.split('_')[0] # 'down_idle' -> 'down'
                base_path = join(path, base_move)
                if os.path.exists(base_path):
                    for img in sorted(os.listdir(base_path)):
                        if img.endswith('.png'):
                            surf = pygame.image.load(join(base_path, img)).convert_alpha()
                            self.animations[animation].append(surf)

            # ÚPLNÁ POJISTKA: Pokud stále nic není, dej tam aspoň růžovou, ať víme, že je to error
            if not self.animations[animation]:
                surf = pygame.Surface((64, 64))
                surf.fill('pink') # Růžová místo modré pro lepší viditelnost chyby
                self.animations[animation] = [surf]

    def set_state(self, x, y, status):
        self.target_pos = pygame.Vector2(x, y)
        # Pokud se cílová pozice liší od aktuální, postava se hýbe
        distance = (self.target_pos - pygame.Vector2(self.rect.center)).length()
        
        if distance > 2: # Pokud je pohyb větší než 2 pixely
            self.status = status
        else:
            # Pokud stojí, přidáme _idle
            if '_idle' not in status:
                self.status = status + '_idle'
            else:
                self.status = status

    def update(self, dt):
        # 1. Výpočet vzdálenosti k cíli pro detekci pohybu
        current_pos = pygame.Vector2(self.rect.center)
        distance = (self.target_pos - current_pos).length()
        
        # 2. Plynulý pohyb k cíli
        if distance > 1: # Tolerance 1 pixel, aby postava nekmitala
            self.rect.centerx += (self.target_pos.x - self.rect.centerx) * 0.15
            self.rect.centery += (self.target_pos.y - self.rect.centery) * 0.15
            self.is_moving = True
        else:
            self.rect.center = self.target_pos # Doskočení přesně na cíl
            self.is_moving = False

        # 3. Logika animace
        if self.is_moving:
            # Přičítáme index animace pouze pokud se hýbe
            self.frame_index += 10 * dt
            if self.frame_index >= len(self.animations[self.status]):
                self.frame_index = 0
        else:
            # Pokud stojí, vynutíme první snímek (stání)
            # Většinou je to nultý snímek v animaci
            self.frame_index = 0

        # 4. Aktualizace obrázku
        self.image = self.animations[self.status][int(self.frame_index)]