FROM python:3.9

WORKDIR /app

COPY . .
ENV PATH="/root/.local/bin:$PATH"
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 -y
RUN python -m pip install --upgrade pip
RUN apt-get install libxcb-xinerama0  -y
RUN pip3 install --user wheel
RUN pip3 install --user pymavlink
RUN pip3 install -r ./requirements.txt --user

ENV QT_DEBUG_PLUGINS=1 

CMD ["bash", "/app/go.sh"]


