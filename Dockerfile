FROM python:3.12-slim

# dont create pyc (python cache) files
ENV PYTHONDONTWRITEBYTECODE=1
# Forces python to output logs immediately
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

#ENTRYPOINT ["python", "-m", "package.main" ]
#ENTRYPOINT ["python", "-c", "import sys; print(sys.argv)"]
ENTRYPOINT ["package"]
CMD ["normal"]
