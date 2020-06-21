import tkinter as tk
import threading
import pyaudio
import wave
import pickle
import librosa
import math
import numpy as np
import scipy
import soundfile as sf
import os


class App:
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 2
    fs = 44100
    frames = []

    # modelpath =
    model_files = [os.path.join("models/", fname) for fname in
                   os.listdir("models/") if fname.endswith('.pkl')]
    models = [pickle.load(open(fname, 'rb')) for fname in model_files]
    speakers = [fname.split("/")[-1].split(".pkl")[0] for fname
                in model_files]

    def __init__(self):

        self.root = tk.Tk()
        self.root.title('Speech Recognition')
        self.root.geometry('400x400')
        self.root.bind("<Key>", self.keypress)


        self.sentences = []
        self.is_recording = False
        self.button1 = tk.Button( self.root, text='record', command=self.start, width=10)
        self.button2 = tk.Button( self.root, text='stop', command=self.stop, width=10)
        self.button3 = tk.Button( self.root, text="play", command=self.play, width=10)
        self.button4 = tk.Button( self.root, text="remove noise", command=self.remove_noise, width=10)
        # self.button5 = tk.Button(main, text="Predict", command=self.predict, width=10)

        self.text = tk.Text( self.root, height=20, width=50)

        self.button1.pack()
        self.button2.pack()
        self.button3.pack()
        self.button4.pack()
        # self.button5.pack()
        self.text.pack()

        self.predict = ''
        self.root.mainloop()

    def start(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.sample_format, channels=self.channels, rate=self.fs,
                                  frames_per_buffer=self.chunk, input=True)
        self.is_recording = True

        print('Recording')
        self.t = threading.Thread(target=self.record)
        self.t.start()

    def stop(self):
        self.is_recording = False
        print('recording complete')

        filename = 'data.wav'
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.sample_format))
        wf.setframerate(self.fs)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        self.frames.clear()
        self.pre()

    def pre(self):
        filename = 'data.wav'
        O = self.get_mfcc(filename)
        log_likelihood = np.zeros(len(self.models))

        for i in range(len(self.models)):
            gmm = self.models[i]  # checking with each model one by one
            scores = np.array(gmm.score(O, [len(O)]))
            log_likelihood[i] = scores.sum()

        winner = np.argmax(log_likelihood)
        pre = self.speakers[winner]
        self.predict = pre
        self.set_predict_text()

    def record(self):
        while self.is_recording:
            data = self.stream.read(self.chunk)
            self.frames.append(data)

    def set_predict_text(self):
        text = 'Không thể đoán nhận từ vừa đọc'
        text = self.predict

        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, text)

    def get_mfcc(self, file_path):
        y, sr = librosa.load(file_path)  # read .wav file
        hop_length = math.floor(sr * 0.010)  # 10ms hop
        win_length = math.floor(sr * 0.025)  # 25ms frame
        # mfcc is 12 x T matrix
        mfcc = librosa.feature.mfcc(
            y, sr, n_mfcc=20, n_fft=1024,
            hop_length=hop_length, win_length=win_length)
        # substract mean from mfcc --> normalize mfcc
        mfcc = mfcc - np.mean(mfcc, axis=1).reshape((-1, 1))
        # delta feature 1st order and 2nd order
        delta1 = librosa.feature.delta(mfcc, order=1)
        delta2 = librosa.feature.delta(mfcc, order=2)
        # X is 36 x T
        X = np.concatenate([mfcc, delta1, delta2], axis=0)  # O^r
        # return T x 36 (transpose of X)
        return X.T  # hmmlearn use T x N matrix

    def play(self):
        filename = 'data.wav'
        chunk = 1024
        wf = wave.open(filename, 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True)

        data = wf.readframes(chunk)

        while len(data) > 0:  # is_playing to stop playing
            stream.write(data)
            data = wf.readframes(chunk)
        stream.stop_stream()
        stream.close()
        p.terminate()

    def trim_silence(self, y):
        y_trimmed, index = librosa.effects.trim(y, top_db=20, frame_length=25, hop_length=10)
        trimmed_length = librosa.get_duration(y) - librosa.get_duration(y_trimmed)
        return y_trimmed, trimmed_length

    def remove_noise(self):
        y, sr = librosa.load("data.wav")
        y_trimmed, index = librosa.effects.trim(y, top_db=20, frame_length=2, hop_length=500)
        y_reduced_median = scipy.signal.medfilt(y_trimmed, 3)

        trimmed_length = librosa.get_duration(y) - librosa.get_duration(y_trimmed)
        sf.write('data.wav', y_reduced_median, sr, 'PCM_24')
        self.pre()

    def keypress(self, event):
        """Recieve a keypress and move the ball by a specified amount"""
        print(event.char)
        if event.char == 'p':
            self.play()

        if event.char == 'r':
            print(True)
            self.start()

        if event.char == 's':
            self.stop()

        if event.char == 'q':
            self.remove_noise()



# main = tk.Tk()
# main.title('Speech Recognition')
# main.geometry('400x400')
#
# app = App(main)
# main.mainloop()

display = App()