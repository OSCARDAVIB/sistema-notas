from app import db
from datetime import datetime

class PeriodoAcademico(db.Model):
    __tablename__ = 'periodos_academicos'
    
    id = db.Column(db.Integer, primary_key=True)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id'), nullable=False)
    ano_lectivo = db.Column(db.Integer, nullable=False)
    numero_periodo = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4
    nombre = db.Column(db.String(50))  # "Primer Periodo", etc.
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    porcentaje = db.Column(db.Numeric(5, 2), default=25.00)  # % del año
    activo = db.Column(db.Boolean, default=True)
    cerrado = db.Column(db.Boolean, default=False)  # Si está cerrado, no se pueden editar notas
    
    # ============================================
    # CAMPOS NUEVOS PARA CONTROL DE CIERRE DE NOTAS
    # ============================================
    cierre_forzado = db.Column(db.Boolean, default=False)  # El director lo activa manualmente
    fecha_cierre_notas = db.Column(db.Date, nullable=True)   # Fecha límite para subir notas
    
    # Relaciones
    institucion = db.relationship('Institucion', back_populates='periodos')
    notas = db.relationship('Nota', back_populates='periodo', lazy='dynamic')
    
    def __repr__(self):
        return f'<Periodo {self.ano_lectivo}-{self.numero_periodo}>'

class Curso(db.Model):
    __tablename__ = 'cursos'
    
    id = db.Column(db.Integer, primary_key=True)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id'), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)  # "Sexto", "Séptimo", etc.
    codigo = db.Column(db.String(10))  # "6", "7", etc.
    orden = db.Column(db.Integer)  # Para ordenar: 6, 7, 8, 9, 10, 11
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    institucion = db.relationship('Institucion', back_populates='cursos')
    grupos = db.relationship('Grupo', back_populates='curso', lazy='dynamic')
    
    def __repr__(self):
        return f'<Curso {self.nombre}>'

class Grupo(db.Model):
    __tablename__ = 'grupos'
    
    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)
    nombre = db.Column(db.String(20), nullable=False)
    codigo = db.Column(db.String(20))
    ano_lectivo = db.Column(db.Integer, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # ===== CAMPOS NUEVOS =====
    jornada = db.Column(db.String(20), default='MAÑANA')
    sede = db.Column(db.String(50), default='PRINCIPAL')
    director_grupo_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Relaciones
    curso = db.relationship('Curso', back_populates='grupos')
    estudiantes = db.relationship('Estudiante', back_populates='grupo', lazy='dynamic')
    carga_academica = db.relationship('CargaAcademica', back_populates='grupo', lazy='dynamic')
    director_grupo = db.relationship('Usuario', foreign_keys=[director_grupo_id])
    
    def __repr__(self):
        return f'<Grupo {self.nombre}>'

class Asignatura(db.Model):
    __tablename__ = 'asignaturas'
    
    id = db.Column(db.Integer, primary_key=True)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20))
    area = db.Column(db.String(50))  # Matemáticas, Ciencias, etc.
    intensidad_horaria = db.Column(db.Integer)  # Horas semanales
    activa = db.Column(db.Boolean, default=True)
    
    # Relaciones
    institucion = db.relationship('Institucion', back_populates='asignaturas')
    carga_academica = db.relationship('CargaAcademica', back_populates='asignatura', lazy='dynamic')
    
    def __repr__(self):
        return f'<Asignatura {self.nombre}>'