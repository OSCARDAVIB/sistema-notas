from app import db
from datetime import datetime

class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    
    id = db.Column(db.Integer, primary_key=True)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id'), nullable=False)
    
    # Datos personales
    tipo_documento = db.Column(db.String(20), default='TI')  # TI, CC, RC, etc.
    numero_documento = db.Column(db.String(20), nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date)
    genero = db.Column(db.String(10))  # M, F, Otro
    direccion = db.Column(db.String(300))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Datos académicos
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=False)
    ano_lectivo = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), default='activo')  # activo, retirado, graduado
    
    # Datos del acudiente
    acudiente_nombre = db.Column(db.String(200))
    acudiente_documento = db.Column(db.String(20))
    acudiente_telefono = db.Column(db.String(20))
    acudiente_email = db.Column(db.String(120))
    
    # Control
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    institucion = db.relationship('Institucion', back_populates='estudiantes')
    grupo = db.relationship('Grupo', back_populates='estudiantes')
    notas = db.relationship('Nota', back_populates='estudiante', lazy='dynamic')
    
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    def __repr__(self):
        return f'<Estudiante {self.nombre_completo()}>'