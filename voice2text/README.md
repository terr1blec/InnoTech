# 语音识别应用

这是一个使用阿里云SenseVoice语音识别服务的语音识别应用。它可以录制音频并将其转换为文本。

## 功能特点

- 高质量音频录制
- 音频降噪处理
- 音量自动调整
- 使用阿里云SenseVoice进行语音识别
- 支持持续监听模式
- 可保存录音文件
- 支持阿里云OSS文件上传

## 安装

1. 克隆仓库
2. 安装依赖项：

```bash
pip install -r requirements.txt
```

3. 创建`.env`文件并添加阿里云API密钥和OSS配置：

```
DASHSCOPE_API_KEY=your_api_key_here
OSS_ACCESS_KEY_ID=your_oss_access_key_id
OSS_ACCESS_KEY_SECRET=your_oss_access_key_secret
OSS_ENDPOINT=your_oss_endpoint
OSS_BUCKET_NAME=your_oss_bucket_name
```

## 使用方法

运行主程序：

```bash
python audio_recorder.py
```

程序将开始录制音频并进行语音识别。按Ctrl+C停止程序。

## 配置选项

在`audio_recorder.py`文件中，您可以调整以下参数：

- `RECORD_SECONDS`：每次录制的秒数
- `NOISE_REDUCTION`：是否启用降噪
- `VOLUME_GAIN`：音量增益倍数
- `VOLUME_NORMALIZE`：是否进行音量归一化
- `SAVE_AUDIO`：是否保存音频文件
- `SAVE_DIR`：保存目录
- `SAVE_FORMAT`：保存格式

## 注意事项

- 确保您的麦克风正常工作
- 阿里云SenseVoice API需要有效的API密钥
- 录音文件将保存在`recordings`目录中（如果启用了保存功能）
- 如果未配置OSS信息，程序将尝试使用本地文件路径，这可能会导致识别失败 