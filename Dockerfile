from python:3.12

workdir /app

copy requirements.txt ./
run apt update
run pip install --no-cache-dir -r requirements.txt

copy ./ /app/

healthcheck --interval=30s --timeout=10s --start-period=5s --retries=3 \
    cmd curl --fail http://localhost:8000/ || exit 1


expose 8000

cmd ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]