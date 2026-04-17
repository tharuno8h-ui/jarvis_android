import time
from os import environ

# This is a Kivy-compatible background service
# Its main purpose is to keep the Android OS from killing
# the Jarvis assistant while running in the background.
# The Kivy Android bootstrap will automatically create a 
# persistent Foreground Notification for this service.

if __name__ == '__main__':
    # We simply run an infinite loop here to keep the service alive.
    # The actual processing can be done via OSC IPC, or we can keep
    # main.py threads alive via the process group.
    
    while True:
        # Sleep to conserve battery while keeping the service active
        time.sleep(10)
