FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /c2

COPY requirements.txt .
COPY skeletor.py .
COPY .env .
COPY ./files /c2/files

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 80
#CMD ["python3", "skeletor.py"] Simple Flask app, make sure to uncomment main
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "3", "--threads", "4", "--access-logfile", "/c2/logs/access.log", "--error-logfile", "/c2/logs/error.log", "skeletor:app"]