import math
import os

import pygame

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540

CENTER_OF_MASS_RATIO_X = 0.47
CENTER_OF_MASS_RATIO_Y = 0.77
JET_SCALE = 0.25


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
clock = pygame.time.Clock()

current_folder = os.path.dirname(__file__)
jet_image_path = os.path.join(current_folder, "jet.png")
original_jet_image = pygame.image.load(jet_image_path).convert_alpha()

original_jet_width = original_jet_image.get_width()
original_jet_height = original_jet_image.get_height()

center_of_mass_offset_x = CENTER_OF_MASS_RATIO_X * original_jet_width * JET_SCALE
center_of_mass_offset_y = CENTER_OF_MASS_RATIO_Y * original_jet_height * JET_SCALE

jet_image = pygame.transform.scale_by(original_jet_image, 0.25)
jet_rect = jet_image.get_rect()
jet_rect.x = SCREEN_WIDTH / 2 - center_of_mass_offset_x
jet_rect.y = SCREEN_HEIGHT / 2 - center_of_mass_offset_y

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    if pygame.mouse.get_pressed()[0]:
        running = False
    print(pygame.mouse.get_pos())
    screen.fill("saddlebrown")

    screen.blit(jet_image, (jet_rect.x, jet_rect.y))
    

    
    

    
    

    
    pygame.display.flip()
    
    clock.tick(60)

pygame.quit()