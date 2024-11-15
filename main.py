import pygame
import numpy as np
from moviepy.editor import VideoFileClip
from settings import *
from player import Player
from ability import Ability
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites
from random import choice

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
        self.ability_sprites = pygame.sprite.Group()

        self.can_shoot = True
        self.shoot_time = 0 
        self.gun_cooldown = 100

        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 500)
        self.spawn_positions = []
        self.ability_drop = []

        self.shoot_sound = pygame.mixer.Sound(join('audio', 'shoot.wav'))
        self.shoot_sound.set_volume(0.2)
        self.collect_sound = pygame.mixer.Sound(join('audio', 'collect.mp3'))
        self.collect_sound.set_volume(0.2)
        self.impact_sound = pygame.mixer.Sound(join('audio', 'impact.ogg'))
        pygame.mixer.music.load(join('audio', 'music.wav'))
        pygame.mixer.music.set_volume(0.4)

        self.main_menu_sound = pygame.mixer.Sound(join('audio', 'menu.wav'))  
        self.game_over_sound = pygame.mixer.Sound(join('audio', 'lose.wav'))  

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
        
        self.game_over_image = pygame.image.load('menu/game_over.png').convert_alpha()
        self.game_over_image = pygame.transform.scale(self.game_over_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
        self.play_again_button_normal = pygame.transform.scale(pygame.image.load('menu/play_again.png'), (BUTTON_WIDTH, BUTTON_HEIGHT))
        self.play_again_button_hover = pygame.transform.scale(pygame.image.load('menu/play_again_hover.png'), (BUTTON_WIDTH, BUTTON_HEIGHT))
        self.exit_button_normal = pygame.transform.scale(pygame.image.load('menu/exit.png'), (BUTTON_WIDTH, BUTTON_HEIGHT))
        self.exit_button_hover = pygame.transform.scale(pygame.image.load('menu/exit_hover.png'), (BUTTON_WIDTH, BUTTON_HEIGHT))

        self.play_again_button = {
            'image': self.play_again_button_normal,
            'rect': pygame.Rect(WINDOW_WIDTH / 2 - BUTTON_WIDTH / 2, WINDOW_HEIGHT / 2 + BUTTON_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT)
        }
        self.exit_button = {
            'image': self.exit_button_normal,
            'rect': pygame.Rect(WINDOW_WIDTH / 2 - BUTTON_WIDTH / 2, WINDOW_HEIGHT / 2 + BUTTON_SPACING + BUTTON_HEIGHT + 10, BUTTON_WIDTH, BUTTON_HEIGHT)
        }

        self.game_started = False
        self.game_over = False  
        self.game_over_sound_played = False  

        self.score = 0 
        self.font = pygame.font.Font(join('fonts','upheavtt.ttf'), FONT_SIZE) 
        self.countdown_font = pygame.font.Font(join('fonts', 'Mario-Kart-DS.ttf'), 72)
        self.time_font = pygame.font.Font(join ('fonts', 'Mario-Kart-DS.ttf'), 24)
        self.boost_font = pygame.font.Font(join ('fonts', 'Mario-Kart-DS.ttf'), 30)
        
        self.heal_text = None  
        self.heal_text_opacity = 255  
        self.heal_text_start_time = 0  
        self.heal_text_duration = 1000
        
        self.hit_enemies = set() 
        self.enemy_speed = ENEMY_SPEED
        self.spawn_interval = SPAWN_INTERVAL
        self.last_spawn_time = pygame.time.get_ticks()
        self.frame_delay = FRAME_DELAY
        self.start_time = 0 
        self.elapsed_time = 0  
        
        self.countdown_time = 3 
        self.countdown_started = False
        self.countdown_start_time = 0
        self.countdown_text = ""

        self.heart_icon = pygame.image.load(join('menu', 'heart.png')).convert_alpha()
        self.heart_icon = pygame.transform.scale(self.heart_icon, (50, 50))  

        self.clock_icon = pygame.image.load(join('menu', 'clock.png')).convert_alpha()
        self.clock_icon = pygame.transform.scale(self.clock_icon, (30, 30))  

        self.star_icon = pygame.image.load(join('menu', 'star.png')).convert_alpha()
        self.star_icon = pygame.transform.scale(self.star_icon, (45, 45)) 
        
        self.ability_icons = {
            'heal': pygame.image.load(join('images', 'ability', 'heal.png')).convert_alpha(),
            'speed': pygame.image.load(join('images', 'ability', 'speed.png')).convert_alpha(),
            'invincibility': pygame.image.load(join('images', 'ability', 'kebal.png')).convert_alpha(),
        }
    
        self.main_menu_sound.play()
        self.main_menu_sound.set_volume(0.4)

        self.wave_duration = 60 
        self.wave_start_time = 0
        self.current_wave = 1
        self.wave_active = False
        self.boss_active = False

        self.ability_spawn_times = {} 
        self.ability_spawn_time = 0  
        self.ability_spawn_interval = ABILITY_DELAY
        self.ability_respawn_timer = {} 
        self.ability_respawn_delay = ABILITY_DELAY
        
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
                for file_name in sorted(file_names, key=lambda name : int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot and not self.game_over:
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
        
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))
        
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)
            
        for obj in map.get_layer_by_name('Ability'):
            if obj.name == 'Drop':
                self.ability_drop.append((obj.x, obj.y))

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites)
            else:
                self.spawn_positions.append((obj.x, obj.y))

    def spawn_ability(self):
        available_spawn_points = [pos for pos in self.ability_drop if pos not in self.ability_spawn_times]
        
        existing_abilities = [ability.rect.topleft for ability in self.ability_sprites]

        available_spawn_points = [pos for pos in available_spawn_points if pos not in existing_abilities]

        if available_spawn_points:
            spawn_pos = choice(available_spawn_points)
            ability_type = choice(['heal', 'speed', 'invincibility'])
            new_ability = Ability(spawn_pos, ability_type, self.ability_sprites)
            self.all_sprites.add(new_ability)
            self.ability_spawn_times[spawn_pos] = pygame.time.get_ticks()  
        else:
            for spawn_pos in self.ability_drop:
                if spawn_pos in self.ability_respawn_timer:
                    if pygame.time.get_ticks() - self.ability_respawn_timer[spawn_pos] >= self.ability_respawn_delay * 1000:
                        del self.ability_respawn_timer[spawn_pos]

    def update(self):
        current_time = pygame.time.get_ticks()
        
        if self.heal_text:
            elapsed_time = current_time - self.heal_text_start_time
            if elapsed_time < self.heal_text_duration:
                self.heal_text_opacity = max(0, 255 - (255 * elapsed_time / self.heal_text_duration))  
            else:
                self.heal_text = None
        
        self.player.active_abilities = [(ability, start_time) for ability, start_time in self.player.active_abilities if (current_time - start_time) < 10000]
        
        for spawn_pos in list(self.ability_spawn_times.keys()):
            if current_time - self.ability_spawn_times[spawn_pos] >= self.ability_spawn_interval * 1000:
                del self.ability_spawn_times[spawn_pos]  
                
        for spawn_pos in self.ability_drop:
            if spawn_pos not in self.ability_spawn_times and spawn_pos not in self.ability_respawn_timer:
                self.ability_respawn_timer[spawn_pos] = current_time  

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
                self.game_over = True  
                pygame.mixer.music.stop()  
                if not self.game_over_sound_played:  
                    self.game_over_sound.play()  
                    self.game_over_sound_played = True  
        else:
            self.damage_taken = False

        collected_abilities = pygame.sprite.spritecollide(self.player, self.ability_sprites, True)
        for ability in collected_abilities:
            self.collect_sound.play()
            self.collect_ability(ability)

    def collect_ability(self, ability):
        current_time = pygame.time.get_ticks()  
        if ability.ability_type == 'heal':
            self.player.heal(50)
            self.heal_text = "50"  
            self.heal_text_start_time = current_time  
            self.heal_text_opacity = 255
        elif ability.ability_type == 'speed':
            if not any(a[0] == 'speed' for a in self.player.active_abilities):
                self.player.increase_speed(100, 10)
                self.player.active_abilities.append((ability.ability_type, current_time)) 
        elif ability.ability_type == 'invincibility':
            if not any(a[0] == 'invincibility' for a in self.player.active_abilities):
                self.player.activate_invincibility(10)
                self.player.active_abilities.append((ability.ability_type, current_time)) 

        for spawn_pos in self.ability_drop:
            if spawn_pos in self.ability_spawn_times:
                del self.ability_spawn_times[spawn_pos]  
                self.ability_respawn_timer[spawn_pos] = pygame.time.get_ticks()  

    def draw_health_bar(self):
        health_ratio = self.player.current_health / self.player.max_health
        
        pygame.draw.rect(self.display_surface, (0, 0, 0), (HEALTH_X - 2, HEALTH_Y - 2, HEALTH_WIDTH + 4, HEALTH_HEIGHT + 4))  

        corner_size = 5 
        for corner_x, corner_y in [(HEALTH_X - 2, HEALTH_Y - 2), (HEALTH_X + HEALTH_WIDTH, HEALTH_Y - 2), (HEALTH_X - 2, HEALTH_Y + HEALTH_HEIGHT), (HEALTH_X + HEALTH_WIDTH, HEALTH_Y + HEALTH_HEIGHT)]:
            pygame.draw.rect(self.display_surface, (0, 0, 0), (corner_x, corner_y, corner_size, corner_size))

        pygame.draw.rect(self.display_surface, (255, 0, 0), (HEALTH_X, HEALTH_Y, HEALTH_WIDTH, HEALTH_HEIGHT))
        pygame.draw.rect(self.display_surface, (0, 255, 0), (HEALTH_X, HEALTH_Y, HEALTH_WIDTH * health_ratio, HEALTH_HEIGHT))

        self.display_surface.blit(self.heart_icon, (HEALTH_X - 20, HEALTH_Y - 15)) 
        
        if self.heal_text:
            font = pygame.font.Font(join('fonts', 'Mario-Kart-DS.ttf'), 24)  
            heal_surface = font.render(self.heal_text, True, (255, 255, 255, self.heal_text_opacity))  
            heal_rect = heal_surface.get_rect(topleft=(HEALTH_X + HEALTH_WIDTH + 10, HEALTH_Y))  
            heal_surface.set_alpha(self.heal_text_opacity) 
            self.display_surface.blit(heal_surface, heal_rect)
        
    def draw_active_abilities(self):
        y_offset = HEALTH_Y + HEALTH_HEIGHT + 30 
        current_time = pygame.time.get_ticks()  

        for ability, start_time in self.player.active_abilities:
            if ability in ['speed', 'invincibility']:
                remaining_time = max(0, 10 - (current_time - start_time) // 1000)  

                if remaining_time > 0:  
                    icon = self.ability_icons.get(ability)
                    if icon:
                        icon = pygame.transform.scale(icon, (30, 30))  
                        self.display_surface.blit(icon, (HEALTH_X, y_offset))  

                    formatted_duration = self.format_time(remaining_time)

                    ability_surface = self.boost_font.render(formatted_duration, True, (0, 0, 0))
                    outline_surface = self.boost_font.render(formatted_duration, True, (255, 255, 255))  
                    self.display_surface.blit(outline_surface, (HEALTH_X + 38, y_offset + 2))  
                    self.display_surface.blit(ability_surface, (HEALTH_X + 38, y_offset))  

                    y_offset += 40  

    def draw_score_and_time(self):
        score_surface = self.font.render(f'Score {self.score}', True, (255, 255, 255)) 
        time_surface = self.time_font.render(self.format_time(self.elapsed_time), True, (255, 255, 255))

        self.display_surface.blit(self.star_icon, (WINDOW_WIDTH - 255, 40)) 
        self.display_surface.blit(score_surface, (WINDOW_WIDTH - 200, 50))  

        if self.game_started and not self.game_over:
            self.elapsed_time = int((pygame.time.get_ticks() - self.start_time) / 1000) 
            self.display_surface.blit(self.clock_icon, (WINDOW_WIDTH // 2 - 45, 84))  
            self.display_surface.blit(time_surface, (WINDOW_WIDTH // 2 - 12, 90)) 

        outline_color = (0, 0, 0)  
        outline_surface = self.font.render(f'Score {self.score}', True, outline_color)
        self.display_surface.blit(outline_surface, (WINDOW_WIDTH - 202, 48))  

        outline_surface_time = self.time_font.render(self.format_time(self.elapsed_time), True, outline_color)
        self.display_surface.blit(outline_surface_time, (WINDOW_WIDTH // 2 - 10, 88))  
        
    def draw_boss_health_bar(self):
        if self.boss_active:
            health_ratio = self.boss_health / 1000  
            
            pygame.draw.rect(self.display_surface, (0, 0, 0), (WINDOW_WIDTH / 2 - 200, 100, 404, 34))  
            pygame.draw.rect(self.display_surface, (255, 0, 0), (WINDOW_WIDTH / 2 - 200, 100, 400, 30))  
            pygame.draw.rect(self.display_surface, (0, 255, 0), (WINDOW_WIDTH / 2 - 200, 100, 400 * health_ratio, 30)) 
            
            health_text = f'Boss Health: {self.boss_health}/1000'
            font = pygame.font.Font(join('fonts', 'Mario-Kart-DS.ttf'), 24)
            health_surface = font.render(health_text, True, (255, 255, 255))
            self.display_surface.blit(health_surface, (WINDOW_WIDTH / 2 - health_surface.get_width() / 2, 70))
    
    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f'{minutes:02}.{seconds:02}'

    def draw_wave(self):
        wave_surface = self.font.render(f'Wave {self.current_wave}', True, (0, 0, 0))
        outline_color = (255, 255, 255)
        outline_surface = self.font.render(f'Wave {self.current_wave}', True, outline_color)
        self.display_surface.blit(outline_surface, (WINDOW_WIDTH // 2 - 50, 48))  
        self.display_surface.blit(wave_surface, (WINDOW_WIDTH // 2 - 48, 48)) 
        
    def draw_countdown(self):
        countdown_surface = self.countdown_font.render(self.countdown_text, True, (255, 255, 255))
        countdown_rect = countdown_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.display_surface.blit(countdown_surface, countdown_rect) 

    def display_game_over(self):
        self.display_surface.fill('black')
        self.display_surface.blit(self.game_over_image, (0, 0))
        self.display_surface.blit(self.play_again_button['image'], self.play_again_button['rect'])
        self.display_surface.blit(self.exit_button['image'], self.exit_button['rect'])

        final_score_surface = self.font.render(f'Final Score: {self.score}', True, (255, 255, 255))
        final_score_outline = self.font.render(f'Final Score: {self.score}', True, (0, 0, 0))  
        final_score_rect = final_score_surface.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 50))

        self.display_surface.blit(final_score_outline, (final_score_rect.x + 2, final_score_rect.y + 2))
        self.display_surface.blit(final_score_surface, final_score_rect)  

        final_time_surface = self.font.render(f'Time Survived: {self.format_time(self.elapsed_time)}', True, (255, 255, 255))
        final_time_outline = self.font.render(f'Time Survived: {self.format_time(self.elapsed_time)}', True, (0, 0, 0))  
        final_time_rect = final_time_surface.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 20))

        self.display_surface.blit(final_time_outline, (final_time_rect.x + 2, final_time_rect.y + 2))  
        self.display_surface.blit(final_time_surface, final_time_rect)  
        pygame.display.update()

    def handle_game_over_input(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if self.play_again_button['rect'].collidepoint(mouse_x, mouse_y):
            self.play_again_button['image'] = self.play_again_button_hover
            if pygame.mouse.get_pressed()[0]: 
                self.restart_game() 
        else:
            self.play_again_button['image'] = self.play_again_button_normal

        if self.exit_button['rect'].collidepoint (mouse_x, mouse_y):
            self.exit_button['image'] = self.exit_button_hover 
            if pygame.mouse.get_pressed()[0]: 
                self.running = False  
        else:
            self.exit_button['image'] = self.exit_button_normal

    def restart_game(self):
        self.__init__() 
        self.start_time = pygame.time.get_ticks()  
        pygame.mixer.music.stop()  
        self.main_menu_sound.play()  
        self.game_over_sound_played = False  

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == self.enemy_event and self.game_started:
                    if pygame.time.get_ticks() - self.last_spawn_time >= self.spawn_interval:
                        Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites, self.enemy_speed)
                        self.last_spawn_time = pygame.time.get_ticks()

            mouse_x, mouse_y = pygame.mouse.get_pos()
            if self.start_button['rect'].collidepoint(mouse_x, mouse_y):
                self.start_button['image'] = self.start_button_hover
                if pygame.mouse.get_pressed()[0]: 
                    if not self.game_started:  
                        self.start_time = pygame.time.get_ticks()
                        self.countdown_started = True
                        self.countdown_start_time = pygame.time.get_ticks()
                    self.game_started = True
                    self.main_menu_sound.stop()  
                    if not pygame.mixer.music.get_busy():  
                        pygame.mixer.music.play(-1)  
            else:
                self.start_button['image'] = self.start_button_normal    
                
            if self.countdown_started:
                current_time = pygame.time.get_ticks()
                elapsed_time = (current_time - self.countdown_start_time) / 1000  
                remaining_time = max(0, 3 - int(elapsed_time))  

                if remaining_time == 0:
                    self.countdown_text = "DUARR!!"
                    pygame.time.delay(1000)  
                    self.countdown_started = False
                    self.game_started = True  
                    self.start_time = pygame.time.get_ticks()  
                    self.wave_start_time = self.start_time  
                    self.wave_active = True  
                else:
                    self.countdown_text = str(remaining_time)

                self.display_surface.fill('black')  
                self.draw_countdown()  
                pygame.display.update()  
                continue
            
            if self.game_started:
                self.gun_timer()
                if self.can_shoot:  
                    self.input()
                self.all_sprites.update(dt)
                self.bullet_collision()
                self.player_collision()
                self.update()  

                current_time = pygame.time.get_ticks()
                if current_time - self.ability_spawn_time >= self.ability_spawn_interval * 1000:  
                    self.spawn_ability()
                    self.ability_spawn_time = current_time  

                if self.game_over: 
                    self.display_game_over()  
                    self.handle_game_over_input()  
                else:
                    self.all_sprites.draw(self.player.rect.center)  
                    self.ability_sprites.draw(self.display_surface)  
                    self.draw_health_bar()
                    self.draw_active_abilities()
                    self.draw_score_and_time()  
                    self.draw_wave() 
                    
                    current_wave_time = (pygame.time.get_ticks() - self.wave_start_time) / 1000
                    if current_wave_time >= self.wave_duration:  
                        self.current_wave += 1  
                        self.wave_start_time = pygame.time.get_ticks() 
                         
                        self.enemy_speed += 20
                        self.spawn_interval = max(100, self.spawn_interval - 50)
                        
                    pygame.display.update()
            else:
                self.display_surface.fill('black')
                self.display_surface.blit(self.frame_surface, (0, 0))
                self.display_surface.blit(self.start_button['image'], self.start_button['rect'])
                pygame.display.update()
                
                try:
                    self.frame_surface = pygame.surfarray.make_surface(np.swapaxes(next(self.video_frames), 0, 1))
                    self.frame_surface = pygame.transform.scale(self.frame_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
                    pygame.time.delay(int(FRAME_DELAY * 1000))  
                except StopIteration:
                    self.video_frames = self.play_background_video()  

        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()