FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 2000

CMD ["python", "key_generator.py"]

CMD ["python", "app.py"]
