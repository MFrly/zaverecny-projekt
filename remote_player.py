# remote_player.py
from settings import *
import pygame, os

_REMOTE_IMG = None
def _img():
    global _REMOTE_IMG
    if _REMOTE_IMG: return _REMOTE_IMG
    path = join('images','player','down','0.png')
    if os.path.exists(path):
        _REMOTE_IMG = pygame.image.load(path).convert_alpha()
    else:
        surf = pygame.Surface((32,32), pygame.SRCALPHA)
        surf.fill((200,50,50,255)); pygame.draw.rect(surf,(255,255,255),surf.get_rect(),2)
        _REMOTE_IMG = surf
    return _REMOTE_IMG

class RemotePlayer(pygame.sprite.Sprite):
    def __init__(self, player_id, pos, groups, name =None):
        super().__init__(groups)
        self.player_id = player_id
        self.name = name or f"Player {player_id}"
        self.image = _img()
        self.rect = self.image.get_rect(center=(int(pos[0]), int(pos[1])))
        self.hitbox_rect = self.rect.inflate(-60, -60)

    def set_pos(self, x, y):
        self.rect.center = (int(x), int(y))
        self.hitbox_rect.center = self.rect.center

    def update(self, dt): pass
