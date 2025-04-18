import os
import sys

# 添加CosyVoice目录到Python路径
cosyvoice_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'CosyVoice'))
sys.path.append(cosyvoice_path) 