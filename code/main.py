from settings import *
from player import Player
from npc import NPC  # Importujeme NPC z nového souboru
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites
import pygame_gui

class Game:
    def __init__(self):
        # setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True

        # GUI
        self.manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))

        # groups 
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.npc_sprites = pygame.sprite.Group()  # Skupina pro NPC

        self.setup()

    def setup(self):
        map = load_pygame(join('data', 'maps', 'world.tmx'))

        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
                npc_position = (obj.x, obj.y + 150)  # NPC se objeví 150 pixelů pod hráčem
                self.npc = NPC(npc_position, (self.all_sprites, self.npc_sprites), self.manager)

    def check_npc_interaction(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_e]:  # Pokud hráč zmáčkne "E"
            for npc in self.npc_sprites:
                if self.player.hitbox_rect.colliderect(npc.hitbox_rect):  # Použití hitboxů pro přesnější detekci
                    npc.interact()

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.manager.process_events(event)
                for npc in self.npc_sprites:
                    npc.handle_popup(event)

            self.check_npc_interaction()  # Kontrola interakce s NPC
            self.all_sprites.update(dt)
            self.manager.update(dt)

            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            self.manager.draw_ui(self.display_surface)
            pygame.display.update()

        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()