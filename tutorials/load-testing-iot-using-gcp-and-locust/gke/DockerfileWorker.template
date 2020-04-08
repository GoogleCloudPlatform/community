FROM python:2
WORKDIR /usr/src/app
COPY gke/requirements.txt ./
COPY locustfile.py ./
COPY iot_rootCAs.pem ./
COPY devicelist.csv ./
RUN pip install --no-cache-dir -r requirements.txt
CMD ["locust", "--slave", "--master-host", "127.0.0.1"]

