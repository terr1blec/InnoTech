import time
import queue
import sounddevice as sd
import numpy as np
from aip import AipSpeech
import sys
 
# 百度云配置信息
APP_ID = '6743375'  # 替换为实际的 APP ID
API_KEY = '47WnxRpPkJr739TFVbBzplXj'  # 替换为实际的 API KEY
SECRET_KEY = 'O47O7phCennMUifH2sVQkyI3mi1pMCaJ'  # 替换为实际的 SECRET KEY
 
client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
 
# Queue to hold the recorded audio data
audio_queue = queue.Queue()
speaker_queue = queue.Queue()
 
# Callback function to capture audio data from microphone
def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(indata.copy())
 
# Callback function to capture audio data from speaker
def speaker_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    speaker_queue.put(indata.copy())
# [2]实现实时语音识别类
class RealTimeSpeechRecognizer:
    def __init__(self, client, name):
        self.client = client
        self.name = name
 
    def send_audio(self, audio_data):
        result = self.client.asr(audio_data, 'pcm', 16000, {
            'dev_pid': 1537,
        })
        if result.get('err_no') == 0:
            print(f"{self.name} 识别结果: {result['result']}")
        else:
            print(f"{self.name} 错误: {result['err_msg']}")
 
# 调用百度的语音转文字的接口
def recognize_speech(audio_data, recognizer):
    audio_data = np.concatenate(audio_data)
    recognizer.send_audio(audio_data.tobytes())
# [3]开始音频流并处理音频数据
def start_audio_stream(mic_recognizer, speaker_recognizer, speaker_device_index):
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=16000, dtype='int16') as mic_stream, \
            sd.InputStream(callback=speaker_callback, channels=2, samplerate=16000, dtype='int16', device=speaker_device_index) as spk_stream:
        print("Recording audio... Press Ctrl+C to stop.")
        mic_audio_buffer = []
        speaker_audio_buffer = []
        try:
            while True:
                while not audio_queue.empty():
                    mic_audio_buffer.append(audio_queue.get())
                while not speaker_queue.empty():
                    speaker_audio_buffer.append(speaker_queue.get())
 
                if len(mic_audio_buffer) >= 10:
                    recognize_speech(mic_audio_buffer, mic_recognizer)
                    mic_audio_buffer = []  # Clear buffer after sending
 
                if len(speaker_audio_buffer) >= 10:
                    recognize_speech(speaker_audio_buffer, speaker_recognizer)
                    speaker_audio_buffer = []  # Clear buffer after sending
 
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping audio recording.")
# [4]主程序入口
if __name__ == "__main__":
    speaker_device_index = 8  # 使用 pulse 设备（索引 8）来捕获扬声器输出
 
    mic_recognizer = RealTimeSpeechRecognizer(client, "麦克风接收：")
    speaker_recognizer = RealTimeSpeechRecognizer(client, "扬声器接收：")
 
    start_audio_stream(mic_recognizer, speaker_recognizer, speaker_device_index)
