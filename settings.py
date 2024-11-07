import pygame 
from os.path import join 
from os import walk

# GLOBAL
WINDOW_WIDTH, WINDOW_HEIGHT = 1280,720 
TILE_SIZE = 64
MAX_HEALTH = 100
PLAYER_SPEED = 500
ENEMY_SPEED = 200

# MENU
BUTTON_WIDTH, BUTTON_HEIGHT = 250, 150 
BUTTON_SPACING = 20
FRAME_DELAY = 1 / 60

# UI
HEALTH_WIDTH = 200 
HEALTH_HEIGHT = 20
HEALTH_X = 10
HEALTH_Y = 10