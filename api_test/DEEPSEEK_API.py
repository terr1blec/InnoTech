import json
from pathlib import Path
from openai import OpenAI
import os

class DualAPISimulator:
    def __init__(self):
        # 初始化两个独立的API客户端
        self.main_client = OpenAI( base_url="https://api.deepseek.com")
        self.mood_client = OpenAI(base_url="https://api.deepseek.com")
        
        # 从本地加载prompt
        self.main_prompt = Path("F:\Agent\InnoTech\\api_test\mainprompt.txt").read_text(encoding='utf-8')
        self.mood_prompt = Path("F:\Agent\InnoTech\\api_test\moodprompt.txt").read_text(encoding='utf-8')
        
        # 初始化状态
        self.conversation = [{"role": "system", "content": self.main_prompt}]
        self.mood_score = 50

    def run(self):
        print(f"初始心情值: {self.mood_score}")
        
        while True:
            # 获取用户输入
            user_input = input("\n警方指令: ").strip()
            if user_input.lower() == "quit":
                break
            
            # 1. 主API生成回复
            self.conversation.append({"role": "user", "content": user_input})
            main_response = self.main_client.chat.completions.create(
                model="deepseek-chat",
                messages=self.conversation,
                response_format={"type": "json_object"}
            )
            doctor_reply = json.loads(main_response.choices[0].message.content)
            self.conversation.append({"role": "assistant", "content": main_response.choices[0].message.content})
            
            print(f"\n[医生行动] {json.dumps(doctor_reply, indent=2, ensure_ascii=False)}")
            
            # 2. 心情API评分
            mood_input = {
                "user_input": user_input,
                "llm_response": doctor_reply["speak"],
                "current_mood": self.mood_score
            }
            
            # 确保心情prompt明确要求score_change字段
            mood_prompt_with_format = (
                self.mood_prompt + 
                "\n请务必包含'score_change'字段在你的JSON响应中。"
            )
            
            mood_response = self.mood_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": mood_prompt_with_format},
                    {"role": "user", "content": json.dumps(mood_input)}
                ],
                response_format={"type": "json_object"}
            )
            
            try:
                mood_result = json.loads(mood_response.choices[0].message.content)
                if "score_change" not in mood_result:
                    raise ValueError("心情API响应缺少score_change字段")
                
                self.mood_score += mood_result["score_change"]
                print(f"\n[心情系统] 变化: {mood_result['score_change']:+} (原因: {mood_result.get('reason', '无说明')})")
                print(f"当前心情值: {self.mood_score}")
                
            except (KeyError, json.JSONDecodeError) as e:
                print(f"\n[错误] 心情评分失败: {e}")
                print("使用默认变化值: -1")
                self.mood_score -= 1  # 默认变化

if __name__ == "__main__":
    simulator = DualAPISimulator()
    simulator.run()