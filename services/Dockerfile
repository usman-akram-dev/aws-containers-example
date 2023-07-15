FROM registry.access.redhat.com/ubi9/python-39:1-108 

# Set working directory
USER root
RUN mkdir -p /usr/src/app && chown -R 1001:root /usr/src/app
USER 1001
WORKDIR /usr/src/app

# Don't buffer stdout and stderr so we see output in real time
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt --no-cache-dir  

COPY . /usr/src/app

# Run app
ENTRYPOINT ["python3", "api.py"]