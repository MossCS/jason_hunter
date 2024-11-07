import pygame
import sys
import numpy as np
from moviepy.editor import VideoFileClip
from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites
from random import randint, choice

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Jason Hunter')
        self.clock = pygame.time.Clock()
        self.running = True

        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        self.can_shoot = True
        self.shoot_time = 0 
        self.gun_cooldown = 100

        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 300)
        self.spawn_positions = []

        self.shoot_sound = pygame.mixer.Sound(join('audio', 'shoot.wav'))
        self.shoot_sound.set_volume(0.2)
        self.impact_sound = pygame.mixer.Sound(join('audio', 'impact.ogg'))
        pygame.mixer.music.load(join('audio', 'music.wav'))
        pygame.mixer.music.set_volume(0.4)

        self.load_images()
        self.setup()

        self.video_frames = self.play_background_video()
        self.first_frame = next(self.video_frames)
        self.frame_surface = pygame.surfarray.make_surface(np.swapaxes(self.first_frame, 0, 1))
        self.frame_surface = pygame.transform.scale(self.frame_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))

        self.start_button_normal = pygame.transform.scale(pygame.image.load('menu/start.png'), (BUTTON_WIDTH, BUTTON_HEIGHT))
        self.start_button_hover = pygame.transform.scale(pygame.image.load('menu/start_hover.png'), (BUTTON_WIDTH, BUTTON_HEIGHT))
        self.start_button = {
            'image': self.start_button_normal,
            'rect': pygame.Rect(WINDOW_WIDTH / 2 - BUTTON_WIDTH / 2, WINDOW_HEIGHT / 2 + BUTTON_SPACING + 10, BUTTON_WIDTH, BUTTON_HEIGHT)
        }
        self.game_started = False

        self.score = 0 
        self.font = pygame.font.Font(None, 36) 
        self.hit_enemies = set() 

    def play_background_video(self):
        clip = VideoFileClip("menu/background.mp4")
        fps = clip.fps
        for frame in clip.iter_frames(fps=fps, dtype='uint8'):
            yield frame
            
    def load_images(self):
        self.bullet_surf = pygame.image.load(join('images', 'gun', 'bullet.png')).convert_alpha()

        folders = list(walk(join('images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            self.shoot_sound.play()
            pos = self.gun.rect.center + self.gun.player_direction * 50
            Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True

    def setup(self):
        map = load_pygame(join('data', 'maps', 'world2.tmx'))

        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)
        
        for obj in map.get_layer_by_name ('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))
        
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites)
            else:
                self.spawn_positions.append((obj.x, obj.y))

    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    self.impact_sound.play()
                    for sprite in collision_sprites:
                        if sprite not in self.hit_enemies:  
                            sprite.destroy()
                            self.score += 1  
                            self.hit_enemies.add(sprite)  
                    bullet.kill()

    def player_collision(self):
        collided_enemies = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask)
        
        if collided_enemies:
            if not hasattr(self, 'damage_taken') or not self.damage_taken:
                self.player.take_damage(10)
                self.damage_taken = True  
            if not self.player.is_alive():
                self.running = False  
        else:
            self.damage_taken = False
            
    def draw_health_bar(self):
        health_ratio = self.player.current_health / self.player.max_health
        
        pygame.draw.rect(self.display_surface, (0, 0, 0), (HEALTH_X - 2, HEALTH_Y - 2, HEALTH_WIDTH + 4, HEALTH_HEIGHT + 4))  

        corner_size = 5
        for corner_x, corner_y in [(HEALTH_X - 2, HEALTH_Y - 2), (HEALTH_X + HEALTH_WIDTH, HEALTH_Y - 2), (HEALTH_X - 2, HEALTH_Y + HEALTH_HEIGHT), (HEALTH_X + HEALTH_WIDTH, HEALTH_Y + HEALTH_HEIGHT)]:
            pygame.draw.rect(self.display_surface, (0, 0, 0), (corner_x, corner_y, corner_size, corner_size))

        pygame.draw.rect(self.display_surface, (255, 0, 0), (HEALTH_X, HEALTH_Y, HEALTH_WIDTH, HEALTH_HEIGHT))
        pygame.draw.rect(self.display_surface, (0, 255, 0), (HEALTH_X, HEALTH_Y, HEALTH_WIDTH * health_ratio, HEALTH_HEIGHT))

    def draw_score(self):
        score_surface = self.font.render(f'Score: {self.score}', True, (255, 255, 255)) 
        self.display_surface.blit(score_surface, (WINDOW_WIDTH - 150, 10))  

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == self.enemy_event:
                    Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)

            mouse_x, mouse_y = pygame.mouse.get_pos()
            if self.start_button['rect'].collidepoint(mouse_x, mouse_y):
                self.start_button['image'] = self.start_button_hover
                if pygame.mouse.get_pressed()[0]: 
                    self.game_started = True
            else:
                self.start_button['image'] = self.start_button_normal

            try:
                frame = next(self.video_frames)
                self.frame_surface = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))
                self.frame_surface = pygame.transform.scale(self.frame_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
            except StopIteration:
                self.video_frames = self.play_background_video()
                frame = next(self.video_frames)

                self.frame_surface = pygame.surfarray.make_surface(np.swapaxes(self.first_frame, 0, 1))
                self.frame_surface = pygame.transform.scale(self.frame_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))

            self.display_surface.blit(self.frame_surface, (0, 0))
            pygame.time.delay(int(FRAME_DELAY * 1000))

            if self.game_started:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(0)
                    
                self.gun_timer()
                self.input()
                self.all_sprites.update(dt)
                self.bullet_collision()
                self.player_collision()
                
                self.all_sprites.draw(self.player.rect.center)
                self.draw_health_bar()
                self.draw_score() 
                pygame.display.update()
            else:
                self.display_surface.fill('black')
                self.display_surface.blit(self.frame_surface, (0, 0))
                self.display_surface.blit(self.start_button['image'], self.start_button['rect'])
                pygame.mixer.music.stop()
                pygame.display.update()
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()