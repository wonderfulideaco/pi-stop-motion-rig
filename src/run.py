import datetime as dt
import random
import glob
import os
import pygame
import textinput
import re
import sys

from pygame.locals import *
from gpiozero import Button
from picamera import PiCamera

# 2 = delete movie / pink button
# 3 = preview movie / green button
# 4 = delete a frame / blue button
# 5 - take a picture / yellow button
# 6 - save movie / white button
# 13 - exit program / switch

# KEYBOARD MAPPING
# forward slash = delete movie 
# space = preview movie 
# back = delete a frame 
# enter = take a picture 
# s = save 
# esc = exit program

BUTTON_NUMBERS = [2, 3, 4, 5, 6, 13]


BUTTONS = {
    bnum: Button(bnum)
    for bnum in BUTTON_NUMBERS
}

WHITE = (255, 255, 255)
TEAL = (116, 199, 208)
BLACK = (0, 0, 0)

# whether to show the title screen
reset = True

# whether the preview is being show
preview_playing = False

def display_start_screen(W, H, switch_frame):
    SCREEN.fill(TEAL)
    
    # LOAD IMAGES
    title_1 = pygame.image.load('src/assets/title_1.png')
    title_2 = pygame.image.load('src/assets/title_2.png')
    # get_rect includes x, y, width, height, centerx, centery, center
    title_rect = title_1.get_rect()
    aspect = float(title_rect.width)/float(title_rect.height)
    title_1= pygame.transform.scale(title_1, (int(H*aspect), H))
    title_2 = pygame.transform.scale(title_2, (int(H*aspect), H))
      
    title_to_show = title_1 if switch_frame else title_2
    SCREEN.blit(title_to_show, (W/2-H*aspect/2, 0))

    # TODO add WICO logo

    pygame.display.update()
    
def display_create_video(W, H):
    print('display_create_video')
    SCREEN.fill(TEAL)
    
    loading_images = ['src/assets/loading_1.png', 'src/assets/loading_2.png',
                      'src/assets/loading_3.png'];
    
    random_src = random.choice (loading_images)
    loading_image = pygame.image.load(random_src)
    loading_rect = loading_image.get_rect()
    aspect = float(loading_rect.width)/float(loading_rect.height)
    loading_image = pygame.transform.scale(loading_image, (int(H*aspect), H))
     
    SCREEN.blit(loading_image, (int(W/2-H*aspect/2), 0))
    pygame.display.update()
    
def frame_capture():
    print('capture frame')
    ns = frame_get_numbers()
    n = max(ns) + 1 if len(ns) > 0 else 0
    frame_name = 'frames/frame_{n:04d}.jpg'.format(n=n)
    CAMERA.capture(frame_name, use_video_port=True)


def frame_display_ghost(W, H):
    last_image = frame_get_last(W, H)
    SCREEN.blit(last_image, (0, 0))
    pygame.display.update()


def frame_erase_last():
    ns = frame_get_numbers()
    if len(ns) > 0:
        n = max(ns)
        fname = 'frames/frame_{n:04d}.jpg'.format(n=n)
        if os.path.exists(fname):
            os.remove(fname)

def frame_get_last(W, H):
    ns = frame_get_numbers()
    if len(ns) > 0:
        n = max(ns)
        image = pygame.image.load('frames/frame_{n:04d}.jpg'.format(n=n))
        image = pygame.transform.scale(image, (W, H))
    else:
        image = pygame.Surface((W, H))
        image.fill([0, 0, 0])
    return image
                 
def frame_get_numbers():
    ns = []
    pattern = re.compile(r'frames\/frame\_(?P<num>\d+)\.jpg')
    for frame in glob.glob('frames/frame*.jpg'):
        m = re.match(pattern, frame)
        if m is not None:
            n = int(m.group('num'))
            ns.append(n)
    return sorted(ns)


def frames_delete():
    for frame in glob.glob('frames/frame*.jpg'):
        os.remove(frame)
    return 0

def get_pressed_buttons():
    return set([bnum for bnum in BUTTONS if BUTTONS[bnum].is_pressed])

def movie_make(fps):
    print('make movie')
    ns = frame_get_numbers()
    if len(ns) > 0:
        now = dt.datetime.now()
        movie_name = 'movies/{hour:02d}_{minute:02d}_{second:02d}.mp4'.format(
            hour=now.hour,
            minute=now.minute,
            second=now.second,
        )
        command = "ffmpeg -r {fps:d} -pattern_type glob -i 'frames/*.jpg' -c:v libx264 {movie_name:s}".format(fps=fps, movie_name=movie_name)
        os.system(command)
        return movie_name

def play_movie(name, W, H):
    print('play movie ', name)
    SCREEN.fill(TEAL)
    pygame.display.update()
    
    preview_playing = True
    ns = frame_get_numbers()
    
    # show preview background image
    preview = pygame.image.load('src/assets/preview.png')
    preview_rect = preview.get_rect()
    aspect = float(preview_rect.width)/float(preview_rect.height)
    preview = pygame.transform.scale(preview, (W, int(W/aspect)))
    preview_rect = preview.get_rect(center = (W/2, preview.get_rect().height/2))
    SCREEN.blit(preview, preview_rect)
    pygame.display.flip()
    
    while preview_playing:
        for n in ns:
            anim = pygame.image.load('frames/frame_{n:04d}.jpg'.format(n=n))

            # fill animation at 3/4 the height of the display
            scale = 0.7
            padding = 10
            anim_rect = anim.get_rect()
            aspect = float(anim_rect.width)/float(anim_rect.height)
            anim = pygame.transform.scale(anim, (int(scale*H*aspect), int(H*scale)))
            anim_rect = anim.get_rect(center=(W/2, anim.get_rect().height/2 + padding))
            SCREEN.blit(anim, anim_rect)
            CLOCK.tick(FPS)
            pygame.display.flip()
            
            # add info about video path
            font_size = 16
            font = pygame.font.Font('src/cafe.ttf', font_size)
            video_path_text = font.render('Video saved at {path:s}'.format(path=name),
                                        True, BLACK)
            video_path_text_rect = video_path_text.get_rect(center=(W/2, anim_rect.height + padding*4))
            SCREEN.blit(video_path_text, video_path_text_rect)
            
            # add retart button
            btn_width = 300 
            restart_btn_img = pygame.image.load('src/assets/restart_btn.png')
            restart_btn_rect = restart_btn_img.get_rect()
            btn_aspect = float(restart_btn_rect.width) / float(restart_btn_rect.height)
            restart_btn_img = pygame.transform.scale(restart_btn_img, (btn_width, int(btn_width/btn_aspect)))
            restart_rect = restart_btn_img.get_rect(center=(W/2, anim_rect.height + padding*8 + video_path_text_rect.height))
            SCREEN.blit(restart_btn_img, restart_rect)
            
            # check if user asked to exit and reset
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    print('stop video')
                    preview_playing = False
                    if event.key == pygame.K_ESCAPE:
                        quit_app()

def quit_app():
    print('quit app')
    frames_delete()
    quit(CAMERA)

def quit(camera):
    camera.close()
    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    # Ensure frames and movies directories exist.
    repodir = os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    for dirname in ('frames', 'movies'):
        absdir = os.path.join(repodir, dirname)
        if not os.path.exists(absdir):
            os.mkdir(absdir)

    # Initialize.
    FPS = 10
    FPS_MOVIE = 5
    pygame.init()
    W, H = pygame.display.list_modes()[0]

    # title screen frame info
    frame = 0 # used to cycle between frames for animations
    cycle = 5 # switch frames every 5 cycles
    screen = 0

    # new variables for easily changing scale for debugging purposes
    WIDTH = int(W)
    HEIGHT = int(H)
    
    print('Resolution: ({WIDTH}, {HEIGHT}).'.format(WIDTH=WIDTH, HEIGHT=HEIGHT))
    SCREEN = pygame.display.set_mode([WIDTH, HEIGHT])
    pygame.mouse.set_visible = False
    pygame.display.toggle_fullscreen()
    
    CLOCK = pygame.time.Clock()
    CAMERA = PiCamera()
    CAMERA.preview_alpha = 200
    CAMERA.resolution = (WIDTH, HEIGHT)
    
    # Main loop.
    while True:
        pressed = get_pressed_buttons()
        
        if reset:
            if frame >= cycle:
                frame = 0 
                screen = not screen
            display_start_screen(WIDTH, HEIGHT, screen)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        quit_app()
                    else: 
                        print('start app')
                        reset = False
                        # show camera preview
                        CAMERA.start_preview()
                        SCREEN.fill(WHITE)
                        pygame.display.update()
                        break
            frame += 1
        else:
            CAMERA.preview_alpha = 200

            # possible events
            delete_and_quit = False
            show_preview = False
            erase_last_frame = False
            take_picture = False
            make_and_save_movie = False
            exit_app = False

            # button press events
            pressed = get_pressed_buttons()              
            if pressed == {2}:
                delete_and_quit = True
            elif pressed == {3}:
                show_preview = True
            elif pressed == {4}:
                erase_last_frame = True
            elif pressed == {5}:
                take_picture = True
            elif pressed == {6}:
                make_and_save_movie = True
            elif pressed == {13}:
                exit_app = True

            # keyboard press events
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    key = event.key  
                    print('keypressed: ', key)
                  
                    # Delete frames and quit.
                    if key == pygame.K_SLASH: #forward slash
                        delete_and_quit = True                        
                    # Show preview.
                    elif key == pygame.K_SPACE: #space key
                        show_preview = True
                    # Erase the last frame
                    elif key == pygame.K_BACKSPACE: #backspace
                        erase_last_frame = True
                    # Take picture.
                    elif key == pygame.K_RETURN: #enter key
                        take_picture = True
                    # Make and save movie.
                    elif key == pygame.K_s: # s key
                        make_and_save_movie = True
                    # Exit program.
                    elif key == pygame.K_ESCAPE:
                        exit_app = True

            if delete_and_quit: 
                print('delete frames and quit')
                frames_delete()
                frame_display_ghost(WIDTH, HEIGHT)
            elif show_preview:
                print('show preview')
                CAMERA.stop_preview()
                ns = frame_get_numbers()
                for n in ns:
                    anim = pygame.image.load('frames/frame_{n:04d}.jpg'.format(n=n))
                    SCREEN.blit(anim, (0, 0))
                    CLOCK.tick(FPS)
                    pygame.display.flip()
                CLOCK.tick(FPS)
                frame_display_ghost(WIDTH, HEIGHT)
                CAMERA.start_preview(fullscreen=False, window = (W-WIDTH, 100, WIDTH, HEIGHT))
            elif erase_last_frame:
                print('erase last frame')
                frame_erase_last()
                frame_display_ghost(WIDTH, HEIGHT)
            elif take_picture:
                print('take picture')
                frame_capture()
                frame_display_ghost(WIDTH, HEIGHT)
            elif make_and_save_movie:
                print('make and save movie')
                CAMERA.preview_alpha = 0 # hide camera
                
                display_create_video(WIDTH, HEIGHT)
                CLOCK.tick(FPS)
                # make movie          
                new_movie = movie_make(FPS_MOVIE)
                play_movie(new_movie, WIDTH, HEIGHT)
                frames_delete()
                reset = True
            elif exit_app:
                print('exit')
                quit_app()