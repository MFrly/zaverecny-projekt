import pygame

class KeyPart(pygame.sprite.Sprite):
    def __init__(self, pos, part_id: int, groups, image: pygame.Surface):
        super().__init__(groups)
        self.part_id = part_id
        self.image = image
        self.rect = self.image.get_rect(center=pos)

    def on_pickup(self, player):
        # player musí mít set, viz níže
        player.key_parts.add(self.part_id)
        self.kill()
