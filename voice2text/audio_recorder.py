import os
import signal  # for keyboard events handling (press "Ctrl+C" to terminate recording and translation)
import sys

import dashscope
import pyaudio
from dashscope.audio.asr import *

mic = None
stream = None

# Set recording parameters
sample_rate = 16000  # sampling rate (Hz)
channels = 1  # mono channel
dtype = 'int16'  # data type
format_pcm = 'pcm'  # the format of the audio data
block_size = 3200  # number of frames per buffer


def init_dashscope_api_key():
    """
        Set your DashScope API-key. More information:
        https://github.com/aliyun/alibabacloud-bailian-speech-demo/blob/master/PREREQUISITES.md
    """

    if 'DASHSCOPE_API_KEY' in os.environ:
        dashscope.api_key = os.environ[
            'DASHSCOPE_API_KEY']  # load API-key from environment variable DASHSCOPE_API_KEY
    else:
        dashscope.api_key = '<your-dashscope-api-key>'  # set API-key manually


# Real-time speech recognition callback
class Callback(RecognitionCallback):
    def __init__(self, on_sentence_end_callback=None):
        """
        初始化回调类
        :param on_sentence_end_callback: 当句子结束时调用的回调函数，接收识别文本作为参数
        """
        self.on_sentence_end_callback = on_sentence_end_callback
        super().__init__()

    def on_open(self) -> None:
        global mic
        global stream
        print('RecognitionCallback open.')
        mic = pyaudio.PyAudio()
        stream = mic.open(format=pyaudio.paInt16,
                          channels=1,
                          rate=16000,
                          input=True)

    def on_close(self) -> None:
        global mic
        global stream
        print('RecognitionCallback close.')
        stream.stop_stream()
        stream.close()
        mic.terminate()
        stream = None
        mic = None

    def on_complete(self) -> None:
        print('RecognitionCallback completed.')  # translation completed

    def on_error(self, message) -> None:
        print('RecognitionCallback task_id: ', message.request_id)
        print('RecognitionCallback error: ', message.message)
        # Stop and close the audio stream if it is running
        if 'stream' in globals() and stream.is_active():
            stream.stop_stream()
            stream.close()
        # Forcefully exit the program
        sys.exit(1)

    def on_event(self, result: RecognitionResult) -> None:
        sentence = result.get_sentence()
        if 'text' in sentence:
            print('RecognitionCallback text: ', sentence['text'])
            if RecognitionResult.is_sentence_end(sentence):
                print(
                    'RecognitionCallback sentence end, request_id:%s, usage:%s'
                    % (result.get_request_id(), result.get_usage(sentence)))
                
                # 如果设置了回调函数，则调用它
                if self.on_sentence_end_callback:
                    self.on_sentence_end_callback(sentence['text'])


def signal_handler(sig, frame):
    print('Ctrl+C pressed, stop translation ...')
    # Stop translation
    recognition.stop()
    print('Translation stopped.')
    # 修复错误：Recognition对象没有get_last_request_id方法
    # print(
    #     '[Metric] requestId: {}, first package delay ms: {}, last package delay ms: {}'
    #     .format(
    #         recognition.get_last_request_id(),
    #         recognition.get_first_package_delay(),
    #         recognition.get_last_package_delay(),
    #     ))
    # Forcefully exit the program
    sys.exit(0)


# 启动语音识别的函数
def start_voice_recognition(on_sentence_end_callback=None):
    """
    启动语音识别
    :param on_sentence_end_callback: 当句子结束时调用的回调函数，接收识别文本作为参数
    :return: recognition对象，可用于停止识别
    """
    init_dashscope_api_key()
    print('Initializing voice recognition...')

    # 创建回调对象
    callback = Callback(on_sentence_end_callback)

    # 调用识别服务
    recognition = Recognition(
        model='paraformer-realtime-v2',
        format=format_pcm,
        sample_rate=sample_rate,
        semantic_punctuation_enabled=False,
        callback=callback)

    # 启动识别
    recognition.start()

    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    print("Press 'Ctrl+C' to stop recording and translation...")
    
    # 返回recognition对象，以便外部可以控制它
    return recognition


# main function
if __name__ == '__main__':
    # 示例回调函数
    def example_callback(text):
        print(f"句子结束，识别结果: {text}")
    
    # 启动语音识别
    recognition = start_voice_recognition(example_callback)
    
    # 主循环
    while True:
        if stream:
            data = stream.read(3200, exception_on_overflow=False)
            recognition.send_audio_frame(data)
        else:
            break

    recognition.stop()