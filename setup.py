import os
import playsound

# 使用绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
audio_file = os.path.join(current_dir, 'temp', 'doctor_speech.mp3')

# 确保temp目录存在
temp_dir = os.path.join(current_dir, 'temp')
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

# 使用os.path.normpath确保路径格式正确
audio_file = os.path.normpath(audio_file)

# 检查文件是否存在
if os.path.exists(audio_file):
    print(f"播放音频文件: {audio_file}")
    playsound.playsound(audio_file)
else:
    print(f"错误: 音频文件不存在: {audio_file}")
