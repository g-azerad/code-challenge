import subprocess
from app.main import app
from mangum import Mangum

# Start Xvfb into the Lambda
try:
    subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1920x1080x24"])
    print("Xvfb started successfully")
except Exception as e:
    print(f"Error starting Xvfb: {e}")

# Launch the FastApi app with Mangum (for Lambda)
handler = Mangum(app)
