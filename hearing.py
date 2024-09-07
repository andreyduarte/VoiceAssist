import pyaudio
import wave
import threading
import time

class AudioBuffer:
    def __init__(self, buffer_duration=6):
        self.buffer_duration = buffer_duration
        self.buffer_size = int(self.buffer_duration * 44100 * 2)  # Buffer size in bytes (stereo)
        self.audio_data = bytearray(self.buffer_size)
        self.audio_data_index = 0

        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recording_thread = None
        self.is_recording = False

        # Find Stereo Mix device index
        self.dev_index = self._find_stereo_mix_device()

        if self.dev_index is not None:
            self.start_recording()
        else:
            print("Error: Stereo Mix device not found.")

    def start_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self.record_audio)
            self.recording_thread.start()

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.recording_thread.join()
        self.p.terminate()

    def record_audio(self):
        # Audio settings
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = 44100
        CHUNK = 1024

        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  input_device_index=self.dev_index,
                                  frames_per_buffer=CHUNK)

        # Buffer loop (circular buffer)
        while self.is_recording:
            data = self.stream.read(CHUNK)

            # Write data to the circular buffer
            self.audio_data = self.audio_data[int(len(data)/2):]
            self.audio_data += data
                
    def get_buffer(self):
        """
        Returns the current buffer contents.
        """
        return self.audio_data

    def _find_stereo_mix_device(self):
        """
        Finds the Stereo Mix device index.

        Returns:
            int: Device index if found, None otherwise.
        """
        main = None
        secondary = None
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if (dev['name'].lower().find('stereo mix') != -1 and dev['hostApi'] == 0):
                secondary = dev['index']
            if (dev['name'].lower().find('qcy') != -1 and dev['hostApi'] == 0):
                main = dev['index']

        if main:
            return main
        elif secondary:
            return secondary
        return None

    def __del__(self):
        self.stop_recording()
        self.p.terminate()

# Example usage:
if __name__ == "__main__":
    buffer = AudioBuffer()
    # Record for 10 seconds
    time.sleep(10)
    audio_data = buffer.get_buffer()
    buffer.stop_recording()

    # Save the audio data as a WAV file
    wf = wave.open("output.wav", 'wb')
    wf.setnchannels(2)
    wf.setsampwidth(buffer.p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(44100)
    wf.writeframes(audio_data)
    wf.close()

    print("Finished recording and saving to output.wav.")