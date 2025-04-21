import speech_recognition as sr
from aip import AipSpeech
import dotenv
import os
import time
import threading
import wave
import pyaudio
import tempfile
from datetime import datetime
import numpy as np
from scipy import signal

dotenv.load_dotenv()
# 百度云配置信息
APP_ID = os.environ.get('APP_ID')  # 替换为实际的 APP ID
API_KEY = os.environ.get('API_KEY')  # 替换为实际的 API KEY
SECRET_KEY = os.environ.get('SECRET_KEY')  # 替换为实际的 SECRET KEY

client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

# 音频参数 - 提升音质
CHUNK = 2048  # 增大缓冲区
FORMAT = pyaudio.paInt16  # 16位音频
CHANNELS = 1  # 单声道
RATE = 44100  # 提高采样率到44.1kHz (CD音质)
RECORD_SECONDS = 5  # 每次录制5秒
NOISE_REDUCTION = True  # 是否启用降噪

# 音量增益设置
VOLUME_GAIN = 2.0  # 音量增益倍数，1.0表示不增益
VOLUME_NORMALIZE = True  # 是否进行音量归一化

# 保存设置
SAVE_AUDIO = True  # 是否保存音频文件
SAVE_DIR = "recordings"  # 保存目录
SAVE_FORMAT = "wav"  # 保存格式

# 确保保存目录存在
if SAVE_AUDIO and not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def apply_noise_reduction(audio_data):
    """应用简单的降噪处理"""
    # 将字节数据转换为numpy数组
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    # 应用高通滤波器去除低频噪声
    b, a = signal.butter(4, 100/(RATE/2), btype='highpass')
    filtered_audio = signal.filtfilt(b, a, audio_array)
    
    # 应用低通滤波器去除高频噪声
    b, a = signal.butter(4, 7000/(RATE/2), btype='lowpass')
    filtered_audio = signal.filtfilt(b, a, filtered_audio)
    
    # 将numpy数组转回字节
    return filtered_audio.astype(np.int16).tobytes()

def adjust_volume(audio_data):
    """调整音频音量"""
    # 将字节数据转换为numpy数组
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    # 音量归一化
    if VOLUME_NORMALIZE:
        # 计算当前音频的最大振幅
        max_amplitude = np.max(np.abs(audio_array))
        if max_amplitude > 0:
            # 归一化到最大振幅的80%
            target_amplitude = 0.8 * 32767  # 16位音频的最大值是32767
            scale_factor = target_amplitude / max_amplitude
            audio_array = audio_array * scale_factor
    
    # 应用音量增益
    if VOLUME_GAIN != 1.0:
        audio_array = audio_array * VOLUME_GAIN
        # 防止溢出
        audio_array = np.clip(audio_array, -32768, 32767)
    
    # 将numpy数组转回字节
    return audio_array.astype(np.int16).tobytes()

def get_text(wav_bytes):
    result = client.asr(wav_bytes, 'wav', 16000, {'dev_pid': 1537,})
    try:
        text = result['result'][0]
    except Exception as e:
        print(f"识别错误: {e}")
        text = ""
    return text

def record_audio():
    """录制音频并保存为临时文件"""
    p = pyaudio.PyAudio()
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_filename = temp_file.name
    temp_file.close()
    
    # 打开音频流 - 使用高质量设置
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=None)  # 使用默认输入设备
    
    print(f"开始录音... ({datetime.now().strftime('%H:%M:%S')})")
    
    frames = []
    
    # 录制音频
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    
    print(f"录音结束... ({datetime.now().strftime('%H:%M:%S')})")
    
    # 停止并关闭流
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # 合并所有音频数据
    audio_data = b''.join(frames)
    
    # 应用降噪处理
    if NOISE_REDUCTION:
        print("应用降噪处理...")
        audio_data = apply_noise_reduction(audio_data)
    
    # 调整音量
    if VOLUME_GAIN != 1.0 or VOLUME_NORMALIZE:
        print("调整音量...")
        audio_data = adjust_volume(audio_data)
    
    # 保存为WAV文件
    wf = wave.open(temp_filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(audio_data)
    wf.close()
    
    return temp_filename, audio_data

def save_audio_file(audio_data, timestamp=None):
    """保存音频文件到指定目录"""
    if not SAVE_AUDIO:
        return None
        
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename = f"recording_{timestamp}.{SAVE_FORMAT}"
    filepath = os.path.join(SAVE_DIR, filename)
    
    # 保存为WAV文件
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(audio_data)
    wf.close()
    
    print(f"音频已保存到: {filepath}")
    return filepath

def process_audio():
    """处理音频文件并识别文本"""
    # 录制音频
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filename, audio_data = record_audio()
    
    # 保存音频文件
    saved_filepath = None
    if SAVE_AUDIO:
        saved_filepath = save_audio_file(audio_data, timestamp)
    
    # 读取音频文件
    with open(temp_filename, 'rb') as f:
        audio_data = f.read()
    
    # 识别文本
    print("正在识别...")
    text = get_text(audio_data)
    
    # 打印结果
    if text:
        print(f"识别结果: {text}")
    else:
        print("未能识别出文本")
    
    # 删除临时文件
    try:
        os.unlink(temp_filename)
    except:
        pass
    
    return text, saved_filepath

def continuous_listening():
    """持续监听音频"""
    print("开始持续监听，按Ctrl+C停止...")
    try:
        while True:
            text, filepath = process_audio()
            # 短暂暂停，避免CPU占用过高
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n停止监听")

if __name__ == "__main__":
    # 使用线程进行持续监听
    listening_thread = threading.Thread(target=continuous_listening)
    listening_thread.daemon = True  # 设置为守护线程，主线程结束时自动结束
    listening_thread.start()
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n程序已停止")
