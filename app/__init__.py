from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

# Inicializar extensiones (sin app todavía)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configurar login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder.'
    login_manager.login_message_category = 'warning'
    
    # Importar modelos para que SQLAlchemy los reconozca
    from app.models import Usuario, Rol, Institucion, PeriodoAcademico
    from app.models import Curso, Grupo, Asignatura, Estudiante
    from app.models import Nota, ConfiguracionInstitucion, FirmaDigital, CargaAcademica
    
    # Registrar blueprints (módulos de rutas)
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.routes.superadmin import bp as superadmin_bp
    app.register_blueprint(superadmin_bp)
    
    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp)
    
    from app.routes.docente import bp as docente_bp
    app.register_blueprint(docente_bp)
    
    from app.routes.secretaria import bp as secretaria_bp
    app.register_blueprint(secretaria_bp)
    
    from app.routes.api import bp as api_bp
    app.register_blueprint(api_bp)
    
    from app.routes.reportes import bp as reportes_bp
    app.register_blueprint(reportes_bp)
    
    # Crear tablas de la base de datos si no existen
    with app.app_context():
        db.create_all()
        # Crear roles por defecto si no existen
        crear_roles_por_defecto()
    
    return app

def crear_roles_por_defecto():
    """Crea los roles del sistema si no existen"""
    from app.models import Rol
    roles = [
        ('superadmin', 'Super Administrador del sistema'),
        ('admin', 'Administrador Institucional'),
        ('docente', 'Docente'),
        ('secretaria', 'Secretaria')
    ]
    for nombre, descripcion in roles:
        if not Rol.query.filter_by(nombre=nombre).first():
            rol = Rol(nombre=nombre, descripcion=descripcion)
            db.session.add(rol)
    db.session.commit()