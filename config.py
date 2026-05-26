import os
from dotenv import load_dotenv

# Cargar variables de entorno
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Clave secreta para sesiones
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-sistema-academico-2026'
    
    # Configuración de la base de datos PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:admin123@localhost:5432/sistema_academico'
    
    # No rastrear modificaciones (mejor rendimiento)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de subida de archivos
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora de inactividad