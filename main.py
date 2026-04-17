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

# Pyjnius imports for Android
if platform == 'android':
    from jnius import autoclass, PythonJavaClass, java_method
    from android.runnable import run_on_ui_thread

    Locale = autoclass('java.util.Locale')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
    Intent = autoclass('android.content.Intent')

    # Native Android TTS
    class TTSListener(PythonJavaClass):
        __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']
        def onInit(self, status):
            if status == TextToSpeech.SUCCESS:
                global tts_instance
                tts_instance.setLanguage(Locale.US)

    tts_listener = TTSListener()
    tts_instance = TextToSpeech(PythonActivity.mActivity, tts_listener)

    def speak_text(text):
        if tts_instance:
            tts_instance.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)

    # Native Android STT
    speech_text = None
    speech_event = threading.Event()

    class SpeechListener(PythonJavaClass):
        __javainterfaces__ = ['android/speech/RecognitionListener']

        def __init__(self):
            super().__init__()

        @java_method('(Landroid/os/Bundle;)V')
        def onReadyForSpeech(self, params): pass

        @java_method('()V')
        def onBeginningOfSpeech(self): pass

        @java_method('(F)V')
        def onRmsChanged(self, rmsdB): pass

        @java_method('([B)V')
        def onBufferReceived(self, buffer): pass

        @java_method('()V')
        def onEndOfSpeech(self): pass

        @java_method('(I)V')
        def onError(self, error):
            global speech_event
            speech_event.set()

        @java_method('(Landroid/os/Bundle;)V')
        def onResults(self, results):
            global speech_text, speech_event
            matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            if matches and matches.size() > 0:
                speech_text = matches.get(0)
            speech_event.set()

        @java_method('(Landroid/os/Bundle;)V')
        def onPartialResults(self, partialResults): pass

        @java_method('(ILandroid/os/Bundle;)V')
        def onEvent(self, eventType, params): pass

    speech_listener = SpeechListener()

    def get_user_speech(timeout=5):
        global speech_text, speech_event
        speech_text = None
        speech_event.clear()

        @run_on_ui_thread
        def start_recognition():
            if not hasattr(get_user_speech, 'recognizer'):
                get_user_speech.recognizer = SpeechRecognizer.createSpeechRecognizer(PythonActivity.mActivity)
                get_user_speech.recognizer.setRecognitionListener(speech_listener)
            
            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault().toString())
            get_user_speech.recognizer.startListening(intent)

        start_recognition()
        speech_event.wait() # Blocking wait to keep the AI Loop synchronous
        return speech_text if speech_text else ""

else:
    # Desktop mockups
    def speak_text(text):
        print(f"[JARVIS SPEAKS]: {text}")

    def get_user_speech(timeout=5):
        time.sleep(3)
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
        self.chat_log = TransparentChatLog(size_hint=(0.9, 0.33), pos_hint={'center_x': 0.5, 'y': 0.1})
        self.add_widget(self.chat_log)

        self.chat_log.add_message("SYSTEM", "Android HUD Initialized. Press START to listen.")

        # Control Buttons
        from kivy.uix.button import Button
        btn_layout = BoxLayout(size_hint=(0.9, 0.08), pos_hint={'center_x': 0.5, 'y': 0.01}, spacing=10)
        
        self.btn_start = Button(text="START JARVIS", background_color=(0, 0.8, 0.2, 1), bold=True)
        self.btn_start.bind(on_release=self.start_jarvis)
        
        self.btn_stop = Button(text="STOP JARVIS", background_color=(0.8, 0, 0, 1), bold=True)
        self.btn_stop.bind(on_release=self.stop_jarvis)
        
        btn_layout.add_widget(self.btn_start)
        btn_layout.add_widget(self.btn_stop)
        self.add_widget(btn_layout)

        # AI Threading Control
        self.ai_running = False
        self.ai_thread = threading.Thread(target=self.ai_loop)
        self.ai_thread.daemon = True

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def log_ui(self, sender, text):
        Clock.schedule_once(lambda dt: self.chat_log.add_message(sender, text))

    def set_emotion(self, emotion):
        Clock.schedule_once(lambda dt: setattr(self.ring, 'emotion', emotion))
        Clock.schedule_once(lambda dt: setattr(self.status_lbl, 'text', f"[b]SYSTEM {emotion.upper()}[/b]"))

    def start_jarvis(self, instance):
        if self.ai_running: return
        self.ai_running = True
        
        if platform == 'android':
            try:
                from jnius import autoclass
                context = autoclass('org.kivy.android.PythonActivity').mActivity
                service_class = autoclass('org.test.jarvishud.ServiceJarvisbackground')
                intent = autoclass('android.content.Intent')(context, service_class)
                intent.putExtra("pythonServiceArgument", "")
                context.startService(intent)
            except Exception as e:
                self.log_ui("SYSTEM", f"Notification Service error: {e}")

        if not self.ai_thread.is_alive():
            self.ai_thread = threading.Thread(target=self.ai_loop)
            self.ai_thread.daemon = True
            self.ai_thread.start()
        self.log_ui("SYSTEM", "AI Loop and Service Started.")

    def stop_jarvis(self, instance):
        self.ai_running = False
        if platform == 'android':
            try:
                from jnius import autoclass
                context = autoclass('org.kivy.android.PythonActivity').mActivity
                service_class = autoclass('org.test.jarvishud.ServiceJarvisbackground')
                intent = autoclass('android.content.Intent')(context, service_class)
                context.stopService(intent)
            except Exception as e:
                pass
        self.log_ui("SYSTEM", "AI Loop and Service Stopped.")

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
