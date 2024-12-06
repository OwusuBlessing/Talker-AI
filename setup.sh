#!/bin/bash

# Print commands and exit on errors
set -ex

echo "Installing PyTorch with CUDA support..."
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118

echo "Installing requirements from requirements_app.txt..."
pip install -r requirements_app.txt

echo "Installing QWen dependencies..."
pip install transformers==4.32.0 accelerate tiktoken einops scipy transformers_stream_generator==0.0.4 peft deepspeed

echo "Upgrading protobuf..."
pip install --upgrade protobuf

echo "Installing MuesTalk dependencies..."
pip install --no-cache-dir -U openmim

echo "Installing MMlab dependencies..."
mim install mmengine
mim install "mmcv>=2.0.1"
mim install "mmdet>=3.1.0"
mim install "mmpose>=1.1.0"

echo "Installing MuesTalk requirements..."
pip install -r TFG/requirements_musetalk.txt
pip install nest_asyncio ultralytics modelscope
apt-get update && apt-get install -y ffmpeg
pip install -r VITS/requirements_gptsovits.txt
pip install funasr
pip install -U rotary_embedding_torch

echo "Downloading models..."
pip install imagekitio
pip install fastapi uvicorn
sh modeld.sh
echo "Setup completed!" 