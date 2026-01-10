# This file defines how to build a docker image. Image => creates the REPRODUCABLE environment
FROM python:3.12-slim

# dont create pyc (python cache) files
ENV PYTHONDONTWRITEBYTECODE=1
# Forces python to output logs immediately
ENV PYTHONUNBUFFERED=1

# All future commands run from this (like a "cd /app")
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
# reduces image size (best practice for docker)
    && rm -rf /var/lib/apt/lists/*

# copes requirements.txt into the image (so first part: path to source, second part: location in image)
# Here done before for caching reasoms
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENTRYPOINT ["python", "main.py" ]
CMD ["normal"]
