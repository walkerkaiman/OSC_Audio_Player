🎛️ Sound Server GUI
A lightweight Python-based GUI tool for managing multiple audio tracks with OSC triggering, independent volume control, waveform previews, and real-time playback cursors. Built with Tkinter, pygame, and python-osc.

📦 Features
Add/remove multiple audio tracks

Individual volume and mute controls per track

Live waveform display with red playback cursor

OSC-triggered audio playback (/trigger by default)

Master volume slider

Static IP address display for both Wi-Fi and Ethernet

Track settings saved between sessions

Drag-and-drop loading of audio files

Scrollable interface supporting 16+ tracks

Responsive cursor animation (even when muted)

🖥️ Requirements
Install required dependencies with:
pip install -r requirements.txt

Minimal requirements.txt
matplotlib==3.10.3
Pillow==11.3.0
psutil==7.0.0
pydub==0.25.1
pygame==2.6.1
python-osc==1.9.3

▶️ Usage
Run the GUI with:
py -3.ll main.py

Configuration
Audio files are stored in the Audio/ folder.

Settings (volume, mute, OSC address, etc.) are saved to config.json.

Default OSC port is 8000.

🎚️ OSC Integration
Each track can be triggered with an OSC message:

Default address: /trigger

Customize per track in the GUI

OSC server listens on the specified port (default: 8000)

Send an OSC message using Python:
from pythonosc.udp_client import SimpleUDPClient
client = SimpleUDPClient("127.0.0.1", 8000)
client.send_message("/trigger", 1)

🧪 Tips
Clicking “Add Track” will add a new track row at the bottom.

Each track can be triggered manually using the Play button.

You can scroll using the mouse wheel to navigate through many tracks.

📁 File Structure

📁 Audio/ # Audio files saved here
📄 config.json # Persistent settings for tracks
📄 main.py # Main GUI application
📄 requirements.txt # Python dependencies
