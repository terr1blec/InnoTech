import pyaudio
import wave
import numpy as np
import threading
import queue
import time
import os

class AudioRecorder:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 2
        self.RATE = 16000
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.p = pyaudio.PyAudio()
        
    def start_recording(self):
        """开始录音"""
        self.is_recording = True
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        def record():
            while self.is_recording:
                try:
                    data = self.stream.read(self.CHUNK)
                    self.audio_queue.put(data)
                except Exception as e:
                    print(f"录音错误: {e}")
                    break
                    
        self.record_thread = threading.Thread(target=record)
        self.record_thread.start()
        
    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        self.record_thread.join()
        
    def get_audio_data(self):
        """获取录音数据"""
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
        return b''.join(audio_data)
    
    def save_audio(self, filename):
        """保存音频数据到文件"""
        audio_data = self.get_audio_data()
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(audio_data)
        return filename

class VoiceActivityDetector:
    def __init__(self, recorder):
        self.recorder = recorder
        self.CHUNK = recorder.CHUNK
        self.RATE = recorder.RATE
        self.FORMAT = recorder.FORMAT
        self.silence_threshold = 0.01  # 静音阈值
        self.silence_duration = 0.5  # 静音持续时间（秒）
        self.speech_duration = 0.3  # 语音持续时间（秒）
        self.silence_counter = 0
        self.speech_counter = 0
        self.is_speaking = False
        self.stream = None
        
    def start_detection(self):
        """开始语音活动检测"""
        self.stream = self.recorder.p.open(
            format=self.FORMAT,
            channels=self.recorder.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        def detect():
            while True:
                try:
                    data = self.stream.read(self.CHUNK)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    volume_norm = np.linalg.norm(audio_data) / len(audio_data)
                    
                    if volume_norm > self.silence_threshold:
                        self.speech_counter += 1
                        self.silence_counter = 0
                        
                        if self.speech_counter >= int(self.speech_duration * self.RATE / self.CHUNK) and not self.is_speaking:
                            self.is_speaking = True
                            print("检测到语音，开始录音...")
                            self.recorder.start_recording()
                    else:
                        self.silence_counter += 1
                        self.speech_counter = 0
                        
                        if self.silence_counter >= int(self.silence_duration * self.RATE / this.CHUNK) and this.is_speaking:
                            this.is_speaking = False
                            print("语音结束，停止录音...")
                            this.recorder.stop_recording()
                            
                            # 保存录音并返回文件名
                            temp_file = f"temp_audio_{int(time.time())}.wav"
                            this.recorder.save_audio(temp_file)
                            return temp_file
                            
                except Exception as e:
                    print(f"检测错误: {e}")
                    break
                    
        this.detect_thread = threading.Thread(target=detect)
        this.detect_thread.start()
        
    def stop_detection(self):
        """停止语音活动检测"""
        if this.stream:
            this.stream.stop_stream()
            this.stream.close()
        this.detect_thread.join()