FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    PORT=5000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    libglib2.0-0 \
    libgl1 \
    libnss3 \
    libxss1 \
    libasound2 \
    libgbm1 \
    libgtk-3-0 \
    ca-certificates \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Install CPU-only PyTorch first to avoid pulling massive CUDA wheels in Docker
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision

# Then install remaining dependencies
RUN grep -Ev '^(torch|torchvision)([<>=!~].*)?$' requirements.txt > requirements-docker.txt \
    && pip install -r requirements-docker.txt

COPY . .

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/', timeout=3).read()" || exit 1

CMD ["python", "src/backend/pipeline/run_all_wsl.py"]
