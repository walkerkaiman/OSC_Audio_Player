from pythonosc.udp_client import SimpleUDPClient
import time

# Set these values to match your OSC Audio Player
TARGET_IP = "192.168.4.21"  # Use your computer's IP or 127.0.0.1 if local
TARGET_PORT = 8000       # Match the OSC port in the GUI
OSC_ADDRESS = "/ping"    # Match the OSC address entered in the GUI

# Create the OSC client
client = SimpleUDPClient(TARGET_IP, TARGET_PORT)

# Send test messages
print(f"Sending OSC messages to {TARGET_IP}:{TARGET_PORT} at address {OSC_ADDRESS}")
for i in range(3):
    client.send_message(OSC_ADDRESS, f"test {i}")
    print(f"Sent: {OSC_ADDRESS} test {i}")
    time.sleep(1)
