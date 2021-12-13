FROM python:3.9

WORKDIR /app

ENV PATH="/root/.local/bin:$PATH"
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 libxcb-xinerama0 git -y
RUN git clone --recurse-submodules https://github.com/mikel-brostrom/Yolov5_DeepSort_Pytorch.git
COPY ./go.sh /app/Yolov5_DeepSort_Pytorch/

WORKDIR /app/Yolov5_DeepSort_Pytorch
RUN python -m pip install --upgrade pip
RUN pip3 install --user wheel
RUN pip3 install --user pymavlink
RUN pip3 install --user easydict
RUN pip3 install -r ./requirements.txt --user

ENV QT_DEBUG_PLUGINS=1 

CMD ["bash", "/app/Yolov5_DeepSort_Pytorch/go.sh"]

