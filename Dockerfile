# Use the official Python base image with Python 3.10
FROM ubuntu:latest

RUN apt-get update && apt-get install -y python3-pip git

# Set the working directory inside the container
WORKDIR /app

# Copy the code and data files to the container's working directory
COPY . /app

# Install the required dependencies
RUN pip install -r requirements.txt

RUN git clone https://github.com/Ipcagr1d/majestic_1_million
RUN pip install -e majestic_1_million

# Set the entry point for the container
ENTRYPOINT ["/bin/bash"]
