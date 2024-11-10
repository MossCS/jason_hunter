import pygame
from settings import *
from os import walk, path

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites):
        super().__init__(groups)
        self.load_images()
        self.state, self.frame_index = 'right', 0
        self.image = pygame.image.load(path.join('images', 'player', 'down', '0.png')).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-60, -90)
    
        self.direction = pygame.Vector2()
        self.speed = PLAYER_SPEED
        self.max_speed = 600
        self.collision_sprites = collision_sprites

        self.max_health = MAX_HEALTH
        self.current_health = MAX_HEALTH

        # Ability attributes
        self.invincible = False
        self.invincibility_duration = 10  # seconds
        self.invincibility_timer = 0
        
        self.active_abilities = []

    def load_images(self):
        self.frames = {'left': [], 'right': [], 'up': [], 'down': []}

        for state in self.frames.keys():
            for folder_path, sub_folders, file_names in walk(path.join('images', 'player', state)):
                if file_names:
                    for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
                        full_path = path.join(folder_path, file_name)
                        surf = pygame.image.load(full_path).convert_alpha()
                        self.frames[state].append(surf)

    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction

    def move(self, dt):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y < 0: self.hitbox_rect.top = sprite.rect.bottom
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top

    def animate(self, dt):
        if self.direction.x != 0:
            self.state = 'right' if self.direction.x > 0 else 'left'
        if self.direction.y != 0:
            self.state = 'down' if self.direction.y > 0 else 'up'

        self.frame_index = self.frame_index + 5 * dt if self.direction else 0
        self.image = self.frames[self.state][int(self.frame_index) % len(self.frames[self.state])]

    def take_damage(self, amount):
        if not self.invincible:  # Only take damage if not invincible
            self.current_health -= amount
            if self.current_health <= 0:
                self.current_health = 0
                self.die()

    def heal(self, amount):
        self.current_health += amount
        if self.current_health > self.max_health:
            self.current_health = self.max_health

    def die(self):
        print("Player has died.")
        self.kill() 

    def is_alive(self):
        return self.current_health > 0

    def activate_invincibility(self, duration):
        self.invincible = True
        self.invincibility_start_time = pygame.time.get_ticks()
        self.invincibility_duration = duration
        self.active_abilities.append(('invincibility', duration))  # Start the timer
    
    def increase_speed(self, amount, duration):
        self.speed += amount
        if self.speed > self.max_speed:
            self.speed = self.max_speed  # Ensure speed does not exceed max speed
        self.speed_boost_start_time = pygame.time.get_ticks()
        self.speed_boost_duration = duration
        self.active_abilities.append(('speed', duration))
        
    def reset_speed(self):
        self.speed = PLAYER_SPEED

    def update(self, dt):
        self.input()
        self.move(dt)
        self.animate(dt)

        # Handle invincibility duration
        if self.invincible and (pygame.time.get_ticks() - self.invincibility_start_time >= self.invincibility_duration * 1000):
            self.invincible = False

        # Check if speed boost duration has expired
        if hasattr(self, 'speed_boost_start_time'):
            if pygame.time.get_ticks() - self.speed_boost_start_time >= self.speed_boost_duration * 1000:
                self.reset_speed()
                del self.speed_boost_start_time  # Clean up the attribute

        # Remove expired abilities
        current_time = pygame.time.get_ticks()
        self.active_abilities = [
            (ability, duration) for ability, duration in self.active_abilities
            if ability != 'speed' or (hasattr(self, 'speed_boost_start_time') and current_time - self.speed_boost_start_time < duration * 1000)
            if ability != 'invincibility' or (hasattr(self, 'invincibility_start_time') and current_time - self.invincibility_start_time < duration * 1000)
        ]