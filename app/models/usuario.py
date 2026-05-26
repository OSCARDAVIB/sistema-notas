from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Tabla intermedia: Usuarios-Roles (muchos a muchos)
usuario_rol = db.Table('usuario_rol',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('rol_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class Rol(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    
    # Relación con usuarios
    usuarios = db.relationship('Usuario', secondary=usuario_rol, back_populates='roles')
    
    def __repr__(self):
        return f'<Rol {self.nombre}>'

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    # Relación con institución (multi-institución)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id'), nullable=True)
    
    # Relaciones
    roles = db.relationship('Rol', secondary=usuario_rol, back_populates='usuarios')
    institucion = db.relationship('Institucion', back_populates='usuarios')
    
    # Auditoría
    creado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Encripta la contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def tiene_rol(self, nombre_rol):
        """Verifica si el usuario tiene un rol específico"""
        return any(rol.nombre == nombre_rol for rol in self.roles)
    
    def es_superadmin(self):
        return self.tiene_rol('superadmin')
    
    def es_admin(self):
        return self.tiene_rol('admin')
    
    def es_docente(self):
        return self.tiene_rol('docente')
    
    def es_secretaria(self):
        return self.tiene_rol('secretaria')
    
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    def __repr__(self):
        return f'<Usuario {self.username}>'

# Función requerida por Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))