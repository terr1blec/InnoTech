from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

class VoiceRecognizer:
    def __init__(self):
        self.model_dir = "iic/SenseVoiceSmall"
        self.model = AutoModel(
            model=self.model_dir,
            trust_remote_code=True,   
            vad_model="fsmn-vad",
            vad_kwargs={"max_single_segment_time": 30000},
            device="cuda:0",
        )
    
    def recognize(self, audio_file):
        """
        将音频文件转换为文字
        Args:
            audio_file: 音频文件路径
        Returns:
            str: 识别出的文字
        """
        res = self.model.generate(
            input=audio_file,
            cache={},
            language="auto",
            use_itn=True,
            batch_size_s=60,
            merge_vad=True,
            merge_length_s=15,
        )
        
        text = rich_transcription_postprocess(res[0]["text"])
        return text

if __name__ == "__main__":
    voice_recognizer = VoiceRecognizer()
    text = voice_recognizer.recognize("F:\Agent\InnoTech\iic\SenseVoiceSmall\example\en.mp3")
    print(text)