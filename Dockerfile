FROM nvidia/cuda:11.2.2-devel-ubuntu20.04

RUN apt-get update && apt-get install -y \
                                python3.8 \
                                python3-pip

WORKDIR /dnp
COPY requirements.txt /dnp/

RUN pip install torch torchvision torchaudio

RUN pip install -r requirements.txt

RUN DEBIAN_FRONTEND=noninteractive  apt-get install -y ffmpeg libsm6 libxext6

# RUN DEBIAN_FRONTEND=noninteractive apt-get install -y  ninja-build libglib2.0-0 libsm6 libxrender-dev libxext6 libgl1-mesa-glx \
#                                 && apt-get clean \
#                                 && rm -rf /var/lib/apt/lists/*

# RUN pip install -U openmim

RUN pip install mmengine

COPY . /dnp/