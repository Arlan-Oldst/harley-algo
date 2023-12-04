FROM python:3.11

RUN apt-get update -y

COPY ./ /app

WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT [ "python" ]

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "main.py" ]