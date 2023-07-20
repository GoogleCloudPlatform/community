FROM python:3.7-slim
WORKDIR /
COPY requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt
COPY . /
CMD ["python3", "firestore.py"]
