FROM python:3
WORKDIR /server-src
RUN mkdir /server-files
RUN echo "Test file" > /server-files/hello.txt
RUN mkdir /server-files/test_folder
RUN echo "Test file 2" > /server-files/test_folder/hello2.txt
COPY ./src/server.py .
