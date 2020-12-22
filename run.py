from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


from app import create_app
app = create_app(os.environ.get('FLASK_CONFIG') or 'default')