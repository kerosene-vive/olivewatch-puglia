import os

import ee
from dotenv import load_dotenv

load_dotenv()

ee.Authenticate()  # serve solo la prima volta, poi puoi toglierla
ee.Initialize(project=os.environ["EE_PROJECT"])
print(ee.String("Earth Engine funziona").getInfo())