# npc.py
from settings import *

# npc.py
class NPC(pygame.sprite.Sprite):
    def __init__(self, pos, groups, npc_id):
        super().__init__(groups)
        self.npc_id = npc_id
        self.image = pygame.image.load(join('images', 'npc', 'NPC_skin.png')).convert_alpha()
        # ZMĚNA: center -> topleft
        self.rect = self.image.get_rect(topleft = pos)
        # Hitbox pro NPC (o něco menší než postava, aby se dalo projít kolem)
        self.hitbox_rect = self.rect.inflate(-10, -10)

    def interact(self):
        # už nevoláme input(); interakci řeší GUI v main.py
        pass

    def update(self, dt):
        pass
