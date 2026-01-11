import pygame
import os  # Importujeme celý modul os pro správné fungování os.walk
from os.path import join
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites, name="Ty"):
        super().__init__(groups)
        
        # 1. Animace a obrázky
        self.import_assets()
        self.status = 'down'
        self.frame_index = 0
        
        # 2. Nastavení úvodního obrázku a rectu
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(topleft=pos)
        
        # 3. Hitbox (zmenšený jen na nohy pro plynulý průchod za objekty)
        # Šířka je 60% postavy, výška fixních 20 pixelů u nohou
        self.hitbox_rect = pygame.Rect(0, 0, self.rect.width * 0.6, 20)
        self.hitbox_rect.midbottom = self.rect.midbottom

        # 4. Logika pohybu
        self.direction = pygame.Vector2()
        self.speed = 500
        self.collision_sprites = collision_sprites
        self.input_enabled = True
        self.name = name 
        
        # Inventář
        self.key_parts = set()
        self.has_master_key = False

    def import_assets(self):
        self.animations = {'up': [], 'down': [], 'left': [], 'right': []}
        for animation in self.animations.keys():
            full_path = join('images', 'player', animation)
            
            # OPRAVA: Používáme os.walk místo walk z os.path
            for _, __, image_files in os.walk(full_path):
                # Seřazení souborů (0.png, 1.png...)
                sorted_files = sorted(image_files, key=lambda x: int(x.split('.')[0]))
                for image in sorted_files:
                    img_surf = pygame.image.load(join(full_path, image)).convert_alpha()
                    self.animations[animation].append(img_surf)

    def input(self):
        if not self.input_enabled: return
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        
        if self.direction.length_squared() > 0:
            self.direction = self.direction.normalize()

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.hitbox_rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.hitbox_rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprite.hitbox_rect.right
                if direction == 'vertical':
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.hitbox_rect.top
                    if self.direction.y < 0: self.hitbox_rect.top = sprite.hitbox_rect.bottom

    def move(self, dt):
        # Horizontální pohyb
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        
        # Vertikální pohyb
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        
        # Grafika (rect) následuje hitbox (nohy)
        self.rect.midbottom = self.hitbox_rect.midbottom

    def animate(self, dt):
        current_animation = self.animations[self.status]
        if not current_animation: return
        
        if self.direction.length() != 0:
            self.frame_index += 10 * dt
            if self.frame_index >= len(current_animation):
                self.frame_index = 0
        else:
            self.frame_index = 0
            
        self.image = current_animation[int(self.frame_index)]

    def get_status(self):
        if self.direction.length() != 0:
            if abs(self.direction.x) > abs(self.direction.y):
                self.status = 'right' if self.direction.x > 0 else 'left'
            else:
                self.status = 'down' if self.direction.y > 0 else 'up'

    def update(self, dt):
        self.input()
        self.get_status()
        self.animate(dt)
        self.move(dt)

    def set_input_enabled(self, enabled):
        self.input_enabled = enabled
        if not enabled:
            self.direction.update(0, 0)