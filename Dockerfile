FROM python:3.10-slim

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    unzip \
    curl \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    curl -fsSL https://deno.land/install.sh | sh

ENV DENO_INSTALL="/root/.deno"
ENV PATH="${DENO_INSTALL}/bin:${PATH}"

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["python", "main.py"]
