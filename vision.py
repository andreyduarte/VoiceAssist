import threading
import time
import cv2
from PIL import Image, PngImagePlugin 
import numpy as np
import mss

class Vision:
    def __init__(self, fps=20, buffer = 5, width=1920, height=1080):
        self.width = width
        self.height = height
        self.fps = fps
        self.interval = 1/self.fps
        self.max_frames = int(self.fps * buffer)
        self.frames = []
        self.lock = threading.Lock()
        self.stopped = True
        self.thread = None

    def start(self):
        print("Starting vision")
        if self.stopped:
            self.stopped = False
            self.thread = threading.Thread(target=self.run)
            self.thread.start()

    def stop(self):
        self.stopped = True
        if self.thread:
            self.thread.join()

    def run(self):
        print("Running vision")
        with mss.mss() as sct:
            while not self.stopped:
                start_time = time.time()

                # Captura a tela
                img = np.array(sct.grab(sct.monitors[1]))
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                # Converte para PIL Image
                img = Image.fromarray(img).resize((self.width, self.height))

                # Adiciona a imagem à lista

                with self.lock:
                    self.frames.append(img)
                    if len(self.frames) > self.max_frames:
                        self.frames.pop(0)

                elapsed_time = time.time() - start_time
                sleep_time = self.interval - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def get_imgs(self):
        with self.lock:
            return self.frames.copy()  # Retorna uma cópia para evitar modificações acidentais