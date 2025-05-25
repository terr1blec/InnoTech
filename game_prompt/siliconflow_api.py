import os
import sys

# 将项目根目录添加到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import requests
from typing import List, Dict, Any, Optional
import dotenv
from game_prompt.game_prompts import get_mood_prompt, action_prompt, system_prompt_init


class SiliconFlowAPI:
    """SiliconFlow API 客户端，使用requests库直接调用API，支持历史消息功能"""

    def __init__(self, api_key: Optional[str] = None, model: str = "Pro/deepseek-ai/DeepSeek-V3"):
        """
        初始化 SiliconFlow API 客户端

        Args:
            api_key: SiliconFlow API 密钥，如果为 None，则从环境变量 SILICONFLOW_API_KEY 获取
            model: 使用的模型名称
        """
        self.api_key = api_key or os.environ.get("SILICONFLOW_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set it as an argument or in the SILICONFLOW_API_KEY environment variable."
            )

        self.model = model
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        top_p: float = 0.7,
        top_k: int = 50,
        frequency_penalty: float = 0.5,
        n: int = 1,
        response_format: Dict[str, str] = {"type": "text"},
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        发送聊天请求到 SiliconFlow API

        Args:
            messages: 消息历史列表，格式为 [{"role": "user", "content": "..."}, ...]
            temperature: 温度参数，控制输出的随机性
            max_tokens: 最大生成的令牌数
            stream: 是否使用流式响应
            top_p: 控制采样概率的参数
            top_k: 控制采样时考虑的候选数量
            frequency_penalty: 频率惩罚参数
            n: 生成回复的数量
            response_format: 响应格式设置
            tools: 工具函数列表

        Returns:
            API 响应
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "max_tokens": max_tokens,
            "stop": None,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "frequency_penalty": frequency_penalty,
            "n": n,
            "response_format": response_format,
        }
        
        if tools:
            payload["tools"] = tools

        response = requests.post(self.base_url, json=payload, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code} - {response.text}")
            
        return response.json()

    def get_response_content(self, response: Dict[str, Any]) -> str:
        """
        从 API 响应中提取内容

        Args:
            response: API 响应

        Returns:
            响应内容
        """
        # 根据SiliconFlow API的响应格式提取内容
        if "choices" in response and len(response["choices"]) > 0:
            if "message" in response["choices"][0]:
                return response["choices"][0]["message"]["content"]
            elif "text" in response["choices"][0]:
                return response["choices"][0]["text"]
        return ""


class GameAgent:
    """游戏代理，管理与 SiliconFlow API 的交互和消息历史"""

    def __init__(self, api_key: Optional[str] = None, model: str = "Pro/deepseek-ai/DeepSeek-V3"):
        """
        初始化游戏代理

        Args:
            api_key: SiliconFlow API 密钥
            model: 使用的模型名称
        """
        self.api = SiliconFlowAPI(api_key, model)
        self.messages = []
        self.mood = "轻微紧张"  # 初始心情状态
        self.action_prompt_sent = False  # 添加标志，跟踪是否已发送action_prompt

    def initialize_game(self, system_prompt: str):
        """
        初始化游戏，设置系统提示

        Args:
            system_prompt: 系统提示内容
        """
        # 添加心情值相关的系统提示
        mood_prompt = get_mood_prompt(self.mood)
        self.messages = [{"role": "system", "content": system_prompt + mood_prompt}]

    def update_environment(self, environment_info: str):
        """
        更新环境信息

        Args:
            environment_info: 环境信息内容
        """
        self.messages.append({"role": "system", "content": environment_info})

    def update_mood(self, mood: str):
        """
        更新心情状态

        Args:
            mood: 新的心情状态，可以是"平静"、"轻微紧张"、"中度紧张"、"极度恐慌"或"惊慌失措"
        """
        self.mood = mood
        mood_update = f"你的心情状态现在是 {self.mood}。"
        self.messages.append({"role": "system", "content": mood_update})

    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入并获取代理响应

        Args:
            user_input: 用户输入内容

        Returns:
            代理响应，包含动作和说话内容
        """

        # 只在第一次发送动作提示
        if not self.action_prompt_sent:
            self.messages.append({"role": "system", "content": action_prompt})
            self.action_prompt_sent = True

        # 添加用户消息到历史
        self.messages.append({"role": "user", "content": user_input})

        # 调用 API 获取响应
        response = self.api.chat(self.messages)
        response_content = self.api.get_response_content(response)

        # 解析响应
        try:
            response_data = json.loads(response_content)
            # 添加代理响应到历史
            self.messages.append({"role": "assistant", "content": response_content})
            # 更新心情状态
            if "mood" in response_data:
                self.update_mood(response_data["mood"])
            return response_data
        except json.JSONDecodeError:
            # 如果无法解析JSON，则返回一个默认响应
            default_response = {
                "action": "none",
                "target": "none",
                "speak": "我...我不知道该怎么做...",
                "mood": self.mood,
            }
            self.messages.append(
                {"role": "assistant", "content": json.dumps(default_response)}
            )
            return default_response

    def save_messages(self, file_path: str):
        """
        保存消息历史到文件

        Args:
            file_path: 文件路径
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=4)

    def load_messages(self, file_path: str):
        """
        从文件加载消息历史

        Args:
            file_path: 文件路径
        """
        with open(file_path, "r", encoding="utf-8") as f:
            self.messages = json.load(f)


# 使用示例
if __name__ == "__main__":
    # 从 game_prompts.py 导入系统提示
    from game_prompt.game_prompts import system_prompt_init

    dotenv.load_dotenv()
    print(os.environ.get("SILICONFLOW_API_KEY"))
    # 初始化游戏代理
    agent = GameAgent()

    # 设置系统提示
    agent.initialize_game(system_prompt_init)

    # 更新环境信息
    agent.update_environment(
        '你当前所处房间为: "办公室" \n\n你当前周围的环境信息如下：\n{\n    "room": "办公室",\n    "description": "你自己的办公室，暂时是安全的",\n    "objects": [\n        {\n            "id": "Target_Cube_1", \n            "description": "一张办公桌"\n        },\n        {\n            "id": "Target_Cube_2", \n            "description": "存放有重要文件的柜子"\n        },\n        {\n            "id": "Target_Cube_3", \n            "description": "一扇窗户"\n        },\n        {\n            "id": "Target_Cube_4", \n            "description": "一扇门，通往走廊，门是关着的"\n        },\n        {\n            "id": "Target_Cube_5", \n            "description": "坏掉的电脑"\n        },\n    ],\n}\n'
    )

    # 处理用户输入
    user_input = "有人吗？"
    response = agent.process_user_input(user_input)
    print(f"用户: {user_input}")
    print(f"代理: {response}")

    # 保存消息历史
    agent.save_messages("game_messages.json")
