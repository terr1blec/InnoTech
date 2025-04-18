# DeepSeek 游戏代理

这是一个使用 DeepSeek API 的游戏代理系统，允许玩家通过命令游戏中的代理来行动。系统使用 OpenAI 接口调用 DeepSeek API，并支持历史消息功能。

## 功能特点

- 使用 OpenAI 接口调用 DeepSeek API
- 支持历史消息功能
- 可以保存和加载游戏状态
- 支持多种动作类型：移动、交互
- 心情值系统，影响代理的语言和描述风格
- 无论采取何种行动，代理都会说话，并根据心情值调整语气
- 所有提示内容统一在 `game_prompts.py` 中管理

## 安装

1. 克隆仓库：

```bash
git clone <仓库地址>
cd <仓库目录>
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 设置环境变量：

创建一个 `.env` 文件，并添加以下内容：

```
DEEPSEEK_API_KEY=你的DeepSeek API密钥
```

## 使用方法

1. 运行游戏主程序：

```bash
python game_main.py
```

2. 在游戏中，你可以：
   - 输入命令与游戏代理交互
   - 输入 "保存" 保存当前游戏状态
   - 输入 "退出" 结束游戏

## 心情值系统

游戏代理有一个心情值系统（0-10），影响代理的语言和描述风格：
- 心情值越低，代理的语言和描述会表现得更加慌乱和恐惧
- 心情值越高，代理的语言和描述会表现得更加冷静和镇定
- 当遇到危险或紧张情况时，心情值会降低
- 当找到安全的地方或获得帮助时，心情值会提高

## 项目结构

- `deepseek_api.py`: DeepSeek API 客户端和游戏代理类
- `game_main.py`: 游戏主程序
- `game_prompts.py`: 游戏提示和系统消息，所有提示内容统一在此文件中管理
- `messages.json`: 示例消息历史

## 自定义

你可以通过修改 `game_prompts.py` 文件来自定义游戏提示和系统消息。所有的提示内容，包括系统提示、心情值提示和动作提示，都统一在此文件中管理。

## 依赖

- openai
- python-dotenv
- requests

## 许可证

[MIT](LICENSE) 