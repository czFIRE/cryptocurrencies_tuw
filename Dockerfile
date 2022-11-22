FROM python:3.10.8-bullseye
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential
COPY ./requirements.txt ./
RUN pip install -r /app/requirements.txt
COPY . .
EXPOSE 18018
CMD [ "python", "node.py" ]