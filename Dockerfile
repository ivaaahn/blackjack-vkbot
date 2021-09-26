FROM python:3.9

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /app
WORKDIR /app

RUN chmod +x ./docker/app/wait-for-it.sh

#ENTRYPOINT ["python"]
#CMD ["main.py"]

ENTRYPOINT ["bash"]
CMD ["./docker/app/wait-for-it.sh", "rabbit:5672", "--", "python", "main.py"]