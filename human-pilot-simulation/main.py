import math
import os
import asyncio
import random
import sys

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
DT = 1/240 # 1 / ((60 frames per second) * (4 repetitions per frame cuz otherwise its too slow)) -> frame and frame cancel and 1/s becomes s so 1/240s   TIME PER ONE OF THE 4 STEPS
U = 3    

#-----------------------------------


def read_stick(mouse_y):
        
    stick = (SCREEN_HEIGHT/2 - mouse_y)/(SCREEN_HEIGHT*0.4) # distance from the center divided by a certain percentage of the screen, so when it exceedes it we can cap it at 1
        
    if stick > 1: # Capping the stick at 1
        stick = 1
    elif stick < -1:
        stick = -1 
    return stick
def draw_stick_bar(screen, stick):
    capped_stick_bar = SCREEN_HEIGHT/2-stick*(SCREEN_HEIGHT*0.4) # derived formula from the for 'stick', taking in the capped values of the stick to cap those controls, since the rectangles need the TOP/BOTTTOM position of the rectangle 

    if stick > 0: # Draw rectangles that are used for visualising the pilots push 
        pygame.draw.rect(screen, "saddlebrown", (50,capped_stick_bar,50,SCREEN_HEIGHT*0.5 - capped_stick_bar))
    else:
        pygame.draw.rect(screen, "saddlebrown", (50,SCREEN_HEIGHT*0.5,50,-(SCREEN_HEIGHT*0.5-capped_stick_bar)))


def make_target(stick, a):
        # 0.75 is just an eyeball, max angle, which is 1.05 minus the max gust of wind possible minus a little more just in case, and if the stick cant go firther its capped as
        # max for a target is 0.5 * U / a derived from: alpha= a*theta + u   -> say max_theta is positive -> 0 = a * max_theta - 3 -> a * max_theta = U since U is capped at 3, target has to be capped at a certain value too. 
        # stick = 1    ->    max target 
        # the min() part just takes whatever is smaller, the sticks current push or the maximum push and uses that since we cannot exceede the max push
        # make sure the target is proportional to the stick, so when stick is max which is 100% = 1 only then it shows the full target, so it does not get to the max target halfway through the stick
    return (abs(stick)/stick)*min(abs(stick * 0.75), 0.5 * U / a) if stick != 0 else 0

def mouse_y(mouse_pos):
    return pygame.mouse.get_pos()[1]

def mouse_x(mouse_pos):
    return pygame.mouse.get_pos()[0]

def pilot_push(pilot_mode, stick, target, theta, omega, a, I):
    if pilot_mode == "user":
        target = 0.75 * stick                
        u = target*4 # 3/0.75 = 4
        return u        
    elif pilot_mode == "fbw_pid":        
        u = 10*(target - theta) - 3*omega + 2 * I   # Implementing classical PID. Regular PD does NOT work since the plane stabilises at the wrong position because of the additional push of the a*theta. alpha = 2 * 0.3 + 10 * (0.3 - 0.3) = 0.6 while alpha = 2 * 0.375 + 10(0.3 - 0.375) = 0 so we need I to measure the addition of previous errors
        u = max(-U,min(U,u)) # bound u between U and -U
        return u
    elif pilot_mode == "fbw_pd_pushback":
        u = 10*(target - theta) - 3*omega - a * target
        u = max(-U,min(U,u)) # bound u between U and -U
        return u
    elif pilot_mode == "fbw_pd_best": # there is no PID since the times to stabilise have proven this not to work, since it pushes AGAINST the element -a*target(which is there to be a counterpush to the a), making the plane move a more unstable angle.. might add it just as a demonstration
        u = (2*a+6)*(target - theta) - 5*a*omega - a * target   
        u = max(-U,min(U,u)) # bound u between U and -U
        return u 
    elif pilot_mode == "comp":
        u = (2*a+6)*(0 - theta) - 3*omega
        u = max(-U,min(U,u)) # bound u between U and -U
        return u


def physics_step(theta, omega, a, gust, u_used):
    alpha = a * theta + gust + u_used # acceleration proportional to the angle, with the random gusts added and the pilot/computer input
    omega = omega + alpha * DT # speed of rotation infleunced by the push meaning alpha
    theta = theta + omega * DT  # current angle influenced by the sum of all previous speeds
    return theta, omega

def new_run(lag_ms):
    # theta, omega, gust, I, queue
    return 0.05, 0, 0, 0, [0]*round(lag_ms / 1000 / DT) # # SECONDS / DT => seconds to number of steps  ->    200 / 1000 / time per one of the 4 steps = 48 meaning 200ms is equivalent of 48 steps in our game

def draw_jet(screen, jet_image, theta, center_of_mass_to_image_center_x, center_of_mass_to_image_center_y):
    # Experimenting with making the plane turn around its center of mass. Complicated for some reason. 
    # Process goes like: look at original image, rotate it x degrees, position it exactly on its center 
    # of mass and copy it onto the screen. The screen fill covers the whole canvas over so many pictures
    # dont pile up on top of each other        
    rotated_jet_image = pygame.transform.rotate(jet_image, math.degrees(theta)) # rotate the original image by the angle and store that image as the current one, turn into degrees since thats what this function uses
    rotated_jet_rect = rotated_jet_image.get_rect()
    rotated_jet_rect.x = SCREEN_WIDTH / 2 - 0.5 * rotated_jet_rect.width + center_of_mass_to_image_center_x * math.cos(theta) + center_of_mass_to_image_center_y * math.sin(theta)
    rotated_jet_rect.y = SCREEN_HEIGHT / 2 - 0.5 * rotated_jet_rect.height + center_of_mass_to_image_center_y * math.cos(theta) - center_of_mass_to_image_center_x * math.sin(theta) # I almost up on this part cuz it didnt work.. you gotta split the main vector from the center of image to center of mass(that vector's magitude stays constant as it rotates since it goes from the center of the image itself to some point on the image) into two vectors but those two vectros also gain their own two vectors since they turn too and the x vector now has y component and y vector has x component and thats why we have two sin and cos per vector.. AI helped me with this minus and nudged me a little 
    screen.blit(rotated_jet_image, (rotated_jet_rect.x, rotated_jet_rect.y))    # image is copied onto the surface and put on a position  

def get_image(image_file_name):
    # Load the jet image from the same folder as the script so its accessed no matter from which place the python runs from
    current_folder = os.path.dirname(__file__)
    image_path = os.path.join(current_folder, image_file_name)
    image = pygame.image.load(image_path).convert_alpha()
    return image

async def main():
    #input()







    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    # This is just resizing it in web since it was over the whole screen and really hard to play:
    if sys.platform == "emscripten":   # if its inside browser
        import platform # gives python acccess to the webapge my game is on
        platform.window.config.user_canvas = 1 # dont allow pybag to resize it
        platform.window.canvas.style.width = f"{SCREEN_WIDTH}px" # resize it as is here
        platform.window.canvas.style.height = f"{SCREEN_HEIGHT}px"
        platform.window.canvas.style.margin = "auto"    

    clock = pygame.time.Clock()




    
    original_jet_image = get_image("jet.png")

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
    #jet_rect.x, jet_rect.y = center_plane(jet_image)
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


    a = 0.5
    I = 0
    theta = 0.05  # Degrees for a change, not radians, cunterclockwise as a unit-circle
    omega = 0
    alpha = 0
    stick = 0
    gust = 0 # new variable that is a random push of the air in some direction, directly affecting ang. accel. and used to demonstrate our Integral stabilisation factor
    pilot_mode = "user" # user or fly by wire or the pure computer
    lag_ms = 0
    #-------------------------------------------------------------------------------

    

    time = 0
    ladder = False
    game_state = "start"    
    running = True
    while running:
        ms = clock.tick(60) # Amount of FRAMES per SECOND so: ONE frame after every 1/60 = 0.01666667s or as it calculates 1s = 1000ms so it outputs 1000/60 = 16.666667 miliseconds per frame MAX, or less, if PC is slow        
        # We do not put the frame rate to be 240 because updating the screen 
        # that many times would be demanding and its easier to do 4 physics calculations and 
        # show the plane after that finished moment

        #---------------------------------------------------------input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN: # Adding 3 modes - unaided flight, fly-by-wire assisted and pure computer fly-by-wire 

                if game_state == "flying":
                    if event.key == pygame.K_1 or event.key == pygame.K_KP1:
                        pilot_mode = "user"
                        I = 0
                    elif event.key == pygame.K_2 or event.key == pygame.K_KP2:
                        pilot_mode = "fbw_pid"
                        I = 0                    
                    elif event.key == pygame.K_3 or event.key == pygame.K_KP3:
                        pilot_mode = "fbw_pd_pushback"
                        I = 0
                    elif event.key == pygame.K_4 or event.key == pygame.K_KP4:
                        pilot_mode = "fbw_pd_best"
                    elif event.key == pygame.K_5 or event.key == pygame.K_KP5:
                        pilot_mode = "comp"
                        I = 0
                    elif event.key == pygame.K_UP:
                        a += 1
                        if(a == 0):
                            a = 1
                    elif event.key == pygame.K_DOWN:
                        a -=1
                        if(a == 0):
                            a = -1
                    elif event.key == pygame.K_6 or event.key == pygame.K_KP6:                   
                        ladder = True
                elif game_state == "start":                        
                    if event.key == pygame.K_SPACE:
                        game_state = "flying"
                        theta, omega, gust, I, queue = new_run(lag_ms)
                    


        if pygame.mouse.get_pressed()[0]:
            running = False

        if game_state == "flying":           
            stick = read_stick(mouse_y(pygame.mouse.get_pos())) 
            
            
        elif game_state == "start":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False


        

        #------------------------------------------------update:

        
        if game_state == "flying":


            target = make_target(stick, a) 
            print(target)
            

            
            I = I + (target-theta)*DT
            
            
            u = pilot_push(pilot_mode, stick, target, theta, omega, a, I)
                
            if ladder == True:
                time += ms / 1000
                
                a = 1 + int(time//5)
                print(a)




            
            
            

            

        for step in range(4): # Does 4 steps and ONLY THEN do we draw it, since drawing is demanding and slows down the execution    
  
            if game_state == "flying":
                queue.append(u)
                u_used = queue.pop(0)     
                gust = 0.992 * gust + random.gauss(0, 0.05) # 0.992 chosen so it fades to HALF of the gust in about ln(0.5)/ln(0.992) = 86.30 steps which is about 86.3 * DT = 0.359 seconds. And random values will mostly be between 0.1 and -0.1 cuz of standard deviation being 0.05 cuz 95 rule is 2*0.05 = 0.1              
                theta, omega = physics_step(theta, omega, a, gust, u_used)


                
            elif game_state == "start": # initial game screen
                u_used = (-1)*(2*a+6)*theta - 3*omega        
                theta, omega = physics_step(theta, omega, a, 0, u_used)
            
            if abs(theta) > 1.05: # Resets the plane when it is clear it will crash
                theta = 0.05
                omega = 0

        #-----------------------------------------------------------------draw:
        screen.fill("skyblue")
        if game_state == "flying":            
            draw_stick_bar(screen, stick)
        elif game_state == "start":
            pass
      
        draw_jet(screen, jet_image, theta, center_of_mass_to_image_center_x, center_of_mass_to_image_center_y)

        pygame.display.flip()
        
         
        await asyncio.sleep(0) # line used for asyncio for some reason

    pygame.quit()
if __name__ == "__main__":
    asyncio.run(main())