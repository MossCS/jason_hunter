import pygame
import sys
from moviepy.editor import VideoFileClip
import numpy as np

# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 1280, 720
BUTTON_WIDTH, BUTTON_HEIGHT = 250, 150  # Desired button size
BUTTON_SPACING = 20  # Space between buttons

# Load button images
start_button_normal = pygame.transform.scale(pygame.image.load('menu/start.png'), (BUTTON_WIDTH, BUTTON_HEIGHT))
start_button_hover = pygame.transform.scale(pygame.image.load('menu/start_hover.png'), (BUTTON_WIDTH, BUTTON_HEIGHT))

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Function to play the video frames in a loop
def play_background_video():
    clip = VideoFileClip("menu/background.mp4")
    fps = clip.fps
    for frame in clip.iter_frames(fps=fps, dtype='uint8'):
        yield frame

# Create a generator for the video frames
video_frames = play_background_video()

# Get the first frame to avoid blackscreen
try:
    first_frame = next(video_frames)
    frame_surface = pygame.surfarray.make_surface(np.swapaxes(first_frame, 0, 1))
    frame_surface = pygame.transform.scale(frame_surface, (WIDTH, HEIGHT))
except StopIteration:
    print("Video is empty or could not be loaded.")
    frame_surface = pygame.Surface((WIDTH, HEIGHT))  # Create a black surface as fallback

# Set up the buttons with adjusted Y positions
start_button = {
    'image': start_button_normal,
    'rect': pygame.Rect(WIDTH / 2 - BUTTON_WIDTH / 2, HEIGHT / 2 + BUTTON_SPACING + 10, BUTTON_WIDTH, BUTTON_HEIGHT)  # Naikkan posisi Y
}

# Set up the clock
clock = pygame.time.Clock()
frame_delay = 1 / 60  # Delay for 30 FPS video

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Get the mouse position
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # Check if the mouse is hovering over a button
    if start_button['rect'].collidepoint(mouse_x, mouse_y):
        start_button['image'] = start_button_hover
    else:
        start_button['image'] = start_button_normal

    # Draw everything
    screen.fill((0, 0, 0))  # Clear the screen

    # Draw video frame
    try:
        frame = next(video_frames)
        # Convert the frame to a Pygame surface
        frame_surface = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))
        frame_surface = pygame.transform.scale(frame_surface, (WIDTH, HEIGHT))
    except StopIteration:
        # Restart the video when it reaches the end
        video_frames = play_background_video()
        # Use the first frame to avoid blackscreen
        frame_surface = pygame.surfarray.make_surface(np.swapaxes(first_frame, 0, 1))
        frame_surface = pygame.transform.scale(frame_surface, (WIDTH, HEIGHT))

    # Draw the video frame
    screen.blit(frame_surface, (0, 0))

    # Draw buttons
    screen.blit(start_button['image'], start_button['rect'])
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)
    pygame.time.delay(int(frame_delay * 1000))  # Delay to control video playback speed