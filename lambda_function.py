from app.main import app
from mangum import Mangum

# Launch the FastApi app with Mangum (for Lambda)
handler = Mangum(app)
