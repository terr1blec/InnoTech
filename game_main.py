import os
import json
import tempfile
import time
from game_prompt.siliconflow_api import GameAgent
from game_prompt.game_prompts import (
    system_prompt_init,
    system_prompt_env_update1,
    system_prompt_env_update2,
)
import dotenv
from playsound import playsound
from text2voice.generate_voice import generate_voice


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

    # 初始化游戏代理
    agent = GameAgent(api_key=api_key)

    # 设置系统提示
    agent.initialize_game(system_prompt_init)

    # 更新初始环境信息
    agent.update_environment(system_prompt_env_update1)

    print("游戏已初始化。输入'退出'结束游戏，输入'保存'保存当前游戏状态。")
    print("=" * 50)
    print(f"当前心情状态: {agent.mood}")

    # 创建临时目录用于存储音频文件
    
    temp_dir = 'temp'
    audio_file = os.path.join(temp_dir, "doctor_speech.mp3")

    # 主游戏循环
    while True:
        # 获取用户输入
        old_mood = agent.mood
        user_input = input("你: ")

        # 检查特殊命令
        if user_input.lower() == "退出":
            print("游戏结束。")
            break
        elif user_input.lower() == "保存":
            agent.save_messages("game_save.json")
            print("游戏状态已保存到 game_save.json")
            continue

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

    # 清理临时文件
    try:
        os.remove(audio_file)
        os.rmdir(temp_dir)
    except:
        pass


if __name__ == "__main__":
    main()
