from app import db
from datetime import datetime

class Nota(db.Model):
    __tablename__ = 'notas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relaciones
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id'), nullable=False)
    periodo_id = db.Column(db.Integer, db.ForeignKey('periodos_academicos.id'), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Notas
    nota = db.Column(db.Numeric(3, 2), nullable=False)  # Ej: 4.50
    nota_numerica = db.Column(db.Numeric(5, 2))  # Nota sobre 100 si aplica
    desempeno = db.Column(db.String(50))  # Superior, Alto, Básico, Bajo
    
    # Logros y observaciones
    logro = db.Column(db.Text)
    observacion = db.Column(db.Text)
    
    # Control de edición
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime)
    modificado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # Relaciones
    estudiante = db.relationship('Estudiante', back_populates='notas')
    periodo = db.relationship('PeriodoAcademico', back_populates='notas')
    asignatura = db.relationship('Asignatura', backref='notas')
    
    def __repr__(self):
        return f'<Nota {self.estudiante.nombres} - {self.nota}>'