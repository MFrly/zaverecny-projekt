import pygame
from settings import *

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        # OPRAVA: Pro mapu musí být topleft, aby dlaždice seděly vedle sebe
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox_rect = self.rect.copy()
        self.ground = True

class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        # OPRAVA: Přidán hitbox, aby Player.collision() fungoval a neházel chybu
        self.hitbox_rect = self.rect.copy()
        
class KeyPart(pygame.sprite.Sprite):
    def __init__(self, pos, part_id, image, groups):
        super().__init__(groups)
        self.part_id = part_id
        self.image = image
        # Použijeme center, aby klíč seděl přesně na bodu z Tiled
        self.rect = self.image.get_rect(center = pos)
        # Hitbox uděláme menší, aby se klíč lépe sbíral
        self.hitbox_rect = self.rect.inflate(-5, -5)