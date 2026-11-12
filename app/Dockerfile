FROM python:3.12-slim

# Thiết lập biến môi trường tối ưu cho Python trong Container
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cài đặt thư viện phụ thuộc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn ứng dụng & tài nguyên tĩnh TTGShop / Apple Store
COPY main.py apple_template.py checkout_api.py ./
COPY static ./static

# Trụ cột Security (Well-Architected): Không chạy ứng dụng dưới quyền root (UID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh appuser && \
    chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
