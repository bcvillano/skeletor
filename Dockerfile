FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /c2

COPY requirements.txt .
COPY skeletor.py .

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 80
CMD ["python3", "skeletor.py"]
