FROM python:3.12

# Install Xvfb and dependencies
RUN apt-get update && apt-get install -y xvfb

# Install Playwright and dependencies
RUN pip install playwright==1.46.0
RUN playwright install --with-deps

ADD requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8000

ADD app app

CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && fastapi run ./app/main.py"]