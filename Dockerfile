ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim
ARG PLAYWRIGHT_VERSION=1.49.1

# Install Xvfb and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev python3-dev build-essential xvfb xauth

# Install Playwright and dependencies
ENV PLAYWRIGHT_BROWSERS_PATH="/api-uni/ms-playwright"

RUN pip install --no-cache-dir playwright==${PLAYWRIGHT_VERSION} && \
    mkdir -p /api-uni/ms-playwright && \
    playwright install chromium --with-deps

# Application part; install requirements
COPY requirements.txt /tmp/requirements.txt
COPY requirements_aws.txt /tmp/requirements_aws.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt -r /tmp/requirements_aws.txt

COPY lambda_function.py /api-uni/lambda_function.py
COPY app /api-uni/app

# Also copying Amazon RDS cert bundle for eu-west-3 region
# Only used by ECS
COPY db/rds/eu-west-3-bundle.pem /etc/ssl/certs

WORKDIR /api-uni

# Application is exposed to 8000 port but it can be overidden
EXPOSE 8000
ENV APP_PORT=8000

CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && fastapi run ./app/main.py --host 0.0.0.0 --port $APP_PORT"]
