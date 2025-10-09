FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/home/app

RUN mkdir -p $APP_HOME \
    && addgroup -S app \
    && adduser -S app -G app \
    && apk update \
    && apk add libpq

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY ./requirements-test.txt .
RUN pip install -r requirements-test.txt

COPY --from=ghcr.io/ufoscout/docker-compose-wait:latest /wait /wait

WORKDIR $APP_HOME

COPY /django .

RUN chown -R app:app .
USER app

CMD /wait && pytest -v -s --disable-warnings
