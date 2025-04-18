import os
import dotenv
from game_prompt.deepseek_api import GameAgent
from game_prompt.game_prompts import system_prompt_init

# 加载环境变量
dotenv.load_dotenv()

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