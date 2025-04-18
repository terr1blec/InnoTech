import os
from voice2text.audio_recorder import AudioRecorder, VoiceActivityDetector
from voice2text.sense_voice import VoiceRecognizer

class VoiceRecognitionApp:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.vad = VoiceActivityDetector(self.recorder)
        self.recognizer = VoiceRecognizer()
        
    def start(self):
        """开始实时语音识别"""
        print("开始监听，等待语音...")
        
        try:
            while True:
                self.vad.start_detection()
                temp_file = self.vad.detect_thread.join()
                
                if temp_file:
                    # 进行语音识别
                    text = self.recognizer.recognize(temp_file)
                    print(f"识别结果: {text}")
                    
                    # 删除临时文件
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        
        except KeyboardInterrupt:
            print("\n程序已退出")
        finally:
            self.vad.stop_detection()
            self.recorder.p.terminate()

def main():
    app = VoiceRecognitionApp()
    app.start()

if __name__ == "__main__":
    main() 