import pygame
import math
from os import path

class Ability(pygame.sprite.Sprite):
    def __init__(self, pos, ability_type, groups):
        super().__init__(groups)
        self.ability_type = ability_type
        self.image = self.load_image(ability_type)
        self.rect = self.image.get_rect(topleft=pos)
        self.original_y = pos[1] 
        self.animation_speed = 1  
        self.direction = 1  
        self.amplitude = 10  

    def load_image(self, ability_type):
        if ability_type == 'heal':
            return pygame.image.load(path.join('images', 'ability', 'heal.png')).convert_alpha()
        elif ability_type == 'speed':
            return pygame.image.load(path.join('images', 'ability', 'speed.png')).convert_alpha()
        elif ability_type == 'invincibility':
            return pygame.image.load(path.join('images', 'ability', 'kebal.png')).convert_alpha()
        else:
            raise ValueError("Unknown ability type")

    def update(self, dt):
        self.rect.y = self.original_y + self.amplitude * math.sin(pygame.time.get_ticks() * 0.005 * self.animation_speed) 