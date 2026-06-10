FROM python:3.11-slim

WORKDIR /

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt \
    && opentelemetry-bootstrap -a install

COPY app.py /app.py

EXPOSE 5050

CMD ["opentelemetry-instrument", "python", "/app.py"]