FROM python:3.11-slim

WORKDIR /app

# Cài dependencies hệ thống
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để cache layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Chạy bot
CMD ["python", "bot.py"]