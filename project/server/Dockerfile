FROM python:3
WORKDIR /server-src
RUN mkdir /server-files
RUN echo "Test file" > /server-files/hello.txt
COPY ./src/server.py .
