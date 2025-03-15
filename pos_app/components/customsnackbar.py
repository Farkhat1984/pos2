from kivymd.uix.card import MDCard
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty
from kivymd.app import MDApp
from kivy.core.window import Window


class CustomSnackbar(MDCard):
    text = StringProperty("")
    duration = NumericProperty(1.5)

    def __init__(self, **kwargs):
        super(CustomSnackbar, self).__init__(**kwargs)
        self.size_hint = (0.8, None)
        self.height = "48dp"
        self.md_bg_color = [0.2, 0.6, 1, 1]  # Голубой цвет
        self.radius = [10, 10, 10, 10]
        self.elevation = 4
        self.padding = "12dp"

    def open(self):
        app = MDApp.get_running_app()
        # Вместо добавления к root (который является ScreenManager)
        # добавляем к Window
        Window.add_widget(self)

        # Анимация появления
        self.opacity = 0
        self.pos_hint = {"center_x": 0.5, "y": -0.1}
        anim = Animation(opacity=1, pos_hint={"center_x": 0.5, "y": 0.1}, duration=0.3)
        anim.start(self)

        # Исчезновение после заданной продолжительности
        Clock.schedule_once(self.dismiss, self.duration)

    def dismiss(self, *args):
        anim = Animation(opacity=0, pos_hint={"center_x": 0.5, "y": -0.1}, duration=0.3)
        anim.bind(on_complete=lambda *args: Window.remove_widget(self))
        anim.start(self)