ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim
ARG PLAYWRIGHT_VERSION=1.49.1

# Install Xvfb and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends xvfb libpq-dev python3-dev build-essential xauth

# Install Playwright and dependencies
RUN pip install --no-cache-dir playwright==${PLAYWRIGHT_VERSION} && \
    playwright install chromium --with-deps

# Application part; install requirements
COPY requirements.txt /tmp/requirements.txt
COPY requirements_aws.txt /tmp/requirements_aws.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt -r /tmp/requirements_aws.txt

COPY lambda_function.py /api-uni/lambda_function.py
COPY app /api-uni/app

WORKDIR /api-uni

EXPOSE 8000

CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && fastapi run ./app/main.py"]
