import threading
import time
import math

# Kivy configurations
from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '800')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.graphics import *
from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.utils import platform

# Import logic from command handling
from android_commands import process_command

# Polyfill for Voice (Text to Speech)
if platform == 'android':
    from plyer import tts
    def speak_text(text):
        try:
            tts.speak(text)
        except Exception as e:
            pass
else:
    # Desktop mockup for TTS
    def speak_text(text):
        print(f"[JARVIS SPEAKS]: {text}")

# Polyfill for Speech to Text
def get_user_speech(timeout=5):
    # This is a complex feature on Android. Without PyAudio, the standard way
    # is via Android intents or the kivy-android-speech module.
    # For this template, we simulate continuous wake word listening on desktop,
    # and provide the structural hook for Android STT.
    if platform == 'android':
        from jnius import autoclass
        # A fully robust background STT requires an Android Service, which buildozer 
        # supports, but is beyond a single script. Here we mock it so the UI works.
        # Normally you would launch RecognizerIntent here.
        time.sleep(2)
        return "" # Idle wait
    else:
        # Mocking for desktop build
        time.sleep(5) # Simulate listening
        return ""


class HolographicRing(Widget):
    angle = NumericProperty(0)
    angle_rev = NumericProperty(0)
    volume_level = NumericProperty(1.0)
    emotion = StringProperty("Idle")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(self.update_animation, 1.0 / 60.0)
        self.bind(pos=self.update_canvas, size=self.update_canvas, angle=self.update_canvas, emotion=self.update_canvas)

    def update_animation(self, dt):
        self.angle = (self.angle + 60 * dt) % 360
        self.angle_rev = (self.angle_rev - 90 * dt) % 360

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            cx = self.center_x
            cy = self.center_y

            # Core color depending on emotion
            core_col = (0, 0.8, 1, 0.2)
            if self.emotion == "Listening":
                core_col = (0, 1, 0.4, 0.3)
            elif self.emotion == "Speaking":
                core_col = (1, 0.5, 0, 0.3)
            elif self.emotion == "Processing":
                core_col = (1, 1, 0, 0.3)

            # Central Core Glow
            Color(*core_col)
            base_radius = min(self.width, self.height) * 0.2
            pulse = base_radius + abs(math.sin(self.angle/10)) * 10
            Ellipse(pos=(cx - pulse, cy - pulse), size=(pulse*2, pulse*2))

            # Outer ring 1 (Cyan, dashed effect via angle logic in shader, simplified here as Arc)
            Color(0, 1, 1, 0.8)
            radius = base_radius * 1.5
            PushMatrix()
            Translate(cx, cy)
            Rotate(origin=(0, 0), angle=self.angle)
            Line(circle=(0, 0, radius, 0, 90), width=2)
            Line(circle=(0, 0, radius, 120, 210), width=2)
            Line(circle=(0, 0, radius, 240, 330), width=2)
            PopMatrix()

            # Outer ring 2 (Reverse)
            Color(0, 0.5, 1, 0.5)
            radius2 = base_radius * 1.8
            PushMatrix()
            Translate(cx, cy)
            Rotate(origin=(0, 0), angle=self.angle_rev)
            Line(circle=(0, 0, radius2, 0, 180), width=1.5)
            Line(circle=(0, 0, radius2, 200, 340), width=1.5)
            PopMatrix()


class TransparentChatLog(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Translucent Background Canvas
        with self.canvas.before:
            Color(0, 0.1, 0.15, 0.4) # Semi-transparent bluish-dark tint
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        self.layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=10, spacing=10)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def add_message(self, sender, text):
        msg_col = (0, 1, 1, 1) if sender == "JARVIS" else (1, 1, 1, 1)
        lbl_text = f"[b]{sender}:[/b] {text}"
        
        lbl = Label(text=lbl_text, markup=True, size_hint_y=None, color=msg_col, text_size=(self.width - 20, None), font_name='Roboto')
        lbl.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1] + 10))
        lbl.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        
        self.layout.add_widget(lbl)
        # Scroll to bottom
        Clock.schedule_once(lambda dt: setattr(self, 'scroll_y', 0), 0.1)


class JarvisAndroid(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # True Black Background
        with self.canvas.before:
            Color(0.02, 0.02, 0.04, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        # 3D Ring Widget (Center)
        self.ring = HolographicRing(size_hint=(1, 0.5), pos_hint={'top': 0.95})
        self.add_widget(self.ring)

        # Status Label
        self.status_lbl = Label(text="[b]SYSTEM IDLE[/b]", markup=True, size_hint=(1, 0.05), pos_hint={'top': 0.98}, color=(0, 1, 1, 1))
        self.add_widget(self.status_lbl)

        # Transparent Chat Panel
        self.chat_log = TransparentChatLog(size_hint=(0.9, 0.4), pos_hint={'center_x': 0.5, 'y': 0.05})
        self.add_widget(self.chat_log)

        self.chat_log.add_message("SYSTEM", "Android HUD Initialized. Awaiting wake word / command.")

        # AI Threading Control
        self.ai_running = True
        self.ai_thread = threading.Thread(target=self.ai_loop)
        self.ai_thread.daemon = True
        self.ai_thread.start()

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def log_ui(self, sender, text):
        # Schedule UI update on main Kivy thread
        Clock.schedule_once(lambda dt: self.chat_log.add_message(sender, text))

    def set_emotion(self, emotion):
        Clock.schedule_once(lambda dt: setattr(self.ring, 'emotion', emotion))
        Clock.schedule_once(lambda dt: setattr(self.status_lbl, 'text', f"[b]SYSTEM {emotion.upper()}[/b]"))

    def ai_loop(self):
        # Continuous listening loop replacing PyQt thread loop
        while self.ai_running:
            self.set_emotion("Listening")
            text = get_user_speech() 
            
            if text:
                self.log_ui("USER", text)
                self.set_emotion("Processing")
                reply = process_command(text)
                self.log_ui("JARVIS", reply)
                self.set_emotion("Speaking")
                speak_text(reply)
                self.set_emotion("Idle")
            else:
                time.sleep(0.5)

class JarvisApp(App):
    def build(self):
        self.hud = JarvisAndroid()
        return self.hud

if __name__ == '__main__':
    JarvisApp().run()
