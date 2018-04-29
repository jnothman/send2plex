FROM python:2.7.14-slim
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
EXPOSE 5000
CMD [ "python", "app.py" ]