FROM debian:latest
WORKDIR /var/festivus

COPY requirements.txt /tmp/requirements.txt
COPY festivus.py /var/festivus/festivus.py

RUN ["apt-get", "update"]
RUN ["apt-get", "install","-y", "python3", "python3-pip"]
RUN ["pip3", "install", "-r", "/tmp/requirements.txt","--break-system-packages"]
RUN ["rm", "/tmp/requirements.txt"]
RUN ["chmod", "+x", "/var/festivus/festivus.py"]
CMD ["python3", "/var/festivus/festivus.py"]