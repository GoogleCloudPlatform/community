FROM python:3.7 
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt 
EXPOSE 4000 
ENTRYPOINT [ "python" ] 
CMD [ "main.py" ] 
