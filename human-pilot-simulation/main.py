import math
import os
import asyncio
import random

import pygame

#--------------------------------------------------------------------
async def main():

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

    DT = 1/240 # 1 / ((60 frames per second) * (4 repetitions per frame cuz otherwise its too slow)) -> frame and frame cancel and 1/s becomes s so 1/240s
    U = 3
    a = 4
    theta = 0.05  # Degrees for a change, not radians, cunterclockwise as a unit-circle
    omega = 0
    alpha = 0
    target = 0
    gust = 0 # new variable that is a random push of the air in some direction, directly affecting ang. accel. and used to demonstrate our Integral stabilisation factor
    

    running = True
    while running:
        ms = clock.tick(60) # Amount of FRAMES per SECOND so: ONE frame after every 1/60 = 0.01666667s or as it calculates 1s = 1000ms so it outputs 1000/60 = 16.666667 miliseconds per frame MAX, or less, if PC is slow
        # We do not put the frame rate to be 240 because updating the screen 
        # that many times would be demanding and its easier to do 4 physics calculations and 
        # show the plane after that finished moment
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if pygame.mouse.get_pressed()[0]:
            running = False
        #print(pygame.mouse.get_pos())
        screen.fill("skyblue")
        
        stick = (SCREEN_HEIGHT/2 - pygame.mouse.get_pos()[1])/(SCREEN_HEIGHT*0.4) # distance from the center divided by a certain percentage of the screen, so when it exceedes it we can cap it at 1
            
        if stick > 1: # Capping the stick at 1
            stick = 1
        elif stick < -1:
            stick = -1 
        capped_stick_bar = SCREEN_HEIGHT/2-stick*(SCREEN_HEIGHT*0.4) # derived formula from the for 'stick', taking in the capped values of the stick to cap those controls
        print(stick)
        u = U * stick # final stick push with a coefficient, randing from 3 * (-1) to 3 * 1 -> -3 to 3

         
            
        #print(stick)
        if stick > 0: # Draw rectangles that are used for visualising the pilots push 
            pygame.draw.rect(screen, "saddlebrown", (50,capped_stick_bar,50,SCREEN_HEIGHT*0.5 - capped_stick_bar))
        else:
            pygame.draw.rect(screen, "saddlebrown", (50,SCREEN_HEIGHT*0.5,50,-(SCREEN_HEIGHT*0.5-capped_stick_bar)))


        
        for step in range(4): # Does 4 steps and ONLY THEN do we draw it, since drawing is demanding
            gust = 0.992 * gust + random.gauss(0, 0.05) # 0.992 chosen so it fades to HALF of the gust in about ln(0.5)/ln(0.992) = 86.30 steps which is about 86.3 * DT = 0.359 seconds. And random values will mostly be between 0.1 and -0.1 cuz of standard deviation being 0.05 cuz 95 rule is 2*0.05 = 0.1
            
            alpha = a * theta + gust + u # acceleration proportional to the angle, with the random gusts added and the pilot/computer input
            omega = omega + alpha * DT # speed of rotation infleunced by the push meaning alpha
            theta = theta + omega * DT  # current angle influenced by the sum of all previous speeds

            if abs(theta) > 1.05: # Reset plane when it is clear it will crash
                theta = 0.05
                omega = 0

        # Experimenting with making the plane turn around its center of mass. Complicated for some reason. 
        # Process goes like: look at original image, rotate it x degrees, position it exactly on its center 
        # of mass and copy it onto the screen. The screen fill covers the whole canvas over so many pictures
        # dont pile up on top of each other
        
        rotated_jet_image = pygame.transform.rotate(jet_image, math.degrees(theta)) # rotate the original image by the angle and store that image as the current one
        rotated_jet_rect = rotated_jet_image.get_rect()
        rotated_jet_rect.x = SCREEN_WIDTH / 2 - 0.5 * rotated_jet_rect.width + center_of_mass_to_image_center_x * math.cos(math.radians(theta)) + center_of_mass_to_image_center_y * math.sin(math.radians(theta))
        rotated_jet_rect.y = SCREEN_HEIGHT / 2 - 0.5 * rotated_jet_rect.height + center_of_mass_to_image_center_y * math.cos(math.radians(theta)) - center_of_mass_to_image_center_x * math.sin(math.radians(theta)) # I gave up on this part cuz it didnt work AI helped me with this minus and nudged me a little
        screen.blit(rotated_jet_image, (rotated_jet_rect.x, rotated_jet_rect.y))    # image is copied onto the surface and put on a position

        
        

        
        pygame.display.flip()
        
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()
if __name__ == "__main__":
    asyncio.run(main())