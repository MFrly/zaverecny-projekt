from settings import *
import pygame


class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.ground = True


class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)


class KeyPart(pygame.sprite.Sprite):
    def __init__(self, pos, part_id, surf, groups):
        super().__init__(groups)

        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

        # menší hitbox – pocitově lepší sbírání
        self.hitbox_rect = self.rect.inflate(-8, -8)

        self.part_id = part_id

    def update(self, dt):
        # pro budoucí efekty (např. animace / pulsování)
        pass
