import datetime as dt
import glob
import os
import pygame
import textinput
import re
import sys


from gpiozero import Button
from picamera import PiCamera


BUTTON_NUMBERS = [2, 3, 4, 5, 6, 13]


BUTTONS = {
    bnum: Button(bnum)
    for bnum in BUTTON_NUMBERS
}


def frame_capture():
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


def movie_make(name, fps):
    name = name.replace(' ', '_')
    ns = frame_get_numbers()
    if len(ns) > 0:
        now = dt.datetime.now()
        movie_name = 'movies/movie_{name:s}_{hour:02d}{minute:02d}.mp4'.format(
            hour=now.hour,
            minute=now.minute,
            name=name,
        )
        command = "ffmpeg -r {fps:d} -pattern_type glob -i 'frames/*.jpg' -c:v libx264 {movie_name:s}".format(fps=fps, movie_name=movie_name)
        os.system(command)


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
    print('Resolution: ({W}, {H}).'.format(W=W, H=H))
    SCREEN = pygame.display.set_mode([W, H])
    pygame.mouse.set_visible = False
    pygame.display.toggle_fullscreen()
    CLOCK = pygame.time.Clock()
    CAMERA = PiCamera()
    CAMERA.preview_alpha = 128
    CAMERA.resolution = (W, H)
    CAMERA.start_preview()

    # Main loop.
    frame_display_ghost(W, H)
    while True:
        # Get current keypresses.
        pressed = get_pressed_buttons()
        # Delete frames and quit.
        if pressed == {2}:
            frames_delete()
            frame_display_ghost(W, H)
        # Show preview.
        elif pressed == {3}:
            CAMERA.stop_preview()
            ns = frame_get_numbers()
            for n in ns:
                anim = pygame.image.load('frames/frame_{n:04d}.jpg'.format(n=n))
                SCREEN.blit(anim, (0, 0))
                CLOCK.tick(FPS)
                pygame.display.flip()
            CLOCK.tick(FPS)
            frame_display_ghost(W, H)
            CAMERA.start_preview()
        # Erase the last frame.
        elif pressed == {4}:
            frame_erase_last()
            frame_display_ghost(W, H)
        # Take picture.
        elif pressed == {5}:
            frame_capture()
            frame_display_ghost(W, H)
        # Make and save movie.
        elif pressed == {6}:
            textinput = textinput.TextInput(antialias=False)
            while True:
                SCREEN.fill((225, 225, 225))
                events = pygame.event.get()
                SCREEN.blit(textinput.get_surface(), (10, 10))
                if textinput.update(events):
                    movie_name = textinput.get_text()
                    break
                pygame.display.update()
                CLOCK.tick(FPS)
            movie_make(movie_name, FPS_MOVIE)
            frame_display_ghost(W, H)
        # Exit program.
        elif pressed == {13}:
            quit(CAMERA)
