import os

API_TOKEN = '7597400226:AAHMX7MHOTEoHrgTfmeFodZRFeZL__QfN8o'
ADMIN_ID = 1145275050  

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)




    