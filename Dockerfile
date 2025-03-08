# Use Alpine-based Python image
FROM python:3.9-alpine3.13

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/py/bin:$PATH"

# Install system dependencies (jpeg-dev & zlib-dev needed for Pillow)
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    musl-dev \
    gcc \
    postgresql-dev \
    python3-dev \
    py3-pip 

RUN apk add --no-cache jpeg-dev zlib zlib-dev


# Create and activate a virtual environment
RUN python3 -m venv /py && /py/bin/pip install --upgrade pip

# Install Pillow separately first to avoid dependency issues
RUN /py/bin/pip install --no-cache-dir pillow

# Copy requirement files
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

# Install all dependencies
ARG DEV=false
RUN /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then /py/bin/pip install -r /tmp/requirements.dev.txt; fi

# Create a non-root user
RUN adduser --disabled-password --no-create-home django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol/web && \
    chmod -R 775 /vol/web

# Set the working directory and copy application files
WORKDIR /app
COPY ./app /app

# Expose the default Django port
EXPOSE 8000

# Switch to the non-root user
USER django-user
