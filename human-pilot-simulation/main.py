import math
import os

import pygame

#--------------------------------------------------------------------

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540

'''
Where the jet's center of mass sits in the image, as a fraction of the
image's width and height, measured from the top-left corner. Those numbers
are estimated from the image
'''
CENTER_OF_MASS_RATIO_X = 0.47
CENTER_OF_MASS_RATIO_Y = 0.77
JET_SCALE = 0.25


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
clock = pygame.time.Clock()

# Load the jet image from the same folder as the script so its accessed no matter from which place the python runs from
current_folder = os.path.dirname(__file__)
jet_image_path = os.path.join(current_folder, "jet.png")
original_jet_image = pygame.image.load(jet_image_path).convert_alpha()

original_jet_width = original_jet_image.get_width()
original_jet_height = original_jet_image.get_height()

# pinpoint the coordinates of the center of mass using the scaled jet and the ratio
# so it can be found no matter how big the jet is as long as the image is the same
center_of_mass_offset_x = CENTER_OF_MASS_RATIO_X * original_jet_width * JET_SCALE
center_of_mass_offset_y = CENTER_OF_MASS_RATIO_Y * original_jet_height * JET_SCALE

jet_image = pygame.transform.scale_by(original_jet_image, JET_SCALE) # make the image smaller/bigger so it fits well on the screen
jet_rect = jet_image.get_rect() # rectangle around the jet image, just how pygame deals with objects(or as they call it surfaces) coordinates and data
jet_rect.x = SCREEN_WIDTH / 2 - center_of_mass_offset_x # those are just a variables tied to the rectangle pygame draws, makes it easier to use later on, adjusted for its center of mass to be in the middle
jet_rect.y = SCREEN_HEIGHT / 2 - center_of_mass_offset_y

'''
Complications I stumbled upon: I cannot keep track of the center of mass since 
the image's rectangle constantly changes dimensions and they dont stay constant
so I had to figure out that the center of the image always has the same position
and that the vector from center of mass to the center of the image is ALWAYS
constant since its a pivot

This part just calculates x and y values of that vector

'''
center_of_mass_to_image_center_x = 0.5 * original_jet_width * JET_SCALE - center_of_mass_offset_x
center_of_mass_to_image_center_y = 0.5 * original_jet_height * JET_SCALE - center_of_mass_offset_y


#-----------------------------------------------------------------------------------

DT = 1/240
U = 3
theta = 0.05
omega = 0
gust = 0 # new variable that is a random push of the air in some direction, directly affecting ang. accel. and used to demonstrate our Integral stabilisation factor
angle = 0 # Degrees for a change, not radians, cunterclockwise as a unit-circle

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    if pygame.mouse.get_pressed()[0]:
        running = False
    print(pygame.mouse.get_pos())
    screen.fill("skyblue")



    # Experimenting with making the plane turn around its center of mass. Complicated for some reason. 
    # Process goes like: look at original image, rotate it x degrees, position it exactly on its center 
    # of mass and copy it onto the screen. The screen fill covers the whole canvas over so many pictures
    # dont pile up on top of each other
    angle = angle + 1 # Just for now made it spin to demonstrate
    rotated_jet_image = pygame.transform.rotate(jet_image, angle) # rotate the original image by the angle and store that image as the current one
    rotated_jet_rect = rotated_jet_image.get_rect()
    rotated_jet_rect.x = SCREEN_WIDTH / 2 - 0.5 * rotated_jet_rect.width + center_of_mass_to_image_center_x * math.cos(math.radians(angle)) + center_of_mass_to_image_center_y * math.sin(math.radians(angle))
    rotated_jet_rect.y = SCREEN_HEIGHT / 2 - 0.5 * rotated_jet_rect.height + center_of_mass_to_image_center_y * math.cos(math.radians(angle)) - center_of_mass_to_image_center_x * math.sin(math.radians(angle)) # I gave up on this part cuz it didnt work AI helped me with this minus and nudged me a little
    screen.blit(rotated_jet_image, (rotated_jet_rect.x, rotated_jet_rect.y))    # image is copied onto the surface and put on a position

    
    

    
    pygame.display.flip()
    
    clock.tick(60)

pygame.quit()