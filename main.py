import uvicorn
from app.kernel import app
from config.settings import env
from config.route import setup_routes

setup_routes(app, env)

if __name__== "__main__":
    uvicorn.run(app, host="localhost", port=8000)