pip install virtualenv 

virtualenv venv 

source ./venv/Scripts/activate 

pip install -r requirements.txt 

python manage.py migrate

python manage.py shell
from face_recognition.py import create_dataset
">>>" create_dataset(1)

