FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ctfuser

WORKDIR /app

# Create the vulnerable web app
COPY app.py /app/app.py
COPY setup_db.py /app/setup_db.py

RUN pip install --no-cache-dir flask

# Setup the database with the flag
RUN python /app/setup_db.py

RUN chown -R ctfuser:ctfuser /app

USER ctfuser

EXPOSE 80

CMD ["python", "/app/app.py"]
