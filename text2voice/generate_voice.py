import requests
import os
import json
from typing import Optional, Dict, Any, Union, BinaryIO, Literal
import dotenv

dotenv.load_dotenv()

def generate_voice(
    text: str,
    model: Literal["FunAudioLLM/CosyVoice2-0.5B"] = "FunAudioLLM/CosyVoice2-0.5B",
    voice: Literal[
        "FunAudioLLM/CosyVoice2-0.5B:alex", 
        "FunAudioLLM/CosyVoice2-0.5B:anna", 
        "FunAudioLLM/CosyVoice2-0.5B:bella", 
        "FunAudioLLM/CosyVoice2-0.5B:benjamin", 
        "FunAudioLLM/CosyVoice2-0.5B:charles", 
        "FunAudioLLM/CosyVoice2-0.5B:claire", 
        "FunAudioLLM/CosyVoice2-0.5B:david", 
        "FunAudioLLM/CosyVoice2-0.5B:diana"
    ] = "FunAudioLLM/CosyVoice2-0.5B:alex",
    response_format: Literal["mp3", "opus", "wav", "pcm"] = "mp3",
    sample_rate: Optional[int] = None,
    stream: bool = True,
    speed: float = 1.0,
    gain: float = 0.0,
    api_key: Optional[str] = None,
    output_file: Optional[str] = None
) -> Union[str, BinaryIO]:
    """
    将文本转换为语音
    
    参数:
        text (str): 要转换为语音的文本。对于自然语言指令，请在自然语言描述前添加特殊结束标记"<|endofprompt|>"。
                   这些描述涵盖情感、语速、角色扮演和方言等方面。详细指令可在文本标记之间插入音高标记，
                   如"[laughter]"和"[breath]"。文本长度必须在1-128000字符之间。
                   示例: "Can you say it with a happy emotion? <|endofprompt|>I'm so happy, Spring Festival is coming!"
        
        model (str): 使用的模型名称。目前仅支持"FunAudioLLM/CosyVoice2-0.5B"。
        
        voice (str): 使用的语音名称。可选值包括:
                    "FunAudioLLM/CosyVoice2-0.5B:alex", "FunAudioLLM/CosyVoice2-0.5B:anna", 
                    "FunAudioLLM/CosyVoice2-0.5B:bella", "FunAudioLLM/CosyVoice2-0.5B:benjamin", 
                    "FunAudioLLM/CosyVoice2-0.5B:charles", "FunAudioLLM/CosyVoice2-0.5B:claire", 
                    "FunAudioLLM/CosyVoice2-0.5B:david", "FunAudioLLM/CosyVoice2-0.5B:diana"
        
        response_format (str): 输出格式。支持"mp3", "opus", "wav", "pcm"。
        
        sample_rate (int, optional): 控制输出采样率。不同格式的默认值和支持范围不同:
                                    - opus: 支持48000 Hz
                                    - wav, pcm: 支持8000, 16000, 24000, 32000, 44100 Hz，默认为44100 Hz
                                    - mp3: 支持32000, 44100 Hz，默认为44100 Hz
        
        stream (bool): 是否使用流式响应。默认为True。
        
        speed (float): 生成音频的速度。取值范围为0.25到4.0，1.0为默认值。
        
        gain (float): 音量增益。取值范围为-10到10，0为默认值。
        
        api_key (str, optional): API密钥，如果为None则从环境变量获取。
        
        output_file (str, optional): 输出文件路径，如果为None则返回响应内容。
        
    返回:
        如果output_file为None，返回响应内容；否则返回文件对象。
    """
    # 参数验证
    if not 1 <= len(text) <= 128000:
        raise ValueError("文本长度必须在1-128000字符之间")
    
    if not 0.25 <= speed <= 4.0:
        raise ValueError("速度必须在0.25到4.0之间")
    
    if not -10 <= gain <= 10:
        raise ValueError("音量增益必须在-10到10之间")
    
    # 根据response_format设置默认sample_rate
    if sample_rate is None:
        if response_format == "opus":
            sample_rate = 48000
        elif response_format in ["wav", "pcm"]:
            sample_rate = 44100
        elif response_format == "mp3":
            sample_rate = 44100
    
    # 验证sample_rate是否有效
    if response_format == "opus" and sample_rate != 48000:
        raise ValueError("opus格式仅支持48000 Hz采样率")
    elif response_format in ["wav", "pcm"] and sample_rate not in [8000, 16000, 24000, 32000, 44100]:
        raise ValueError("wav和pcm格式仅支持8000, 16000, 24000, 32000, 44100 Hz采样率")
    elif response_format == "mp3" and sample_rate not in [32000, 44100]:
        raise ValueError("mp3格式仅支持32000, 44100 Hz采样率")
    
    url = "https://api.siliconflow.cn/v1/audio/speech"
    
    # 如果没有提供API密钥，尝试从环境变量获取
    if api_key is None:
        api_key = os.environ.get("SILICONFLOW_API_KEY")
        if api_key is None:
            raise ValueError("API密钥未提供，请设置api_key参数或SILICONFLOW_API_KEY环境变量")
    
    payload = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": response_format,
        "sample_rate": sample_rate,
        "stream": stream,
        "speed": speed,
        "gain": gain
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    # 检查响应状态
    if response.status_code != 200:
        error_message = f"API请求失败，状态码: {response.status_code}"
        try:
            error_details = response.json()
            error_message += f", 详情: {json.dumps(error_details, ensure_ascii=False)}"
        except:
            error_message += f", 响应内容: {response.text}"
        raise Exception(error_message)
    
    # 如果指定了输出文件，将响应内容写入文件
    if output_file:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        return open(output_file, 'rb')
    
    # 否则返回响应内容
    return response.content

# 使用示例
if __name__ == "__main__":
    # 从环境变量获取API密钥
    api_key = os.environ.get("SILICONFLOW_API_KEY")
    
    if not api_key:
        print("请设置SILICONFLOW_API_KEY环境变量")
        exit(1)
    
    # 示例1: 生成语音并保存到文件
    try:
        output_file = "output.mp3"
        generate_voice(
            text="我很高兴，春节快到了！",
            api_key=api_key,
            output_file=output_file
        )
        print(f"语音已保存到 {output_file}")
    except Exception as e:
        print(f"生成语音时出错: {e}")
    
    # 示例2: 使用不同的语音和参数
    try:
        output_file = "output2.mp3"
        generate_voice(
            text="Can you say it with a happy emotion? <|endofprompt|>I'm so happy, Spring Festival is coming! [laughter] [breath]",
            voice="FunAudioLLM/CosyVoice2-0.5B:anna",
            speed=1.2,
            gain=0.5,
            api_key=api_key,
            output_file=output_file
        )
        print(f"语音已保存到 {output_file}")
    except Exception as e:
        print(f"生成语音时出错: {e}")
    
    # 示例3: 使用不同的输出格式和采样率
    try:
        output_file = "output3.wav"
        generate_voice(
            text="Can you say it with a happy emotion? <|endofprompt|>I'm so happy, Spring Festival is coming!",
            voice="FunAudioLLM/CosyVoice2-0.5B:claire",
            response_format="wav",
            sample_rate=24000,
            api_key=api_key,
            output_file=output_file
        )
        print(f"语音已保存到 {output_file}")
    except Exception as e:
        print(f"生成语音时出错: {e}")
