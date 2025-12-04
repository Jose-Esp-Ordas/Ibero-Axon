#Elejir una imágen base de python
FROM python:3.11-slim-bullseye

#Establecer el entorno
WORKDIR /usr/src/app   

#Establecer variables de entorno por la v de python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#Instalar dependencias del sistema
RUN apt-get update &&\
    apt-get install -y --no-install-recommends gcc

# lint
RUN pip install --upgrade pip
RUN pip install flake8==7.3.0
COPY . /usr/src/app/ 
RUN flake8 --ignore=E501,F401 --exclude=venv, .



#Instalar dependencias
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

#Copiamos el proyecto
COPY . /usr/src/app/

#Ejecutar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app"]