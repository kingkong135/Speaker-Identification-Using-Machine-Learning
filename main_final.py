# Import the necessary modules.
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import tkinter.messagebox
import pyaudio
import wave
import os
import re
import pickle
import librosa
import math
import numpy as np
import scipy
import soundfile as sf

# work with browser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time

# lock desktop
import ctypes

DATA_PATH = 'record'
CACHE_FILE = '__cache.wav'
BROWSER = webdriver.Edge
# DRIVER = r'C:/Users/vieta/Downloads/chromedriver'
DRIVER = r'./chromedriver_linux64/chromedriver'



class VoiceDetector:
    def __init__(self, chunk=2048, format=pyaudio.paInt16, channels=2, rate=44100, py=pyaudio.PyAudio()):
        # Clear cache file
        cache_full_path = os.path.join(DATA_PATH, CACHE_FILE)
        if os.path.exists(cache_full_path):
            os.remove(cache_full_path)

        # Load model
        model_files = [os.path.join("models/", fname) for fname in
                       os.listdir("models/") if fname.endswith('.pkl')]
        self.models = [pickle.load(open(fname, 'rb')) for fname in model_files]
        self.speakers = [fname.split("/")[-1].split(".pkl")[0] for fname
                         in model_files]
        self.predict_person = ''
        self.is_celeb = False

        # Load model predict function
        self.model_function = pickle.load(open("model_predict_function.pkl", "rb"))
        self.predict_function_result = ''

        # Start Tkinter and set Title
        self.main = tkinter.Tk()
        self.main.bind("<Key>", self.keypress)
        self.collections = []
        self.main.geometry('800x400')
        self.main.title('INT3411 - Speech Processing')
        self.CHUNK, self.FORMAT, self.CHANNELS, self.RATE, self.p = chunk, format, channels, rate, py
        self.frames = []
        self.st = 1
        self.play = 0
        self.current_file = '__cache.wav'  # currenty source audio
        self.stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True,
                                  frames_per_buffer=self.CHUNK)

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
        self.pre_rec_btn = tk.Button(self.header, text="Select file", command=self.select_file, width=10)
        self.pre_rec_btn.grid(row=0, column=1, padx=(0, 10))
        self.pre_rec_filename = tk.Label(self.header, width=0, text='No file selected')
        self.pre_rec_filename.grid(row=0, column=2, padx=(0,))

        # Predict result
        self.predict_result = tk.Label(self.content, text="Predict speaker", font=("Arial", 24))
        self.predict_result.grid(row=0, column=0, sticky='S', ipady=70)
        self.predict_function_text = tk.Label(self.content, text="Action: ")
        self.predict_function_text.grid(row=1, column=0)

        # Action bar
        # Record button
        self.action_btn = tk.Button(self.footer, width=10, padx=10, pady=5, text='Start Record',
                                    command=lambda: self.start_record())
        self.action_btn.grid(row=0, column=0, padx=(0, 10), pady=5)
        # Play button
        self.play_btn = tk.Button(self.footer, width=5, padx=10, pady=5, text='Play', command=lambda: self.play_audio(),
                                  state=tk.DISABLED)
        self.play_btn.grid(row=0, column=1, padx=(0, 10), pady=5)
        # Predict button
        self.predict_btn = tk.Button(self.footer, width=5, padx=10, pady=5, text='Predict',
                                     command=lambda: self.predict(), state=tk.DISABLED)
        self.predict_btn.grid(row=0, column=2, padx=(0, 10), pady=5)
        # Do action checkbox
        self.detect_action_chk = tk.BooleanVar()
        self.detect_action_chk.set(False)
        self.detect_action_chkbox = tk.Checkbutton(self.footer, text='Detect action', var=self.detect_action_chk)
        self.detect_action_chkbox.grid(row=0, column=3, padx=(15, 10))
        # self.predict_function_btn = tk.Button(self.footer, width=10, padx=10, pady=5, text='Predict function', command= self.predict_function)
        # self.predict_function_btn.grid(row=1, column=0, padx=(0, 10), pady=5)
        # Execute function
        self.execute_btn = tk.Button(self.footer, width=10, padx=10, pady=5, text='Execute',
                                     command=self.handle_function)
        self.execute_btn.grid(row=0, column=4, padx=(0, 50), pady=5)
        # State (recording, playing)
        self.state_lbl = tk.Label(self.footer, width=35, text='Waiting for action ...')
        self.state_lbl.grid(row=0, column=5)

        # Login logout function
        self.is_login = False
        self.first_time_browser = True
        self.login_user = ''
        self.uetcodehub = 'https://uetcodehub.xyz/'
        # self.browser = BROWSER(DRIVER)
        # load dataset including all user's account
        self.account = {}
        with open('./data/database.txt', encoding='utf-8') as f:
            for line in f.readlines():
                name, user, password, fullname = line.strip().split(',')
                self.account[name] = [name, user, password, fullname]

        tkinter.mainloop()

    def check_close_browser(self):
        DISCONNECTED_MSG = 'Unable to evaluate script: disconnected: not connected to DevTools\n'
        if len(self.browser.get_log('driver')) == 0:
            print("not closed yet")
            return False
        elif self.browser.get_log('driver')[-1]['message'] == DISCONNECTED_MSG:
            print('Browser window closed by user')
            return True

    def login(self, user):
        self.login_user = user
        self.browser.get('https://uetcodehub.xyz/')
        username = self.account[user][1]
        password = self.account[user][2]

        username_input = self.browser.find_element_by_id("inputName")
        password_input = self.browser.find_element_by_id("inputPassword")
        username_input.send_keys(username)
        password_input.send_keys(password)
        self.browser.find_element_by_id("submit").click()
        self.is_login = True

    def logout(self):
        self.login_user = ''
        self.browser.get('https://uetcodehub.xyz/')
        menu_dropdown = self.browser.find_element_by_id("action-menu-0-menubar")
        if menu_dropdown:
            menu_dropdown.click()
            logout = self.browser.find_element_by_id("actionmenuaction-6")
            logout.click()
            self.is_login = False

    def lock_desktop(self, user):
        # change this to specify user
        if user == 'Tiến Đạt':
            os_name = os.name
            if os_name == 'nt':
                ctypes.windll.user32.LockWorkStation()
            elif os_name == 'posix':
                os.system(
                    'dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock')
        else:
            self.state_lbl['text'] = "Can't lock because you aren't the owner"

    def search_web(self, user):
        self.browser.get('http://www.google.com')

        search = self.browser.find_element_by_name('q')
        # search.send_keys("google search through python")
        if self.is_celeb == True:
            search.send_keys(self.predict_person)
            self.is_celeb = False
        else:
            search.send_keys(self.account[user][3])
        search.send_keys(Keys.RETURN)  # hit return after you enter search text

    def handle_login_logout(self, order, user):
        if order == 'logout':
            if self.is_login == False:
                # set text to already logout
                self.state_lbl['text'] = 'Already logout'
            else:
                self.logout()
        if order == 'login':
            if self.is_login == True:
                if self.login_user == user:
                    # set text to already login
                    self.state_lbl['text'] = 'Already login'
                else:
                    self.logout()
                    self.login(user)
            else:
                self.login(user)

    def handle_function(self):
        if self.predict_function_result == 'Khóa máy':
            self.lock_desktop(self.predict_person)
        else:
            if self.first_time_browser == True:
                self.first_time_browser = False
                self.browser = webdriver.Chrome(DRIVER)
            if self.check_close_browser():
                self.browser = webdriver.Chrome(DRIVER)
                self.is_login = False
            if self.is_celeb == True:
                self.search_web(self.predict_person)
            else:
                if self.predict_function_result == 'Đăng nhập':
                    self.handle_login_logout('login', self.predict_person)
                if self.predict_function_result == 'Đăng xuất':
                    self.handle_login_logout('logout', self.predict_person)
                if self.predict_function_result == 'Tìm kiếm':
                    self.search_web(self.predict_person)

    def change_btn_state(self, s, *args):
        for btn in args:
            btn['state'] = s

    def select_file(self, *args):
        self.predict_result['text'] = "Predict speaker"
        self.predict_function_text.config(text='Action: ')
        self.state_lbl.config(text='Waiting for action')
        self.change_btn_state(tk.DISABLED, self.action_btn, self.play_btn, self.predict_btn, self.detect_action_chkbox,
                              self.execute_btn)
        fname = filedialog.askopenfilename(filetypes=[('Pre-record file (*.wav)', '*.wav')])
        self.current_file = fname
        if (fname):
            self.pre_rec_filename['text'] = self.current_file.split('/')[-1]
            print(self.current_file)
        self.change_btn_state(tk.NORMAL, self.action_btn, self.play_btn, self.predict_btn, self.detect_action_chkbox,
                              self.execute_btn)

    def add_person(self):
        # Not implemented
        pass

    def handle_celeb(self):
        if self.predict_person not in self.account:
            self.is_celeb = True
            self.state_lbl.config(text='Celeb! Only search action available')

    def predict(self):
        audio_full_path = self.current_file
        O = self.get_mfcc(audio_full_path)
        log_likelihood = np.zeros(len(self.models))

        for i in range(len(self.models)):
            gmm = self.models[i]  # checking with each model one by one
            scores = np.array(gmm.score(O, [len(O)]))
            log_likelihood[i] = scores.sum()

        winner = np.argmax(log_likelihood)
        pre = self.speakers[winner]
        self.predict_person = pre
        self.handle_celeb()
        print(pre)
        self.predict_result['text'] = "Speaker detected: " + pre
        if not self.detect_action_chk.get():
            return  # don't detect action
        O2 = self.get_mfcc_predict(audio_full_path)
        score = {cname: model.score(O2, [len(O)]) for cname, model in self.model_function.items()}
        action = max(score, key=score.get)
        self.predict_function_result = action
        print('action detected')
        # self.state_lbl['text'] = 'Action detected: {:s}!'.format(action)
        self.predict_function_text.config(text='Action detected: ' + action)

    def get_mfcc_predict(self, file_path):
        y, sr = librosa.load(file_path)  # read .wav file
        hop_length = math.floor(sr * 0.010)  # 10ms hop
        win_length = math.floor(sr * 0.025)  # 25ms frame
        # mfcc is 12 x T matrix
        mfcc = librosa.feature.mfcc(
            y, sr, n_mfcc=12, n_fft=1024,
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

    def get_mfcc(self, file_path):
        y, sr = librosa.load(file_path)  # read .wav file
        hop_length = math.floor(sr * 0.010)  # 10ms hop
        win_length = math.floor(sr * 0.025)  # 25ms frame
        # mfcc is 20 x T matrix
        mfcc = librosa.feature.mfcc(
            y, sr, n_mfcc=20, n_fft=1024,
            hop_length=hop_length, win_length=win_length)
        # substract mean from mfcc --> normalize mfcc
        mfcc = mfcc - np.mean(mfcc, axis=1).reshape((-1, 1))
        # delta feature 1st order and 2nd order
        delta1 = librosa.feature.delta(mfcc, order=1)
        delta2 = librosa.feature.delta(mfcc, order=2)
        # X is 60 x T
        X = np.concatenate([mfcc, delta1, delta2], axis=0)  # O^r
        # return T x 60 (transpose of X)
        return X.T  # hmmlearn use T x N matrix

    def play_audio(self):
        self.play = 1
        audio_full_path = self.current_file
        file_exists = os.path.exists(audio_full_path) and os.path.isfile(audio_full_path)
        self.state_lbl['text'] = 'Playing {:s} ...'.format(self.current_file) if (
            file_exists) else 'File {:s} not found!'.format(self.current_file)

        if (not file_exists): return

        self.change_btn_state(tk.DISABLED, self.pre_rec_btn, self.action_btn, self.predict_btn,
                              self.detect_action_chkbox, self.execute_btn)
        self.play_btn.configure(text='Stop', command=self.stop_audio)
        wf = wave.open(audio_full_path, 'rb')
        stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()), channels=wf.getnchannels(),
                             rate=wf.getframerate(), output=True)
        data = wf.readframes(self.CHUNK)

        while self.play == 1 and len(data) > 0:
            stream.write(data)
            data = wf.readframes(self.CHUNK)
            self.main.update()

        stream.stop_stream()
        stream.close()

        self.change_btn_state(tk.NORMAL, self.pre_rec_btn, self.action_btn, self.predict_btn, self.detect_action_chkbox,
                              self.execute_btn)
        self.play_btn.configure(text='Play', command=self.play_audio)
        self.state_lbl['text'] = 'Waiting for action ...'

    def stop_audio(self):
        self.play = 0

    def start_record(self):
        self.predict_result['text'] = "Predict speaker"
        self.predict_function_text.config(text='Action: ')
        self.pre_rec_filename.config(text='No file selected')
        self.st = 1
        self.frames = []
        self.change_btn_state(tk.DISABLED, self.pre_rec_btn, self.play_btn, self.predict_btn, self.detect_action_chkbox)
        self.action_btn.configure(text='Stop Recording', command=self.stop_record)
        output_target = os.path.join(DATA_PATH, CACHE_FILE)
        self.state_lbl['text'] = 'Recording to {:s} ...'.format(output_target)
        stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True,
                             frames_per_buffer=self.CHUNK)

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

        self.current_file = output_target
        self.action_btn.configure(text='Start Record', command=self.start_record, state=tk.NORMAL)
        self.state_lbl['text'] = 'Recorded to {:s}'.format(output_target)
        self.change_btn_state(tk.NORMAL, self.pre_rec_btn, self.play_btn, self.predict_btn, self.detect_action_chkbox)

    def stop_record(self):
        self.st = 0

    def keypress(self, event):
        """Recieve a keypress and move the ball by a specified amount"""
        print(event.char)
        if event.char == 'p':
            self.play_audio()

        if event.char == 'r':
            print(True)
            self.start_record()

        if event.char == 's':
            self.stop_record()

        if event.char == "f":
            self.predict()


# Create an object of the ProgramGUI class to begin the program.
if __name__ == '__main__':
    guiAudio = VoiceDetector()
