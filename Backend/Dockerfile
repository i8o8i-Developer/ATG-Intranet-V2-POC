FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install System Dependencies For Python Packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        pkg-config \
        libcairo2-dev \
        libgirepository1.0-dev \
        libxml2-dev \
        libxslt1-dev \
        libjpeg-dev \
        libpng-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libtiff-dev \
        libwebp-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY Backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY Backend /app/Backend

EXPOSE 8000

CMD ["python", "Backend/manage.py", "runserver", "0.0.0.0:8000"]