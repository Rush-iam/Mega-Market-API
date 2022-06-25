FROM python:3-slim
WORKDIR /project

COPY ./project ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./deploy/project/docker-entrypoint.sh ./
RUN chmod +x ./docker-entrypoint.sh
ENTRYPOINT [ "./docker-entrypoint.sh" ]

CMD [ "python", "./main.py" ]
EXPOSE 80