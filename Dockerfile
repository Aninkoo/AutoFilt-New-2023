FROM python:3.11

RUN apt update && apt upgrade -y
RUN apt install git -y
COPY requirements.txt /requirements.txt

RUN cd /
RUN pip3 install -U pip && pip3 install -U -r requirements.txt
WORKDIR /PiroAutoFilterBot

COPY . .

EXPOSE 8080

CMD ["python3", "bot.py"]
