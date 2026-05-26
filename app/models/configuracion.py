from app import db

class ConfiguracionInstitucion(db.Model):
    __tablename__ = 'configuracion_institucion'
    
    id = db.Column(db.Integer, primary_key=True)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id'), unique=True)
    
    # Escala valorativa (MEN)
    usar_escala_men = db.Column(db.Boolean, default=True)
    
    # Rangos personalizados
    rango_superior_min = db.Column(db.Numeric(3, 2), default=4.6)
    rango_superior_max = db.Column(db.Numeric(3, 2), default=5.0)
    rango_alto_min = db.Column(db.Numeric(3, 2), default=4.0)
    rango_alto_max = db.Column(db.Numeric(3, 2), default=4.5)
    rango_basico_min = db.Column(db.Numeric(3, 2), default=3.0)
    rango_basico_max = db.Column(db.Numeric(3, 2), default=3.9)
    rango_bajo_min = db.Column(db.Numeric(3, 2), default=1.0)
    rango_bajo_max = db.Column(db.Numeric(3, 2), default=2.9)
    
    # Configuración de periodos
    numero_periodos = db.Column(db.Integer, default=4)
    nota_minima_aprobacion = db.Column(db.Numeric(3, 2), default=3.0)
    
    # Relación
    institucion = db.relationship('Institucion', back_populates='configuracion')

class FirmaDigital(db.Model):
    __tablename__ = 'firmas_digitales'
    
    id = db.Column(db.Integer, primary_key=True)
    institucion_id = db.Column(db.Integer, db.ForeignKey('instituciones.id'), nullable=False)
    
    cargo = db.Column(db.String(50), nullable=False)  # rector, coordinador, docente, secretaria
    nombre_persona = db.Column(db.String(200), nullable=False)
    titulo = db.Column(db.String(100))  # Mg., Dr., etc.
    firma_url = db.Column(db.String(500))  # Imagen de la firma
    
    # Relación
    institucion = db.relationship('Institucion', back_populates='firmas')

class CargaAcademica(db.Model):
    __tablename__ = 'carga_academica'
    
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=False)
    ano_lectivo = db.Column(db.Integer, nullable=False)
    activa = db.Column(db.Boolean, default=True)
    
    # Relaciones
    docente = db.relationship('Usuario', backref='cargas_academicas')
    asignatura = db.relationship('Asignatura', back_populates='carga_academica')
    grupo = db.relationship('Grupo', back_populates='carga_academica')