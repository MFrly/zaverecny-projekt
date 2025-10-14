# npc.py
from settings import *

class NPC(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player', 'down', '0.png')).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        # zmenšit hitbox ~ o 40 % v obou osách
        shrink_x = int(self.rect.width * 0.4)
        shrink_y = int(self.rect.height * 0.4)
        self.hitbox_rect = self.rect.inflate(-shrink_x, -shrink_y)
        self.interacting = False

    def interact(self):
        # už nevoláme input(); interakci řeší GUI v main.py
        pass

    def update(self, dt):
        pass
