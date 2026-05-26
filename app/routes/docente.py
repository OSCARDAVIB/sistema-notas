from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
import unicodedata
from datetime import date, datetime
from app.models import (
    Usuario, CargaAcademica, Grupo, Asignatura, 
    PeriodoAcademico, Estudiante, Nota, Curso
)

def normalizar_texto(texto):
    """Quita tildes y convierte a minusculas para ordenar correctamente"""
    if not texto:
        return ""
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.lower()

bp = Blueprint('docente', __name__, url_prefix='/docente')

# Decorador para verificar que sea docente
def docente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_docente():
            flash('No tienes permiso para acceder a esta pagina.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@bp.route('/dashboard')
@login_required
@docente_required
def dashboard():
    """Panel principal del docente"""
    carga = CargaAcademica.query.filter_by(
        docente_id=current_user.id,
        activa=True
    ).all()
    
    total_grupos = len(set(c.grupo_id for c in carga))
    total_asignaturas = len(set(c.asignatura_id for c in carga))
    
    periodos_activos = PeriodoAcademico.query.filter_by(
        institucion_id=current_user.institucion_id,
        activo=True,
        cerrado=False
    ).order_by(PeriodoAcademico.numero_periodo).all()

    periodo_id = request.args.get('periodo_id', type=int)
    periodo_seleccionado = None
    
    if periodo_id:
        periodo_seleccionado = PeriodoAcademico.query.get(periodo_id)
    elif periodos_activos:
        periodo_seleccionado = periodos_activos[0]
    
    # SOLO MOSTRAR ADVERTENCIA VISUAL, NO REDIRIGIR
    hoy = date.today()
    periodo_bloqueado = False
    mensaje_bloqueo = None
    
    if periodo_seleccionado:
        if getattr(periodo_seleccionado, 'cierre_forzado', False):
            periodo_bloqueado = True
            mensaje_bloqueo = 'El periodo esta cerrado forzosamente para subida de notas.'
        
        elif getattr(periodo_seleccionado, 'fecha_cierre_notas', None) and periodo_seleccionado.fecha_cierre_notas < hoy:
            periodo_bloqueado = True
            mensaje_bloqueo = f'La fecha limite para subir notas ({periodo_seleccionado.fecha_cierre_notas}) ha vencido.'
    
    return render_template('docente/dashboard.html',
                         carga=carga,
                         total_grupos=total_grupos,
                         total_asignaturas=total_asignaturas,
                         periodos_activos=periodos_activos,
                         periodo_seleccionado=periodo_seleccionado,
                         periodo_bloqueado=periodo_bloqueado,
                         mensaje_bloqueo=mensaje_bloqueo)

@bp.route('/carga-academica')
@login_required
@docente_required
def carga_academica():
    """Ver carga academica completa"""
    carga = CargaAcademica.query.filter_by(
        docente_id=current_user.id,
        activa=True
    ).all()
    
    return render_template('docente/carga_academica.html', carga=carga)

@bp.route('/registrar-notas/<int:grupo_id>/<int:asignatura_id>')
@login_required
@docente_required
def registrar_notas(grupo_id, asignatura_id):
    """Formulario para registrar notas"""
    grupo = Grupo.query.get_or_404(grupo_id)
    asignatura = Asignatura.query.get_or_404(asignatura_id)
    
    periodos_activos = PeriodoAcademico.query.filter_by(
        institucion_id=current_user.institucion_id,
        activo=True,
        cerrado=False
    ).order_by(PeriodoAcademico.numero_periodo).all()
    
    periodo_id = request.args.get('periodo_id', type=int)
    
    if periodo_id:
        periodo_activo = PeriodoAcademico.query.get(periodo_id)
    else:
        periodo_activo = periodos_activos[0] if periodos_activos else None
    
    # SOLO MOSTRAR ADVERTENCIA VISUAL, NO REDIRIGIR
    hoy = date.today()
    periodo_cerrado = False
    
    if periodo_activo:
        if hasattr(periodo_activo, 'cierre_forzado') and periodo_activo.cierre_forzado:
            periodo_cerrado = True
        
        elif hasattr(periodo_activo, 'fecha_cierre_notas') and periodo_activo.fecha_cierre_notas and periodo_activo.fecha_cierre_notas < hoy:
            periodo_cerrado = True
    
    estudiantes = Estudiante.query.filter_by(grupo_id=grupo_id, activo=True).all()
    estudiantes = sorted(estudiantes, key=lambda e: normalizar_texto(e.apellidos + " " + e.nombres))
    
    notas_registradas = {}
    if periodo_activo:
        for est in estudiantes:
            nota = Nota.query.filter_by(
                estudiante_id=est.id,
                asignatura_id=asignatura_id,
                periodo_id=periodo_activo.id
            ).first()
            if nota:
                notas_registradas[est.id] = nota
    
    return render_template('docente/registrar_notas.html',
                         grupo=grupo,
                         asignatura=asignatura,
                         periodo=periodo_activo,
                         periodos_activos=periodos_activos,
                         estudiantes=estudiantes,
                         notas_registradas=notas_registradas,
                         hoy=date.today(),
                         periodo_cerrado=periodo_cerrado)

@bp.route('/guardar-notas', methods=['POST'])
@login_required
@docente_required
def guardar_notas():
    """Guardar notas registradas"""
    grupo_id = request.form.get('grupo_id')
    asignatura_id = request.form.get('asignatura_id')
    periodo_id = request.form.get('periodo_id')
    
    # ============================================
    # VALIDACION ESTRICTA SOLO AL GUARDAR (POST)
    # ============================================
    periodo_activo = PeriodoAcademico.query.get(periodo_id)
    hoy = date.today()
    
    if not periodo_activo:
        flash('Periodo academico no valido.', 'danger')
        return redirect(url_for('docente.registrar_notas', 
                              grupo_id=grupo_id, 
                              asignatura_id=asignatura_id,
                              periodo_id=periodo_id))
    
    if hasattr(periodo_activo, 'cierre_forzado') and periodo_activo.cierre_forzado:
        flash('El periodo esta cerrado para subida de notas. Contacta al director.', 'danger')
        return redirect(url_for('docente.registrar_notas', 
                              grupo_id=grupo_id, 
                              asignatura_id=asignatura_id,
                              periodo_id=periodo_id))
    
    fecha_cierre = getattr(periodo_activo, 'fecha_cierre_notas', None)
    if fecha_cierre and fecha_cierre < hoy:
        flash(f'La fecha limite para subir notas ({fecha_cierre}) ha vencido. Contacta al director.', 'danger')
        return redirect(url_for('docente.registrar_notas', 
                              grupo_id=grupo_id, 
                              asignatura_id=asignatura_id,
                              periodo_id=periodo_id))
    # ============================================
    
    estudiantes = Estudiante.query.filter_by(grupo_id=grupo_id, activo=True).all()
    estudiantes = sorted(estudiantes, key=lambda e: normalizar_texto(e.apellidos + " " + e.nombres))
    
    for estudiante in estudiantes:
        nota_valor = request.form.get(f'nota_{estudiante.id}')
        logro = request.form.get(f'logro_{estudiante.id}')
        observacion = request.form.get(f'observacion_{estudiante.id}')
        
        if nota_valor:
            nota = Nota.query.filter_by(
                estudiante_id=estudiante.id,
                asignatura_id=asignatura_id,
                periodo_id=periodo_id
            ).first()
            
            if nota:
                nota.nota = float(nota_valor)
                nota.logro = logro
                nota.observacion = observacion
                nota.fecha_modificacion = datetime.utcnow()
                nota.modificado_por = current_user.id
            else:
                nueva_nota = Nota(
                    estudiante_id=estudiante.id,
                    asignatura_id=asignatura_id,
                    periodo_id=periodo_id,
                    docente_id=current_user.id,
                    nota=float(nota_valor),
                    logro=logro,
                    observacion=observacion
                )
                db.session.add(nueva_nota)
    
    db.session.commit()
    flash('Notas guardadas correctamente.', 'success')
    
    return redirect(url_for('docente.registrar_notas', 
                          grupo_id=grupo_id, 
                          asignatura_id=asignatura_id,
                          periodo_id=periodo_id))