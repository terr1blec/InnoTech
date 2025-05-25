import os
import time
import threading
from game_prompt.siliconflow_api import GameAgent
from game_prompt.game_prompts import (
    system_prompt_init,
    system_prompt_env_update1,
    system_prompt_env_update2,
)
import dotenv
from playsound import playsound
from text2voice.generate_voice import generate_voice
from voice2text.audio_recorder import start_voice_recognition


def main():
    """游戏主程序"""
    # 加载环境变量
    dotenv.load_dotenv()

    # 检查API密钥
    api_key = os.environ.get("SILICONFLOW_API_KEY")
    if not api_key:
        print("错误: 未设置SILICONFLOW_API_KEY环境变量")
        print("请设置环境变量: export SILICONFLOW_API_KEY=你的API密钥")
        return

    # 检查DashScope API密钥
    if 'DASHSCOPE_API_KEY' not in os.environ:
        print("错误: 未设置DASHSCOPE_API_KEY环境变量")
        print("请设置环境变量: export DASHSCOPE_API_KEY=你的API密钥")
        return

    # 初始化游戏代理
    agent = GameAgent(api_key=api_key)

    # 设置系统提示
    agent.initialize_game(system_prompt_init)

    # 更新初始环境信息
    agent.update_environment(system_prompt_env_update1)

    print("游戏已初始化。按'Ctrl+C'结束游戏，输入'保存'保存当前游戏状态。")
    print("=" * 50)
    print(f"当前心情状态: {agent.mood}")

    # 创建临时目录用于存储音频文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = 'temp'
    if not os.path.exists(os.path.join(current_dir, temp_dir)):
        os.makedirs(os.path.join(current_dir, temp_dir))
    audio_file = os.path.join(current_dir, 'temp', 'doctor_speech.mp3')

    
    # 用于存储用户输入的队列
    user_input_queue = []
    user_input_lock = threading.Lock()
    
    # 用于控制语音识别的标志
    voice_recognition_active = False
    voice_recognition_lock = threading.Lock()
    
    # 用于存储语音识别对象
    recognition = None
    
    # 用于控制音频处理线程的标志
    audio_thread_running = False
    audio_thread = None
    
    # 处理用户输入的函数
    def process_user_input(text):
        """处理用户输入的语音识别结果"""
        with user_input_lock:
            user_input_queue.append(text)
            print(f"\n你: {text}")
            # 获取到用户输入后，停止语音识别
            with voice_recognition_lock:
                nonlocal voice_recognition_active
                voice_recognition_active = False
    
    # 音频处理线程函数
    def audio_processing_thread():
        """处理音频数据的线程"""
        nonlocal audio_thread_running
        print("音频处理线程已启动")
        
        # 导入必要的模块
        from voice2text.audio_recorder import stream
        
        while audio_thread_running:
            if stream and stream.is_active():
                try:
                    # 读取音频数据
                    data = stream.read(3200, exception_on_overflow=False)
                    # 发送音频数据到识别服务
                    recognition.send_audio_frame(data)
                except Exception as e:
                    print(f"音频处理错误: {e}")
                    break
            else:
                print("音频流不可用，等待...")
                time.sleep(0.1)
        
        print("音频处理线程已停止")
    
    # 主游戏循环
    try:
        print("游戏主循环已启动，等待用户输入...")
        while True:
            # 启动语音识别
            with voice_recognition_lock:
                if not voice_recognition_active:
                    print("\n请开始说话...")
                    voice_recognition_active = True
                    recognition = start_voice_recognition(process_user_input)
                    
                    # 启动音频处理线程
                    audio_thread_running = True
                    audio_thread = threading.Thread(target=audio_processing_thread)
                    audio_thread.daemon = True
                    audio_thread.start()
            
            # 等待用户输入
            user_input = None
            while not user_input:
                with user_input_lock:
                    if user_input_queue:
                        user_input = user_input_queue.pop(0)
                
                # 检查语音识别是否仍然活跃
                with voice_recognition_lock:
                    if not voice_recognition_active:
                        # 如果语音识别已停止，但没有用户输入，可能是出现了错误
                        if not user_input:
                            print("语音识别已停止，但没有获取到用户输入。请重试。")
                            break
                
                # 如果没有用户输入，继续等待
                if not user_input:
                    time.sleep(0.1)
            
            # 如果没有获取到用户输入，继续下一次循环
            if not user_input:
                continue
            
            # 停止音频处理线程
            audio_thread_running = False
            if audio_thread:
                audio_thread.join(timeout=1.0)
            
            print(f"处理用户输入: {user_input}")
            
            # 检查特殊命令
            if user_input.lower() == "退出":
                print("游戏结束。")
                break
            elif user_input.lower() == "保存":
                agent.save_messages("game_save.json")
                print("游戏状态已保存到 game_save.json")
                continue
            
            # 获取当前心情状态
            old_mood = agent.mood
            
            # 处理用户输入
            response = agent.process_user_input(user_input)
            
            # 显示代理说的话并转换为语音
            if "speak" in response:
                doctor_speech = response['speak']
                print(f"医生: {doctor_speech}")
                
                # 根据医生的心情状态选择不同的语音
                voice = "FunAudioLLM/CosyVoice2-0.5B:alex"  # 默认语音
            
                # 生成语音
                try:
                    # 添加情感标记
                    emotion_prompt = f"用非常紧张的情绪 说: <|endofprompt|>{doctor_speech}"
                    generate_voice(
                        text=emotion_prompt,
                        voice=voice,
                        api_key=api_key,
                        output_file=audio_file
                    )
                    
                    # 播放语音
                    playsound(audio_file)
                    
                    # 播放后删除文件
                    try:
                        os.remove(audio_file)
                    except Exception as e:
                        print(f"删除临时音频文件时出错: {e}")
                        
                except Exception as e:
                    print(f"生成或播放语音时出错: {e}")
            
            # 处理动作
            action = response.get("action")
            target = response.get("target")
            
            # 根据动作类型处理响应
            if action == "move":
                print(f"医生移动到了 {target}")
                # 这里可以根据实际情况更新环境信息
                if target == "Target_Cube_4":
                    agent.update_environment(system_prompt_env_update2)
            elif action == "interact":
                print(f"医生与 {target} 交互")
                # 这里可以根据实际情况更新环境信息
                if target == "Target_Cube_4":
                    print("门被锁住了，无法打开。")
            elif action == "none":
                print("医生选择不行动")
            else:
                print(f"未知动作: {action}")
            
            # 显示心情状态变化
            if "mood" in response:
                new_mood = response["mood"]
                if old_mood != new_mood:
                    print(f"医生的心情状态从 {old_mood} 变为 {new_mood}")
                else:
                    print("医生的心情状态没有变化")
            
            # 显示当前心情状态
            print(f"当前心情状态: {agent.mood}")
            print("-" * 50)
    
    except KeyboardInterrupt:
        print("\n游戏被用户中断。")
    except Exception as e:
        print(f"游戏运行时出错: {e}")
    finally:
        # 停止音频处理线程
        audio_thread_running = False
        if audio_thread:
            audio_thread.join(timeout=1.0)
        
        # 停止语音识别
        if recognition:
            print("正在停止语音识别...")
            recognition.stop()
        
        # 清理临时文件
        try:
            # 删除临时目录中的所有文件
            for file in os.listdir(temp_dir):
                try:
                    os.remove(os.path.join(temp_dir, file))
                except Exception as e:
                    print(f"删除临时文件时出错: {e}")
            
            # 删除临时目录
            os.rmdir(temp_dir)
        except Exception as e:
            print(f"清理临时文件时出错: {e}")


if __name__ == "__main__":
    main() 