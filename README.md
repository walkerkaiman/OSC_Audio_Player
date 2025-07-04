# 🎧 OSC Sound Server

A GUI-based Python application to trigger and control audio tracks via OSC (Open Sound Control). Designed for use in **interactive installations**, stage shows, or responsive art environments.

---

## ✨ Features

- Receive OSC messages to trigger sound playback
- GUI for managing multiple audio tracks
- Per-track volume and mute controls
- Master volume control
- Auto-saving configuration (`config.json`)
- Auto-restarts OSC server on input changes
- Scrollable waveform viewer with playback cursor
- OSC message logging display
- Audio asset management via built-in `Audio/` folder
- Cross-platform-ready (Windows first, Linux support planned)

---

## 📦 Installation

1. Dependencies (Dev Environment)
   Install requirements:

pip install -r requirements.txt

2. Run the App (Dev Mode)
   python main.py

3. Build a Standalone Executable (Windows)
   Install PyInstaller:
   pip install pyinstaller

Build:
(Windows)
pyinstaller --noconsole --onefile --add-data "Audio;Audio" main.py

This creates an .exe in /dist that can run without Python installed.

## 🕹️ Using the App

General Workflow

- Launch the app
- Add a new track
- Load an audio file via file dialog
- Set OSC Address (e.g. /light1/trigger)
- Set volume or mute as needed
- Send OSC messages to trigger playback

GUI Overview

- Add Track button: Adds a new audio player row
- OSC Address: Set this to the OSC message that should trigger the track
- Volume / Mute: Individual track controls
- Master Volume: Applies globally
- Log Window: Shows received OSC messages, server restarts, and errors

## 📡 OSC Setup

The OSC server listens on all IPs (0.0.0.0) on the specified port (default: 8000)
This app only looks at the OSC address. If you need a different message to the same address do so by making different audio tracks with unique addresses.

- "/trigger"
- "/trigger/0"
- "/trigger/1"

You can send OSC from tools like:

- TouchOSC
- QLab
- Processing
- Touch Designer
- Other Python / Max / Node apps

This repo includes an OSC test script to test locally. Make sure to change IP to the listed one in the app header and match the port numbers of the OSC server and client (app).

🔧 Configuration
Stored in config.json. Automatically saved on every change.

{
"osc_port": 8000,
"master_volume": 1.0,
"tracks": [
{
"file": "thunder.wav",
"volume": 1.0,
"mute": false,
"osc_message": "/storm"
}
]
}

🔐 File Behavior

- All loaded audio files are copied into the /Audio folder
- Only files in /Audio are played by the app
- .png waveforms are generated for each file (and auto-updated)

🛠️ Best Practices for Installations

1. Place the app in a dedicated folder with write access
2. Copy your startup config.json and preload audio assets into /Audio
3. Auto-launch the .exe using Task Scheduler or Startup folder (Windows)
4. Test OSC communication across your network (firewall must allow incoming UDP)
5. Label OSC triggers clearly (e.g., /seesaw/start, /tree/chime)

📁 Project Structure

OSC_Audio_Player/
├── main.py # main script
├── config.json # auto-generated config
├── Audio/ # stores audio files & waveform .pngs
├── requirements.txt
├── README.md
└── .gitignore

💻 Linux Notes

When ready to run on Linux:

- Rebuild using PyInstaller on a Linux machine
- Ensure PulseAudio or ALSA is working
- You may need to chmod +x the binary

```

```
