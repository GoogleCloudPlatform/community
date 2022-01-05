FROM python:3.9
WORKDIR /app
ENV PATH="/root/.local/bin:$PATH"
# Install required packages
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 libxcb-xinerama0 git -y
# Clone git repo
RUN git clone --recurse-submodules https://github.com/mikel-brostrom/Yolov5_DeepSort_Pytorch.git
RUN git clone https://github.com/ZQPei/deep_sort_pytorch.git
RUN mv /app/deep_sort_pytorch /app/Yolov5_DeepSort_Pytorch/
COPY ./go.sh /app/Yolov5_DeepSort_Pytorch/
COPY ./track_container.py /app/Yolov5_DeepSort_Pytorch/
WORKDIR /app/Yolov5_DeepSort_Pytorch
# Install python packages
RUN python -m pip install --upgrade pip
RUN pip3 install --user wheel
RUN pip3 install --user pymavlink
RUN pip3 install --user easydict
RUN pip3 install -r ./requirements.txt --user
# Enable QT debug log for troubleshooting
ENV QT_DEBUG_PLUGINS=1
# Start up application
CMD ["bash", "/app/Yolov5_DeepSort_Pytorch/go.sh"]