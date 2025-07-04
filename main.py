import os
import json
import threading
import tkinter as tk
from tkinter import filedialog
from pygame import mixer
from pythonosc import dispatcher, osc_server
from PIL import Image, ImageTk
from pydub import AudioSegment
import matplotlib.pyplot as plt
import socket
import psutil
import time

CONFIG_FILE = "config.json"
AUDIO_FOLDER = "Audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

mixer.init()

# Global track list
tracks = []
playing_tracks = set()

# Load config
config = {"tracks": [], "osc_port": 8000}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Corrupt config file. Starting fresh.")

# GUI root
root = tk.Tk()
root.title("Sound Server")
root.configure(bg="black")
root.geometry("700x800")
root.resizable(False, True)

font_settings = ("Segoe UI", 10)
title_font_settings = ("Segoe UI", 12, "bold")
label_opts = {"bg": "black", "fg": "white", "font": font_settings}
title_label_opts = {"bg": "black", "fg": "white", "font": title_font_settings}
entry_opts = {"bg": "#222", "fg": "white", "insertbackground": "white", "font": font_settings}

# Helper function to get IP addresses
def get_ip_addresses():
    wifi_ip = "N/A"
    eth_ip = "N/A"
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                if "Wi-Fi" in iface or "wlan" in iface.lower():
                    wifi_ip = addr.address
                elif "Ethernet" in iface or "eth" in iface.lower():
                    eth_ip = addr.address
    return wifi_ip, eth_ip

wifi_ip, eth_ip = get_ip_addresses()

# OSC + Master Volume row
info_frame = tk.Frame(root, bg="black")
info_frame.pack(fill="x", pady=(20, 10), padx=10)

ip_info_frame = tk.Frame(info_frame, bg="black")
ip_info_frame.pack(side="left", padx=(0, 20))
tk.Label(ip_info_frame, text=f"WiFi IP: {wifi_ip}", **label_opts).pack(anchor="w")
tk.Label(ip_info_frame, text=f"Ethernet IP: {eth_ip}", **label_opts).pack(anchor="w")

osc_port_frame = tk.Frame(info_frame, bg="black")
osc_port_frame.pack(side="left", padx=(0, 20))
tk.Label(osc_port_frame, text="OSC Port:", **title_label_opts).pack(anchor="w")
osc_port = tk.IntVar(value=config.get("osc_port", 8000))
osc_entry = tk.Entry(osc_port_frame, textvariable=osc_port, width=6, **entry_opts)
osc_entry.pack()

vol_frame = tk.Frame(info_frame, bg="black")
vol_frame.pack(side="right")

vol_label = tk.Label(vol_frame, text="Master Volume", **title_label_opts)
vol_label.pack(anchor="e")
master_volume = tk.DoubleVar(value=1.0)
tk.Scale(vol_frame, from_=0, to=1, resolution=0.01, orient="horizontal", variable=master_volume,
         bg="black", fg="white", troughcolor="#444", highlightthickness=0, length=200).pack(anchor="e")

# Scrollable track container
track_frame = tk.Frame(root, bg="black")
track_frame.pack(fill="both", expand=True)

canvas = tk.Canvas(track_frame, bg="black", highlightthickness=0)
scrollbar = tk.Scrollbar(track_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="black")
scrollable_frame.bind(
    "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

track_container = scrollable_frame
add_track_button = tk.Button(root, text="Add Track", **label_opts)
add_track_button.pack(pady=10)

# Enable mouse wheel scrolling on the canvas
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def _on_linux_mousewheel(event):
    canvas.yview_scroll(1 if event.num == 5 else -1, "units")

if root.tk.call("tk", "windowingsystem") == 'win32':
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
elif root.tk.call("tk", "windowingsystem") == 'x11':
    canvas.bind_all("<Button-4>", _on_linux_mousewheel)
    canvas.bind_all("<Button-5>", _on_linux_mousewheel)
else:
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

cursor_running = True

# Updated audio cursor and independent track playback logic
track_instances = {}

def update_audio_cursor():
    while cursor_running:
        for track in tracks:
            canvas = track.get("canvas")
            channel = track.get("channel")
            sound = track.get("sound")
            start_time = track.get("start_time")
            duration = track.get("duration")
            if canvas and channel and channel.get_busy() and sound and start_time and duration:
                current_time = time.time() - start_time
                canvas_width = canvas.winfo_width()
                x = int((current_time / duration) * canvas_width)
                canvas.delete("cursor")
                canvas.create_line(x, 0, x, canvas.winfo_height(), fill="red", tags="cursor")
        time.sleep(0.05)

# Cursor fix
cursor_thread = threading.Thread(target=lambda: update_audio_cursor(), daemon=True)
cursor_thread.start()

def play_track(track):
    if not track.get("sound"):
        return

    sound = mixer.Sound(track["file"])
    volume = 0 if track["mute_var"].get() else track["volume_var"].get() * master_volume.get()
    channel = sound.play()
    if not channel:
        return

    channel.set_volume(volume)
    track["start_time"] = time.time()
    track["duration"] = sound.get_length()
    track["channel"] = channel

    track["file_label"].config(text=os.path.basename(track["file"]))

    def stop_check():
        if not channel.get_busy():
            track["channel"] = None
        else:
            root.after(100, stop_check)

    stop_check()
    playing_tracks.add(id(channel))

def save_config():
    to_save = {
        "osc_port": osc_port.get(),
        "tracks": []
    }
    for t in tracks:
        to_save["tracks"].append({
            "file": t["file"],
            "volume": t["volume_var"].get(),
            "osc_message": t["osc_message"].get(),
            "mute": t["mute_var"].get()
        })
    with open(CONFIG_FILE, "w") as f:
        json.dump(to_save, f, indent=4)

def draw_waveform(filepath, canvas):
    try:
        sound = AudioSegment.from_file(filepath)
        samples = sound.get_array_of_samples()
        plt.figure(figsize=(8, 2))
        plt.plot(samples, color="white")
        plt.axis('off')
        img_path = filepath + ".png"
        plt.savefig(img_path, bbox_inches='tight', pad_inches=0, facecolor='black')
        plt.close()

        image = Image.open(img_path)

        def update_canvas(event=None):
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width > 0 and height > 0:
                resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
                tk_image = ImageTk.PhotoImage(resized_image)
                canvas.delete("all")
                canvas.create_image(0, 0, anchor="nw", image=tk_image)
                canvas.image = tk_image

        canvas.bind("<Configure>", update_canvas)
        canvas.update_idletasks()
        update_canvas()
    except Exception as e:
        print(f"Waveform error: {e}")

def update_volume(track):
    ch = track.get("channel")
    if ch:
        vol = track["volume_var"].get() * master_volume.get()
        if track["mute_var"].get():
            ch.set_volume(0)
        else:
            ch.set_volume(vol)

def play_track(track):
    if track["mute_var"].get():
        return
    if not track.get("sound"):
        return
    key = track["file"]
    if key in tracks:
        return
    sound = track["sound"]
    volume = track["volume_var"].get() * master_volume.get()
    channel = sound.play()
    if not channel:
        return
    track["start_time"] = time.time()
    track["duration"] = sound.get_length()

    channel.set_volume(volume)
    track["channel"] = channel
    playing_tracks.add(key)

    def stop_check():
        if not channel.get_busy():
            playing_tracks.discard(key)
            track["channel"] = None
        else:
            root.after(100, stop_check)

    stop_check()

def remove_track(track):
    ch = track.get("channel")
    if ch:
        ch.stop()
    track["frame"].destroy()
    if track in tracks:
        tracks.remove(track)
    save_config()

def add_track(track_data):
    track_frame = tk.Frame(track_container, bg="black", bd=2, relief="groove")
    track_frame.pack(fill="x", padx=10, pady=5)

    for i in range(4):
        track_frame.grid_columnconfigure(i, weight=1)

    col0 = tk.Frame(track_frame, bg="black")
    col0.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    file_label = tk.Label(col0, text="Click To Select Audio...", **label_opts)
    file_label.pack(anchor="w")
    canvas = tk.Canvas(col0, width=300, height=100, bg="#111", highlightthickness=0)
    canvas.pack(fill="x")

    col1 = tk.Frame(track_frame, bg="black")
    col1.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    volume_var = tk.DoubleVar(value=track_data.get("volume", 1.0))
    mute_var = tk.BooleanVar(value=track_data.get("mute", False))
    tk.Scale(col1, from_=0, to=1, resolution=0.01, orient="horizontal",
             variable=volume_var, label="Volume", length=120, bg="black",
             fg="white", troughcolor="#444", highlightthickness=0).pack()
    tk.Checkbutton(col1, text="Mute", variable=mute_var,
                   bg="black", fg="white", selectcolor="black").pack(pady=4)

    col2 = tk.Frame(track_frame, bg="black")
    col2.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
    tk.Label(col2, text="OSC Address", **label_opts).pack(anchor="w")
    osc_message = tk.StringVar(value=track_data.get("osc_message", "/trigger"))
    tk.Entry(col2, textvariable=osc_message, **entry_opts).pack(fill="x")

    col3 = tk.Frame(track_frame, bg="black")
    col3.grid(row=0, column=3, sticky="nsew", padx=5, pady=5)
    play_btn = tk.Button(col3, text="Play", command=lambda: play_track(track), bg="#333", fg="white")
    play_btn.pack(fill="x", pady=(0, 4))
    remove_btn = tk.Button(col3, text="Remove", command=lambda: remove_track(track), bg="#500", fg="white")
    remove_btn.pack(fill="x")

    filename = track_data.get("file", "")
    sound = None
    if filename:
        fullpath = os.path.join(AUDIO_FOLDER, filename)
        try:
            sound = mixer.Sound(fullpath)
            draw_waveform(fullpath, canvas)
        except:
            print("⚠️ Couldn't load preconfigured audio.")

    def load_file():
        path = filedialog.askopenfilename()
        if path:
            filename = os.path.basename(path)
            dest = os.path.join(AUDIO_FOLDER, filename)
            if not os.path.exists(dest):
                with open(path, "rb") as fsrc, open(dest, "wb") as fdst:
                    fdst.write(fsrc.read())
            track["file"] = filename
            try:
                track["sound"] = mixer.Sound(dest)
                draw_waveform(dest, canvas)
            except:
                print("⚠️ Invalid audio file")
        save_config()

    file_label.bind("<Button-1>", lambda e: load_file())

    track = {
        "frame": track_frame,
        "canvas": canvas,
        "volume_var": volume_var,
        "mute_var": mute_var,
        "osc_message": osc_message,
        "file": filename,
        "sound": sound,
        "channel": None
    }

    volume_var.trace_add("write", lambda *args: update_volume(track))
    mute_var.trace_add("write", lambda *args: update_volume(track))
    master_volume.trace_add("write", lambda *args: update_volume(track))

    tracks.append(track)
    save_config()

def start_osc_server(port):
    disp = dispatcher.Dispatcher()
    for track in tracks:
        if "osc_message" in track:
            trigger = track["osc_message"].get()
            disp.map(trigger, lambda addr, *args, tr=track: play_track(tr))
    try:
        server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", int(port)), disp)
        print(f"✅ OSC Server started on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Failed to start OSC server: {e}")

for tdata in config.get("tracks", []):
    add_track(tdata)

add_track_button.config(command=lambda: add_track({}))

osc_thread = threading.Thread(target=lambda: start_osc_server(osc_port.get()), daemon=True)
osc_thread.start()

def on_closing():
    mixer.stop()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
