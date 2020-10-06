FROM python:3.7
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install -U pip
RUN pip install -r /requirements.txt
COPY src /app
WORKDIR /app
CMD ["/usr/local/bin/python", "run_bridge.py"]