import math
import random

import time
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Rectangle
from kivy.properties import NumericProperty, ReferenceListProperty, \
    BooleanProperty, ObjectProperty, ListProperty
from kivy.uix.label import Label
from kivy.uix.widget import Widget

class RootApp(App):
    pass

HELP_STRING = \
"""Controls

Left: move left
Right: move right
Down: SUPER power up
Up: throw spear
n: start new game
h: toggle help
Spacebar: toggle pause
"""

def clamp(n, min_n, max_n):
    return max(min(n, max_n), min_n)

class Ball(Widget):

    accel = NumericProperty(-90)

    speed_x_variance = NumericProperty(100)

    speed_x = NumericProperty(200)
    speed_y = NumericProperty(0)
    speed = ReferenceListProperty(speed_x, speed_y)

    base_x = NumericProperty(0)
    end_x = NumericProperty(0)
    base_y = NumericProperty(0)
    end_y = NumericProperty(0)

    range_x = ReferenceListProperty(base_x, end_x)
    range_y = ReferenceListProperty(base_y, end_y)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.bind(range_y=self.check_borders)
        self.bind(range_x=self.check_borders)

        self.speed_x = random.randint(self.speed_x - self.speed_x_variance,
                                      self.speed_x + self.speed_x_variance)
        self.speed_x *= (random.getrandbits(1) * 2) - 1

        self.size = 10, 10

    def get_max_speed(self):
        return math.sqrt(2 * self.accel * (self.y - self.end_y))

    def check_borders(self, *args):
        if self.y < self.base_y:
            self.speed_y *= -1

        if self.x < self.base_x or self.x + self.width > self.end_x:
            self.speed_x *= -1

        self.x = clamp(self.x, self.base_x, self.end_x - self.width)
        self.y = clamp(self.y, self.base_y, self.end_y - self.height)
        max_speed = self.get_max_speed()
        self.speed_y = clamp(self.speed_y, -max_speed, max_speed)

    def randomize_x(self):
        self.x = random.randint(self.base_x, self.end_x - self.width)


    def update_state(self, dt):
        if self.speed_y != 0 or self.y > self.base_y:
            self.speed_y += self.accel * dt
            self.y += self.speed_y * dt
        self.x += self.speed_x * dt
        self.check_borders()


class Player(Widget):

    max_speed = NumericProperty(200)
    speed = NumericProperty(0)
    accel = NumericProperty(100)
    move_right = BooleanProperty(False)
    move_left = BooleanProperty(False)
    r = NumericProperty(1)
    g = NumericProperty(1)
    b = NumericProperty(1)

    rgb = ReferenceListProperty(r, g, b)

    is_powered = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._power_rectangle = None
        self.bind(is_powered=self.update_powerup)
        self._is_powered = False
        self._base_size = (20, 40)
        self.size = self._base_size

    def update_powerup(self, *args):
        if self.is_powered:
            self.rgb = (1, 1, 0)
        else:
            self.rgb = (1, 1, 1)

    def update_state(self, dt):
        if self.move_right:
            self.speed += self.accel * dt
        elif self.speed > 0:
            self.speed = max(0, self.speed - self.accel * dt)

        if self.move_left:
            self.speed -= self.accel * dt
        elif self.speed < 0:
            self.speed = min(0, self.speed + self.accel * dt)

        self.speed = clamp(self.speed, -self.max_speed, self.max_speed)
        self.x += self.speed * dt

    def on_is_powered(self, *args):
        power_size = 80
        if self.is_powered:
            self.x -= (power_size/2 - self.width/2)
            self.size = (power_size, power_size)
            self.rgb = (1, 1, 0)
            with self.canvas:
                Color(*self.rgb)
                self._power_rectangle = Rectangle(pos=self.pos, size=(power_size, power_size))
        else:
            self.rgb = (1, 1, 1)
            self.canvas.remove(self._power_rectangle)
            self.x += (self.width/2 - self._base_size[0]/2)
            self.size = self._base_size

    def on_pos(self, *args):
        if self._power_rectangle is not None:
            self._power_rectangle.pos = self.pos

    def check_collision(self, item):
        return item.x <= self.x + self.width and item.x + item.width >= self.x and \
               item.y <= self.y + self.height and item.y + item.height >= self.y


class Ray(Widget):

    speed = NumericProperty(250)

    def __init__(self, x_orig, y_orig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.height = 0
        self.width = 10
        self.x = x_orig - self.width/2
        self.y = y_orig

    def update_state(self, dt):
        self.height += self.speed * dt

class RayTimeout(Widget):

    is_timeout_over = BooleanProperty(True)
    duration = NumericProperty(0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._remaining_duration = self.duration

        with self.canvas:
            Color(1, 1, 1)
            self._rectangle = Rectangle(pos=self.pos,size=(0, self.height))

        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self._rectangle.pos = self.pos
        if self.is_timeout_over or self.duration == 0:
            width = 0
        else:
            width = self._remaining_duration/self.duration * self.width
        self._rectangle.size = width, self.height

    def on_is_timeout_over(self, *args):
        self.update_canvas()

    def on_duration(self, *args):
        self._remaining_duration = self.duration

    def reset_timeout(self):
        self.is_timeout_over = False
        self._remaining_duration = self.duration

    def update_state(self, dt):
        if not self.is_timeout_over:
            if self._remaining_duration <= 0:
                self.is_timeout_over = True
            else:
                self._remaining_duration -= dt
            self.update_canvas()

class TimerVisualizer(Widget):

    seconds = NumericProperty(0)
    should_count = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = Label(font_size=50, text="None")
        self.update_label()
        self.add_widget(self._label)
        self._start_time = int(time.time())
        self.bind(pos=self.update_label, size=self.update_label, seconds=self.update_label)
        self._label.bind(texture_size=self.update_label, size=self.update_label)
        self.bind(should_count=self.reset_timer)

    def reset_timer(self, *args):
        if self.should_count:
            self.seconds = 0

    def update_state(self, dt):
        if self.should_count:
            self.seconds += dt

    def update_label(self, *args):
        self._label.pos = self.x - self._label.width, self.y - self._label.height
        self._label.text = str(int(self.seconds))

class RayCountVisualizer(Widget):

    how_many = NumericProperty(0)
    rec_width = NumericProperty(10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind(how_many=self.update)
        self.bind(pos=self.update)
        self._label = None

    def update(self, *args):
        if self.how_many >= 20:
            if self._label is None:
                self._label = Label()
                self.add_widget(self._label)
            self._label.pos = self.x, self.y - 20
            self._label.text = str(self.how_many)
        else:
            if self._label is not None:
                self.remove_widget(self._label)
                self._label = None
            self.canvas.clear()
            with self.canvas:
                Color(1, 1, 1)
                for n in range(self.how_many):
                    pos = self.x + 2 * n * self.rec_width, self.y
                    size = self.rec_width, self.height
                    Rectangle(pos=pos, size=size)


class GamePanel(Widget):

    pause = BooleanProperty(False)

    should_add_ball = BooleanProperty(False)
    add_ball_interval = NumericProperty(2)

    ray_interval = NumericProperty(4)

    powered_duration = NumericProperty(4)
    remains_powered = NumericProperty(0)

    both_directions = BooleanProperty(False)
    rays = ListProperty()
    balls = ListProperty()

    ray_timeout = ObjectProperty(rebind=True)

    player = ObjectProperty(rebind=True)
    visualizer = ObjectProperty(rebind=True)
    timer = ObjectProperty(rebind=True)

    max_rays = NumericProperty(float("inf"))
    left_rays = NumericProperty(0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Clock.schedule_interval(self.update_state, 0.03)
        self._keyboard = Window.request_keyboard(None, self)
        self._keyboard.bind(on_key_down=self.on_key_down)
        self._keyboard.bind(on_key_up=self.on_key_up)
        self.left_rays = self.max_rays
        self.bind(size=self.update_screen_size)
        self._remains_to_next_ball = 0
        self._last_ray_time = 0
        self.remains_powered = self.powered_duration
        self.bind(add_ball_interval=self.update_remains_to_next_ball)
        self.register_event_type('on_help_toggle')

    def on_help_toggle(self, *args):
        pass

    def update_remains_to_next_ball(self, *args):
        self._remains_to_next_ball = self.add_ball_interval

    def on_key_down(self, keyboard, keycode, *args):
        if self.pause:
            return
        if keycode[1] == "right":
            if self.player.move_left:
                self.player.move_left = False
                self.both_directions = True
            elif not self.both_directions:
                self.player.move_right = True
        elif keycode[1] == "left":
            if self.player.move_right:
                self.player.move_right = False
                self.both_directions = True
            elif not self.both_directions:
                self.player.move_left = True
        elif keycode[1] == "down":
            self.give_player_power()

    def on_key_up(self, keyboard, keycode, *args):
        if keycode[1] == "spacebar":
            self.pause = not self.pause
        elif self.pause:
            pass
        elif keycode[1] == "right":
            if self.both_directions:
                self.both_directions = False
                self.player.move_left = True
            else:
                self.player.move_right = False
        elif keycode[1] == "left":
            if self.both_directions:
                self.both_directions = False
                self.player.move_right = True
            else:
                self.player.move_left = False
        elif keycode[1] == "up":
            self.add_ray()
        elif keycode[1] == "a":
            self.add_ball()
        elif keycode[1] == "p":
            if self.player not in self.children:
                self.add_widget(self.player)
        elif keycode[1] == "n":
            self.new_level()
        elif keycode[1] == "h":
            self.dispatch("on_help_toggle")

    def new_level(self):
        self.left_rays = self.max_rays
        if self.player not in self.children:
            self.add_widget(self.player)
        self.remove_balls()
        self.remove_rays()
        self.should_add_ball = True
        self._remains_to_next_ball = 0
        if self.timer:
            self.timer.should_count = True
            self.timer.reset_timer()
        if self.ray_timeout is not None:
            self.ray_timeout.is_timeout_over = True

    def update_player(self, dt):
        self.player.update_state(dt)
        if self.player.is_powered:
            self.remains_powered -= dt
            if self.remains_powered < 0:
                self.player.is_powered = False
        if self.player.x < 0:
            self.move_left = False
            self.player.speed = max(self.player.speed, 0)
            self.player.x = 0
        if self.player.x + self.player.size[0] > self.size[0]:
            self.move_right = False
            self.player.speed = min(self.player.speed, 0)
            self.player.x = self.size[0] - self.player.size[0]

    def give_player_power(self):
        if self.player in self.children and self.left_rays > 0 and not self.player.is_powered:
            self.player.is_powered = True
            self.remains_powered = self.powered_duration
            self.left_rays -= 1

    def add_ray(self):
        if self.player in self.children and self.ray_timeout.is_timeout_over:
            self.ray_timeout.reset_timeout()
            ray = Ray(self.player.x + self.player.width/2, self.player.y + self.player.height)
            self.rays.append(ray)
            self.add_widget(ray)
            #self.left_rays -= 1

    def add_ball(self):
        ball = Ball(base_x=0, end_x=self.width,
                    base_y=self.player.y, end_y=min(self.height, 400),
                    speed_y=0)
        ball.randomize_x()
        ball.y = ball.end_y
        ball.check_borders()

        self.balls.append(ball)
        self.add_widget(ball)

    def update_screen_size(self, *args):
        for ball in self.balls:
            ball.end_x = self.width
            ball.end_y = min(self.height, 400)

    def on_max_rays(self, *args):
        self.left_rays = self.max_rays

    def on_powered_duration(self, *args):
        self.remains_powered = self.powered_duration

    def update_state(self, dt):
        if self.pause:
            return
        if self.player is not None:
            self.update_player(dt)
        new_rays = []
        if self.should_add_ball:
            self._remains_to_next_ball -= dt
            if self._remains_to_next_ball <= 0:
                self.update_remains_to_next_ball()
                self.add_ball()
        for ray in self.rays:
            ray.update_state(dt)
            if ray.y + ray.height >= self.height:
                self.remove_widget(ray)
            else:
                new_rays.append(ray)
        self.rays = new_rays
        for ball in self.balls:
            ball.update_state(dt)
        self.check_collisions()
        if self.timer is not None:
            self.timer.update_state(dt)

        if self.ray_timeout is not None:
            self.ray_timeout.update_state(dt)

    def check_collisions(self):
        to_remove = set()
        for ball in self.balls:
            if self.player.is_powered and self.player.check_collision(ball):
                to_remove.add(ball)
            for ray in self.rays:
                if not (ball.x > ray.x + ray.width or ball.x + ball.width < ray.x) and\
                   not (ball.y > ray.y + ray.height or ball.y + ball.height < ray.y):
                    to_remove.add(ball)
                    to_remove.add(ray)

        self.balls = [ball for ball in self.balls if ball not in to_remove]
        self.rays = [ray for ray in self.rays if ray not in to_remove]
        for child in to_remove:
            self.remove_widget(child)

        collided = False
        for ball in self.balls:
            if self.player.check_collision(ball):
                collided = True
                break
        if collided:
            self.remove_widget(self.player)
            self.remove_balls()
            self.timer.should_count = False
            self.should_add_ball = False

    def remove_balls(self):
        for ball in self.balls:
            self.remove_widget(ball)
        self.balls = []

    def remove_rays(self):
        for ray in self.rays:
            self.remove_widget(ray)
        self.rays = []

def main():
    RootApp().run()

if __name__ == '__main__':
    main()
