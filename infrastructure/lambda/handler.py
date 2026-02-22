from mangum import Mangum
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import app

handler = Mangum(app, lifespan="off")
