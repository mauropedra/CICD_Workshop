FROM public.ecr.aws/docker/library/python:3.7-slim-buster AS development

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_ROOT_USER_ACTION=ignore
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=1

COPY . /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]
