FROM public.ecr.aws/docker/library/python:3.11.6-slim-bullseye
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD python main.py