FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt
COPY 04_ml/models ./04_ml/models
COPY 05_api ./05_api
COPY 06_dashboard ./06_dashboard
EXPOSE 8000 8501
CMD ["uvicorn", "05_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
