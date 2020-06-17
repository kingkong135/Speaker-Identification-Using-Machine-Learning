# Import the necessary modules.
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import pyaudio
import wave
import os
import re

DATA_PATH = 'record'
CACHE_FILE = '__cache.wav'

class VoiceDetector:
    def __init__(self, chunk=2048, format=pyaudio.paInt16, channels=2, rate=44100, py=pyaudio.PyAudio()):
        # Clear cache file
        cache_full_path = os.path.join(DATA_PATH, CACHE_FILE)
        if os.path.exists(cache_full_path):
            os.remove(cache_full_path)

        # Start Tkinter and set Title
        self.main = tkinter.Tk()
        self.collections = []
        self.main.geometry('600x360')
        self.main.title('INT3411 - Speech Processing')
        self.CHUNK, self.FORMAT, self.CHANNELS, self.RATE, self.p = chunk, format, channels, rate, py
        self.frames = []
        self.st = 1
        self.play = 0
        self.pre_rec = tk.StringVar()   # trace pre-record box value changed
        self.pre_rec.trace('w', self.load_record)
        self.current_file = ''  # currenty source audio
        self.stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)

        # Set Frames
        self.header = tkinter.Frame(self.main, padx=10, pady=10)
        self.content = tkinter.Frame(self.main, padx=10, pady=5)
        self.footer = tkinter.Frame(self.main, padx=10, pady=10)

        # Pack Frame
        self.header.pack(side=tk.TOP)
        self.content.pack()
        self.footer.pack(side=tk.BOTTOM)

        # Record selection box
        self.pre_rec_lbl = tk.Label(self.header, text="Pre-record:")
        self.pre_rec_lbl.grid(row=0, column=0, padx=(0, 10))
        self.pre_rec_box = ttk.Combobox(self.header, values=self.get_pre_record_list(), state="readonly", textvar=self.pre_rec)
        self.pre_rec_box.grid(row=0, column=1, padx=(0, 50))

        # Predict result
        self.predict_result = tk.Label(self.content, text="Predict result", font=("Arial", 24))
        self.predict_result.grid(row=0, column=0, sticky='S', ipady=70)

        # Action bar
        ## Record button
        self.action_btn = tk.Button(self.footer, width=10, padx=10, pady=5, text='Start Recording', command=lambda: self.start_record())
        self.action_btn.grid(row=0, column=0, padx=(0, 10), pady=5)
        ## Play button
        self.play_btn = tk.Button(self.footer, width=5, padx=10, pady=5, text='Play', command=lambda: self.play_audio(), state=tk.DISABLED)
        self.play_btn.grid(row=0, column=1, padx=(0, 10), pady=5)
        ## Predict button
        self.predict_btn = tk.Button(self.footer, width=5, padx=10, pady=5, text='Predict', command=lambda: self.predict(), state=tk.DISABLED)
        self.predict_btn.grid(row=0, column=2, padx=(0, 10), pady=5)
        ## State (recording, playing)
        self.state_lbl = tk.Label(self.footer, width=35, text='Waiting for action ...')
        self.state_lbl.grid(row=0, column=3, padx=10)

        tkinter.mainloop()

    def change_btn_state(self, s, *args):
        for btn in args:
            btn['state'] = s

    def load_record(self, *args):
        self.current_file = self.pre_rec.get()

    def add_person(self):
        # Not implemented
        pass

    def predict(self, wav_file):
        # Not implemented
        pass

    def get_pre_record_list(self):
        result = []
        for file in os.listdir(DATA_PATH):
            result.append(file)
        return list(result)

    def play_audio(self):
        self.play = 1
        audio_full_path = os.path.join(DATA_PATH, self.current_file)
        file_exists = os.path.exists(audio_full_path) and os.path.isfile(audio_full_path)
        self.state_lbl['text'] = 'Playing {:s} ...'.format(current_file) if (file_exists) else 'File {:s} not found!'.format(current_file)

        if (not file_exists): return

        self.change_btn_state(tk.DISABLED, self.pre_rec_box, self.action_btn)
        self.play_btn.configure(text='Stop', command=self.stop_audio)
        wf = wave.open(audio_full_path, 'rb')
        stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()), channels=wf.getnchannels(), rate=wf.getframerate(), output=True)
        data = wf.readframes(self.CHUNK)

        while self.play == 1 and len(data) > 0:
            stream.write(data)
            data = wf.readframes(self.CHUNK)
            self.main.update()

        stream.stop_stream()
        stream.close()

        self.change_btn_state(tk.NORMAL, self.pre_rec_box, self.action_btn)
        self.play_btn.configure(text='Play', command=self.play_audio)
        self.state_lbl['text'] = 'Waiting for action ...'

    def stop_audio(self):
        self.play = 0

    def start_record(self):
        self.st = 1
        self.frames = []
        self.change_btn_state(tk.DISABLED, self.pre_rec_box, self.play_btn, self.predict_btn)
        self.action_btn.configure(text='Stop Recording', command=self.stop_record)
        output_target = os.path.join(DATA_PATH, CACHE_FILE)
        self.state_lbl['text'] = 'Recording to {:s} ...'.format(output_target)
        stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)

        while self.st == 1:
            data = stream.read(self.CHUNK)
            self.frames.append(data)
            self.main.update()
        stream.close()

        wf = wave.open(os.path.join(DATA_PATH, CACHE_FILE), 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        self.current_file = CACHE_FILE
        self.action_btn.configure(text='Start Recording', command=self.start_record, state=tk.NORMAL)
        self.change_btn_state(tk.NORMAL, self.pre_rec_box, self.play_btn, self.predict_btn)

    def stop_record(self):
        self.st = 0

# Create an object of the ProgramGUI class to begin the program.
if __name__ == '__main__':
    guiAudio = VoiceDetector()