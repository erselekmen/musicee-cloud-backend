# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY . /app

# Install any dependencies
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the content of the local src directory to the working directory

EXPOSE 80

# Specify the command to run on container start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
