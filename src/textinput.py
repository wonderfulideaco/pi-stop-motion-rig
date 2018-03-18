
import pygame
import pygame.locals as pl
import os.path
pygame.font.init()


class TextInput:

    '''
    Lets a user enter text using pygame.
    '''

    def __init__(
        self,
        antialias=True,
        cursor_color=(0, 0, 1),
        font_family='',
        font_size=35,
        repeat_keys_initial_ms=400,
        repeat_keys_interval_ms=35,
        text_color=(0, 0, 0),
    ):

        self.antialias = antialias
        self.text_color = text_color
        self.font_size = font_size
        self.input_string = ''
        if not os.path.isfile(font_family):
            font_family = pygame.font.match_font(font_family)
        self.font_object = pygame.font.Font(font_family, font_size)

        self.surface = pygame.Surface((1, 1))
        self.surface.set_alpha(0)

        self.keyrepeat_counters = {}
        self.keyrepeat_intial_interval_ms = repeat_keys_initial_ms
        self.keyrepeat_interval_ms = repeat_keys_interval_ms

        self.cursor_surface = pygame.Surface((int(self.font_size / 20 + 1), self.font_size))
        self.cursor_surface.fill(cursor_color)
        self.cursor_position = 0
        self.cursor_visible = True
        self.cursor_switch_ms = 500
        self.cursor_ms_counter = 0

        self.clock = pygame.time.Clock()

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.cursor_visible = True

                if event.key not in self.keyrepeat_counters:
                    self.keyrepeat_counters[event.key] = [0, event.unicode]

                if event.key == pl.K_BACKSPACE:
                    self.input_string = self.input_string[:max(self.cursor_position - 1, 0)] + \
                        self.input_string[self.cursor_position:]

                    self.cursor_position = max(self.cursor_position - 1, 0)
                elif event.key == pl.K_DELETE:
                    self.input_string = self.input_string[:self.cursor_position] + \
                        self.input_string[self.cursor_position + 1:]

                elif event.key == pl.K_RETURN:
                    return True

                elif event.key == pl.K_RIGHT:
                    self.cursor_position = min(self.cursor_position + 1, len(self.input_string))

                elif event.key == pl.K_LEFT:
                    self.cursor_position = max(self.cursor_position - 1, 0)

                elif event.key == pl.K_END:
                    self.cursor_position = len(self.input_string)

                elif event.key == pl.K_HOME:
                    self.cursor_position = 0

                else:
                    self.input_string = self.input_string[:self.cursor_position] + \
                        event.unicode + \
                        self.input_string[self.cursor_position:]
                    self.cursor_position += len(event.unicode)

            elif event.type == pl.KEYUP:
                if event.key in self.keyrepeat_counters:
                    del self.keyrepeat_counters[event.key]

        for key in self.keyrepeat_counters:
            self.keyrepeat_counters[key][0] += self.clock.get_time()
            if self.keyrepeat_counters[key][0] >= self.keyrepeat_intial_interval_ms:
                self.keyrepeat_counters[key][0] = self.keyrepeat_intial_interval_ms - \
                    self.keyrepeat_interval_ms

                event_key, event_unicode = key, self.keyrepeat_counters[key][1]
                pygame.event.post(pygame.event.Event(pl.KEYDOWN, key=event_key, unicode=event_unicode))

        prompt_string = 'Please enter your movie name and press <ENTER>: {input_string:s}'.format(input_string=self.input_string)
        self.surface = self.font_object.render(prompt_string, self.antialias, self.text_color)

        self.cursor_ms_counter += self.clock.get_time()
        if self.cursor_ms_counter >= self.cursor_switch_ms:
            self.cursor_ms_counter %= self.cursor_switch_ms
            self.cursor_visible = not self.cursor_visible

        if self.cursor_visible:
            cp = self.get_cursor_position()
            cursor_y_pos = self.font_object.size(self.input_string[:cp])[0]
            if self.cursor_position > 0:
                cursor_y_pos -= self.cursor_surface.get_width()
            self.surface.blit(self.cursor_surface, (cursor_y_pos, 0))

        self.clock.tick()
        return False

    def get_surface(self):
        return self.surface

    def get_text(self):
        return self.input_string

    def get_cursor_position(self):
        return self.cursor_position

    def set_text_color(self, color):
        self.text_color = color

    def set_cursor_color(self, color):
        self.cursor_surface.fill(color)
