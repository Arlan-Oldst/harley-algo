FROM public.ecr.aws/docker/library/python:3.11.6-slim-bullseye
ENV NX_API_URL_RESOURCE=https://p90fyzcpt1.execute-api.eu-west-2.amazonaws.com/stg/resource/api/resource
ENV NX_API_URL_ACTIVITY=https://cjk61kgsrb.execute-api.eu-west-2.amazonaws.com/stg/activity/api
ENV NX_API_URL_ASSESSMENT=https://ww7cvhqrj1.execute-api.eu-west-2.amazonaws.com/stg/assessment/api/assessment
ENV SOLVER_MAX_MINUTES=10
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD python main.py