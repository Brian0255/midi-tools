"""
Version 0.9

This script does the following:
- Removes the empty track FL creates and merges the tempo track with another track, allowing 16 channels to be used.
- Multiplies all pitch values by 6 so they sound the same as in FL
- Converts velocity and volume events to the DK64 linear curve (as opposed to FL's exponential curve)
  - this probably needs more fine tuning
- Removes unrecognized MIDI events
- Deletes duplicate patch events caused by fl
  - This also condenses the subsequent events on the same tick caused by patch changes.
  - This means that fl midis no longer need to be offset or have events at the loop to fix the patch bug!!
"""

from mido import MidiFile
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

valid_CCs = {
    "volume": 7,
    "reverb": 91,
    "pan": 10,
}

def read_maxes(midi, velocities, volumes):
    for i in range(len(midi.tracks)):
        track = midi.tracks[i]
        for msg in track:
            match msg.type:
                case 'note_on':
                    velocities[i] = max(velocities[i], msg.velocity)
                case 'control_change':
                    if msg.control == valid_CCs["volume"]:
                        volumes[i] = max(volumes[i], msg.value)

def rebalance_from_input(midi, velocities, volumes):
    toRaise = 1
    while True:
        raiseInput = input("Enter percent value: ")
        if raiseInput.endswith("%"):
            raiseInput = raiseInput[:-1]
        try:
            toRaise = float(raiseInput)/100
        except ValueError:
            print("Invalid input.")
            continue
        for i in range(len(midi.tracks)):
            if velocities[i] == 0 or volumes[i] == 0:
                continue
            track = midi.tracks[i]
            toRaiseVol = min(127/volumes[i], toRaise)
            remainder = toRaise/toRaiseVol
            toRaiseVel = min(127/velocities[i], remainder)
            for msg in track:
                match msg.type:
                    case 'control_change':
                        if msg.control == valid_CCs["volume"]:
                            msg.value = round(msg.value * toRaiseVol)
            for msg in track:
                match msg.type:
                    case 'note_on':
                        msg.velocity = round(msg.velocity * toRaiseVel)
        print("Volume successfully rebalanced.")
        break

def rebalance(midi_file: str):
    midi = MidiFile(midi_file)
    velocities = [0] * len(midi.tracks)
    volumes = [0] * len(midi.tracks)
    read_maxes(midi, velocities, volumes)
    maxRaise = 100
    for i in range(len(midi.tracks)):
        if velocities[i] == 0 or volumes[i] == 0:
            continue
        maxRaise = min(maxRaise, (127.0/velocities[i] * 127.0/volumes[i]))
    maxPercent = str(round(maxRaise * 100)) + "%"
    print("Max percentage without compromising mix is " + maxPercent + ".")
    rebalance_from_input(midi, velocities, volumes)
    midi.save(midi_file.replace(".mid", "_rebalanced.mid"))
    input("Press any key to exit...")

rebalance(filedialog.askopenfilename())