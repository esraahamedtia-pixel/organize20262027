# استخدم Python 3.10
FROM python:3.10-slim

# اضبطي مجلد العمل
WORKDIR /app

# تثبيت أدوات البناء الضرورية
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# تشغيل البوت مباشرة
CMD ["python", "organize.py"]
