from app import db
from datetime import datetime

class Institucion(db.Model):
    __tablename__ = 'instituciones'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Datos básicos
    nombre = db.Column(db.String(200), nullable=False)
    codigo_dane = db.Column(db.String(20), unique=True)
    nit = db.Column(db.String(20), unique=True)
    direccion = db.Column(db.String(300))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(120))
    pagina_web = db.Column(db.String(200))
    
    # Configuración visual
    logo_url = db.Column(db.String(500))
    escudo_colombia_url = db.Column(db.String(500))
    resolucion_numero = db.Column(db.String(50))  # Ej: "12345"
    resolucion_fecha = db.Column(db.String(50))
    fuente_tipografica = db.Column(db.String(50), default='Arial')
    tamano_encabezado = db.Column(db.Integer, default=14)
    color_primario = db.Column(db.String(7), default='#003366')  # Hex color
    
    # Estado
    activa = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_suspension = db.Column(db.DateTime)
    
    # Configuración académica
    ano_lectivo_actual = db.Column(db.Integer)
    periodo_actual = db.Column(db.Integer)
    
    # Relaciones
    usuarios = db.relationship('Usuario', back_populates='institucion')
    periodos = db.relationship('PeriodoAcademico', back_populates='institucion', lazy='dynamic')
    cursos = db.relationship('Curso', back_populates='institucion', lazy='dynamic')
    asignaturas = db.relationship('Asignatura', back_populates='institucion', lazy='dynamic')
    estudiantes = db.relationship('Estudiante', back_populates='institucion', lazy='dynamic')
    configuracion = db.relationship('ConfiguracionInstitucion', back_populates='institucion', uselist=False)
    firmas = db.relationship('FirmaDigital', back_populates='institucion', lazy='dynamic')
    
    def __repr__(self):
        return f'<Institucion {self.nombre}>'