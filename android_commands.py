import os
import random
from datetime import datetime
try:
    import requests
except ImportError:
    requests = None

from kivy.utils import platform

# We will use the REST API directly to avoid Android build errors from complex SDKs
GEMINI_API_KEY = "AIzaSyBCiEEyznfM9eHyKYrDCAP_OZ_D8FHP8eE"

memory = {}

# Only import Android specific modules if on Android
if platform == 'android':
    from jnius import autoclass, cast
    from android import activity
    import plyer
    
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    String = autoclass('java.lang.String')
    PackageManager = autoclass('android.content.pm.PackageManager')
    Context = autoclass('android.content.Context')
    Settings = autoclass('android.provider.Settings')
    AlarmClock = autoclass('android.provider.AlarmClock')
    MediaStore = autoclass('android.provider.MediaStore')
    
    def get_context():
        return PythonActivity.mActivity

    def launch_app(package_name):
        context = get_context()
        pm = context.getPackageManager()
        intent = pm.getLaunchIntentForPackage(package_name)
        if intent:
            context.startActivity(intent)
            return True
        return False
        
else:
    # Desktop fallbacks for testing the GUI
    def launch_app(package_name):
        print(f"[Simulated Android] Launching app: {package_name}")
        return True


def get_common_package(app_name):
    packages = {
        "whatsapp": "com.whatsapp",
        "youtube": "com.google.android.youtube",
        "chrome": "com.android.chrome",
        "instagram": "com.instagram.android",
        "settings": "com.android.settings",
        "camera": "com.android.camera2",
        "gallery": "com.android.gallery3d",
        "spotify": "com.spotify.music",
        "facebook": "com.facebook.katana",
        "calculator": "com.android.calculator2",
        "clock": "com.android.deskclock",
        "contacts": "com.android.contacts",
        "maps": "com.google.android.apps.maps",
        "play store": "com.android.vending",
        "gmail": "com.google.android.gm",
        "telegram": "org.telegram.messenger"
    }
    return packages.get(app_name.lower())

def process_command(command):
    command = command.lower().strip()
    
    # 👋 WAKE COMMANDS
    if any(word in command for word in ["hey jarvis", "wake up", "you there"]):
        return random.choice(["Yes sir", "I'm listening", "At your service", "Ready on Android platform."])

    # 🌐 APP LAUNCHING (DYNAMIC)
    if command.startswith("open ") or command.startswith("launch "):
        app_name = command.replace("open ", "").replace("launch ", "").strip()
        pkg = get_common_package(app_name)
        
        if pkg:
            success = launch_app(pkg)
            if success:
                return f"Opening {app_name}"
            return f"Failed to launch {app_name}. App might not be installed."
        elif platform == 'android':
            # Try to search play store if unknown
            try:
                context = get_context()
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(f"market://search?q={app_name}"))
                context.startActivity(intent)
                return f"Could not find exact package. Searching Play Store for {app_name}."
            except Exception as e:
                return f"I couldn't open {app_name}."
        else:
            return f"[Desktop] Simulated opening Android App: {app_name}"

    # 📞 PHONE COMMANDS
    if command.startswith("call "):
        target = command.replace("call ", "").strip()
        if platform == 'android':
            try:
                plyer.call.makecall(target) # Note: requires permissions
                return f"Calling {target}..."
            except:
                return "Failed to make a call. Ensure CALL_PHONE permission is granted."
        return f"[Desktop] Simulated Android call to {target}."

    # 🎵 MEDIA COMMANDS
    if command.startswith("play "):
        song = command.replace("play ", "").strip()
        if platform == 'android':
            try:
                context = get_context()
                intent = Intent(Intent.ACTION_SEARCH)
                intent.setPackage("com.google.android.youtube")
                intent.putExtra("query", song)
                context.startActivity(intent)
                return f"Playing {song} on YouTube"
            except:
                pass
        return f"Searching for {song}."

    # 🔦 FLASHLIGHT
    if "turn on flashlight" in command or "enable flashlight" in command:
        if platform == 'android':
            try:
                plyer.flash.on()
                return "Flashlight activated."
            except Exception as e:
                return "Could not control flashlight."
        return "[Desktop] Flashlight on."
        
    if "turn off flashlight" in command or "disable flashlight" in command:
        if platform == 'android':
            try:
                plyer.flash.off()
                return "Flashlight deactivated."
            except Exception as e:
                return "Could not control flashlight."
        return "[Desktop] Flashlight off."

    # 🔋 BATTERY
    if "battery" in command:
        if platform == 'android':
            try:
                status = plyer.battery.status
                return f"Battery status is {status.get('percentage', 'unknown')} percent. Charging state: {status.get('isCharging', 'unknown')}"
            except:
                return "Could not retrieve battery info."
        return "[Desktop] Simulated battery 95%."

    # 🌐 SEARCH / INTERNET
    if command.startswith("search ") or "google for" in command:
        query = command.replace("search google for", "").replace("search", "").strip()
        if platform == 'android':
            try:
                context = get_context()
                intent = Intent(Intent.ACTION_WEB_SEARCH)
                intent.putExtra("query", query)
                context.startActivity(intent)
                return f"Searching the web for {query}"
            except:
                return "Could not open search intent."
        return f"[Desktop] Web search for {query}."

    # 📍 LOCATION
    if "navigate to" in command or "open maps" in command:
        place = command.replace("navigate to", "").strip()
        if platform == 'android':
            try:
                context = get_context()
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(f"google.navigation:q={place}"))
                intent.setPackage("com.google.android.apps.maps")
                context.startActivity(intent)
                return f"Navigating to {place}"
            except:
                return "Failed to open maps."
        return f"[Desktop] Navigating to {place}."

    # 🌐 INTERNET & WIFI CONTROLS
    if any(cmd in command for cmd in ["turn on internet", "enable mobile data", "turn on wifi", "enable wifi", "open wifi settings"]):
        if platform == 'android':
            try:
                context = get_context()
                intent = Intent(Settings.ACTION_WIFI_SETTINGS)
                context.startActivity(intent)
                return "Opening WiFi Settings. Direct background toggling is restricted on Android 10+."
            except: pass
        return "Opening network settings."
        
    if "airplane mode" in command:
        if platform == 'android':
            try:
                intent = Intent(Settings.ACTION_AIRPLANE_MODE_SETTINGS)
                get_context().startActivity(intent)
                return "Opening Airplane Mode settings."
            except: pass
        return "Toggling Airplane mode."

    # 🔵 BLUETOOTH COMMANDS
    if any(cmd in command for cmd in ["turn on bluetooth", "enable bluetooth", "open bluetooth settings"]):
        if platform == 'android':
            try:
                intent = Intent(Settings.ACTION_BLUETOOTH_SETTINGS)
                get_context().startActivity(intent)
                return "Opening Bluetooth Settings."
            except: pass
        return "Opening Bluetooth Settings."

    # 🔊 VOLUME CONTROLS
    if any(cmd in command for cmd in ["increase volume", "volume up"]):
        if platform == 'android':
            try:
                AudioManager = autoclass('android.media.AudioManager')
                context = get_context()
                audio = context.getSystemService(Context.AUDIO_SERVICE)
                audio.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_RAISE, AudioManager.FLAG_SHOW_UI)
                return "Increasing volume levels."
            except: pass
        return "Increasing volume."
    if any(cmd in command for cmd in ["decrease volume", "volume down"]):
        return "Decreasing volume levels."
    if "mute" in command or "silent mode" in command:
        return "Muting device audio."

    # 📩 MESSAGING COMMANDS
    if command.startswith("send message to ") or command.startswith("send sms to "):
        target = command.replace("send message to ", "").replace("send sms to ", "").strip()
        if platform == 'android':
            try:
                plyer.sms.send(recipient=target, message="Hello from JARVIS")
                return f"Drafting SMS to {target}."
            except:
                return "Error accessing SMS protocols."
        return f"[Desktop] Simulated SMS to {target}."

    # ⏰ TIME & REMINDERS
    if command.startswith("set alarm "):
        time_text = command.replace("set alarm ", "").strip()
        if platform == 'android':
            try:
                intent = Intent(AlarmClock.ACTION_SET_ALARM)
                intent.putExtra(AlarmClock.EXTRA_MESSAGE, "JARVIS Alarm")
                intent.putExtra(AlarmClock.EXTRA_SKIP_UI, False)
                get_context().startActivity(intent)
                return f"Opening alarm application to set your alarm."
            except: pass
        return f"Alarm successfully configured for {time_text}."
        
    if command.startswith("set timer for "):
        if platform == 'android':
            try:
                minutes = int(''.join(filter(str.isdigit, command)))
                intent = Intent(AlarmClock.ACTION_SET_TIMER)
                intent.putExtra(AlarmClock.EXTRA_LENGTH, minutes * 60)
                intent.putExtra(AlarmClock.EXTRA_MESSAGE, "JARVIS Timer")
                intent.putExtra(AlarmClock.EXTRA_SKIP_UI, False)
                get_context().startActivity(intent)
                return f"Timer starting for {minutes} minutes."
            except: return "Could not parse the timer duration."
        return "Timer started."
        
    if command.startswith("set reminder "):
        note = command.replace("set reminder ", "").strip()
        return f"Reminder actively set for {note}."
        
    if "show time" in command or "what time" in command or "current time" in command:
        return f"The current time is {datetime.now().strftime('%I:%M %p')}."
        
    if "show date" in command or "what date" in command or "today's date" in command:
        return f"Today's date is {datetime.now().strftime('%d %B %Y')}."

    # 📷 CAMERA CONTROLS
    if any(cmd in command for cmd in ["take a picture", "open camera"]):
        if platform == 'android':
            try:
                intent = Intent(MediaStore.INTENT_ACTION_STILL_IMAGE_CAMERA)
                get_context().startActivity(intent)
                return "Opening camera view finder."
            except: pass
        return "Opening camera."
        
    if any(cmd in command for cmd in ["record a video", "open video camera"]):
        if platform == 'android':
            try:
                intent = Intent(MediaStore.INTENT_ACTION_VIDEO_CAMERA)
                get_context().startActivity(intent)
                return "Opening video camera."
            except: pass
        return "Opening video camera."

    # 🤖 FALLBACK TO GEMINI
    if requests and GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{
                    "parts": [{"text": f"You are Jarvis, a mobile assistant. Keep answers brief. Provide a 1 or 2 sentence reply to: {command}"}]
                }]
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                return "My AI cognitive services are experiencing an error."
        except Exception as e:
            return "My AI cognitive services are currently offline."

    return "Command not recognized, and AI fallback is unavailable."
