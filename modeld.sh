#!/bin/bash

# Prompt user to confirm the download method
echo "Downloading models from ModelScope... (Only Option Available)"
echo "正在从 ModelScope 下载模型...(仅提供此选项)"
echo "Make sure you have ModelScope installed: pip install modelscope"
echo "请确保已安装 ModelScope：pip install modelscope"

# Download models using ModelScope
python modelscope_download.py
if [ $? -ne 0 ]; then
  echo "Failed to download models from ModelScope. Please check the scripts/modelscope_download.py script or your network connection."
  echo "从 ModelScope 下载模型失败，请检查脚本 scripts/modelscope_download.py 或网络连接。"
  exit 1
fi

echo "Model download completed."
echo "模型下载完成。"

# Check and move the models
# Move all models to the current directory
if [ -d "Kedreamix/Linly-Talker/checkpoints" ]; then
  mv Kedreamix/Linly-Talker/checkpoints/* ./checkpoints
  if [ $? -ne 0 ]; then
    echo "Failed to move checkpoints."
    echo "移动 checkpoints 失败。"
    exit 1
  fi
else
  echo "Directory Kedreamix/Linly-Talker/checkpoints does not exist, cannot move checkpoints."
  echo "目录 Kedreamix/Linly-Talker/checkpoints 不存在，无法移动 checkpoints。"
  exit 1
fi

# Move GFPGAN model if it exists
if [ -d "Kedreamix/Linly-Talker/gfpgan" ]; then
  mv Kedreamix/Linly-Talker/gfpgan ./
  if [ $? -ne 0 ]; then
    echo "Failed to move gfpgan directory."
    echo "移动 gfpgan 目录失败。"
    exit 1
  fi
else
  echo "Directory Kedreamix/Linly-Talker/gfpgan does not exist, cannot move gfpgan."
  echo "目录 Kedreamix/Linly-Talker/gfpgan 不存在，无法移动 gfpgan。"
  exit 1
fi

# Move other models as necessary
models=("GPT_SoVITS" "Qwen" "MuseTalk" "Whisper" "FunASR")
for model in "${models[@]}"; do
  if [ -d "Kedreamix/Linly-Talker/$model" ]; then
    mv Kedreamix/Linly-Talker/$model ./
    if [ $? -ne 0 ]; then
      echo "Failed to move $model directory."
      echo "移动 $model 目录失败。"
      exit 1
    fi
  else
    echo "Directory Kedreamix/Linly-Talker/$model does not exist, cannot move $model model."
    echo "目录 Kedreamix/Linly-Talker/$model 不存在，无法移动 $model 模型。"
    exit 1
  fi
done

# CosyVoice model specific handling
if [ -d "checkpoints/CosyVoice_ckpt" ]; then
  mkdir -p CosyVoice/pretrained_models
  mv checkpoints/CosyVoice_ckpt/CosyVoice-ttsfrd CosyVoice/pretrained_models
  if [ $? -ne 0 ]; then
    echo "Failed to move CosyVoice-ttsfrd directory."
    echo "移动 CosyVoice-ttsfrd 目录失败。"
    exit 1
  fi
  unzip CosyVoice/pretrained_models/CosyVoice-ttsfrd/resource.zip -d CosyVoice/pretrained_models/CosyVoice-ttsfrd
  pip install CosyVoice/pretrained_models/CosyVoice-ttsfrd/ttsfrd-0.3.6-cp38-cp38-linux_x86_64.whl
  if [ $? -ne 0 ]; then
    echo "Failed to unzip resource.zip."
    echo "解压 resource.zip 失败。"
    exit 1
  fi
else
  echo "Directory Kedreamix/Linly-Talker/checkpoints/CosyVoice_ckpt does not exist, cannot move CosyVoice model."
  echo "目录 Kedreamix/Linly-Talker/checkpoints/CosyVoice_ckpt 不存在，无法移动 CosyVoice 模型。"
  exit 1
fi

echo "All models have been successfully moved and are ready."
echo "所有模型已成功移动并准备就绪。"
