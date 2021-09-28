FROM python:3.9

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /app
WORKDIR /app

RUN chmod +x ./docker/wait-for-it.sh


ENTRYPOINT ["bash"]
CMD ["./docker/wait-for-it.sh", "rabbit:5672", "--", "python", "-u", "main.py", "--service", "worker"]