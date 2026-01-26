FROM python:3.9-slim

WORKDIR /app

# copy the current directory contents into the container at /app
COPY . /app

# install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# run server.py when the container launches
CMD ["python", "-u", "server.py"]

