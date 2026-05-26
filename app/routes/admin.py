from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
from app import db
from app.models import (
    Institucion, PeriodoAcademico, Curso, Grupo, 
    Asignatura, ConfiguracionInstitucion, FirmaDigital,
    Estudiante, Usuario, Rol, CargaAcademica,
    usuario_rol
)
import os
import pandas as pd
from datetime import date, datetime
from sqlalchemy.orm import joinedload

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorador para verificar que sea admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin():
            flash('No tienes permiso para acceder a esta página.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Panel principal del Admin Institucional"""
    institucion = current_user.institucion
    
    if not institucion:
        flash('No tienes una institución asignada.', 'danger')
        return redirect(url_for('auth.login'))
    
    total_cursos = Curso.query.filter_by(institucion_id=institucion.id).count()
    total_grupos = Grupo.query.join(Curso).filter(Curso.institucion_id == institucion.id).count()
    total_asignaturas = Asignatura.query.filter_by(institucion_id=institucion.id).count()
    total_periodos = PeriodoAcademico.query.filter_by(institucion_id=institucion.id).count()
    
    total_estudiantes = Estudiante.query.filter_by(institucion_id=institucion.id).count()
    estudiantes_activos = Estudiante.query.filter_by(institucion_id=institucion.id, activo=True).count()
    estudiantes_inactivos = Estudiante.query.filter_by(institucion_id=institucion.id, activo=False).count()
    
    total_docentes = Usuario.query.filter(
        Usuario.institucion_id == institucion.id,
        Usuario.roles.any(Rol.nombre == 'docente')
    ).count()
    
    periodo_activo = PeriodoAcademico.query.filter_by(
        institucion_id=institucion.id,
        activo=True
    ).order_by(PeriodoAcademico.numero_periodo).first()
    
    return render_template('admin/dashboard.html',
                         institucion=institucion,
                         total_cursos=total_cursos,
                         total_grupos=total_grupos,
                         total_asignaturas=total_asignaturas,
                         total_periodos=total_periodos,
                         total_estudiantes=total_estudiantes,
                         estudiantes_activos=estudiantes_activos,
                         estudiantes_inactivos=estudiantes_inactivos,
                         total_docentes=total_docentes,
                         periodo_activo=periodo_activo)

# ============================================
# CONFIGURACIÓN INSTITUCIONAL
# ============================================

@bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracion():
    """Configurar datos de la institución"""
    institucion = current_user.institucion
    
    if request.method == 'POST':
        institucion.nombre = request.form.get('nombre')
        institucion.codigo_dane = request.form.get('codigo_dane')
        institucion.nit = request.form.get('nit')
        institucion.direccion = request.form.get('direccion')
        institucion.telefono = request.form.get('telefono')
        institucion.email = request.form.get('email')
        institucion.pagina_web = request.form.get('pagina_web')
        institucion.fuente_tipografica = request.form.get('fuente_tipografica', 'Arial')
        institucion.tamano_encabezado = int(request.form.get('tamano_encabezado', 14))
        institucion.color_primario = request.form.get('color_primario', '#003366')
        institucion.resolucion_numero = request.form.get('resolucion_numero')
        institucion.resolucion_fecha = request.form.get('resolucion_fecha')
        
        img_folder = os.path.join(current_app.root_path, 'static', 'img')
        if not os.path.exists(img_folder):
            os.makedirs(img_folder)
        
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo.filename:
                filename = secure_filename('logo_' + str(institucion.id) + '_' + logo.filename)
                ruta = os.path.join(img_folder, filename)
                logo.save(ruta)
                institucion.logo_url = url_for('static', filename='img/' + filename)
        
        if 'escudo_colombia' in request.files:
            escudo = request.files['escudo_colombia']
            if escudo.filename:
                filename = secure_filename('escudo_' + str(institucion.id) + '_' + escudo.filename)
                ruta = os.path.join(img_folder, filename)
                escudo.save(ruta)
                institucion.escudo_colombia_url = url_for('static', filename='img/' + filename)
        
        db.session.commit()
        flash('Configuración actualizada correctamente.', 'success')
        return redirect(url_for('admin.configuracion'))
    
    return render_template('admin/configuracion.html', institucion=institucion)

# ============================================
# PERIODOS ACADÉMICOS
# ============================================

@bp.route('/periodos')
@login_required
@admin_required
def periodos():
    """Lista de periodos académicos"""
    institucion = current_user.institucion
    periodos = PeriodoAcademico.query.filter_by(institucion_id=institucion.id).order_by(
        PeriodoAcademico.ano_lectivo.desc(),
        PeriodoAcademico.numero_periodo.asc()
    ).all()
    
    return render_template('admin/periodos.html', 
                         periodos=periodos,
                         hoy=date.today())

@bp.route('/periodos/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_periodo():
    """Crear nuevo periodo académico"""
    if request.method == 'POST':
        institucion = current_user.institucion
        
        periodo = PeriodoAcademico(
            institucion_id=institucion.id,
            ano_lectivo=int(request.form.get('ano_lectivo')),
            numero_periodo=int(request.form.get('numero_periodo')),
            nombre=request.form.get('nombre'),
            fecha_inicio=request.form.get('fecha_inicio'),
            fecha_fin=request.form.get('fecha_fin'),
            porcentaje=float(request.form.get('porcentaje', 25))
        )
        
        db.session.add(periodo)
        db.session.commit()
        
        flash('Periodo académico creado correctamente.', 'success')
        return redirect(url_for('admin.periodos'))
    
    return render_template('admin/crear_periodo.html')

@bp.route('/periodos/editar/<int:periodo_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_periodo(periodo_id):
    """Editar un periodo académico existente"""
    institucion = current_user.institucion
    
    periodo = PeriodoAcademico.query.filter_by(
        id=periodo_id,
        institucion_id=institucion.id
    ).first_or_404()
    
    if request.method == 'POST':
        periodo.nombre = request.form.get('nombre')
        periodo.ano_lectivo = int(request.form.get('ano_lectivo'))
        periodo.numero_periodo = int(request.form.get('numero_periodo'))
        periodo.fecha_inicio = request.form.get('fecha_inicio')
        periodo.fecha_fin = request.form.get('fecha_fin')
        periodo.activo = 'activo' in request.form
        periodo.cerrado = 'cerrado' in request.form
        
        fecha_cierre_notas = request.form.get('fecha_cierre_notas')
        if fecha_cierre_notas:
            periodo.fecha_cierre_notas = fecha_cierre_notas
        else:
            periodo.fecha_cierre_notas = None
        
        periodo.cierre_forzado = 'cierre_forzado' in request.form
        
        nuevo_porcentaje = float(request.form.get('porcentaje', 25))
        ano_lectivo = periodo.ano_lectivo
        
        otros_periodos = PeriodoAcademico.query.filter(
            PeriodoAcademico.institucion_id == institucion.id,
            PeriodoAcademico.ano_lectivo == ano_lectivo,
            PeriodoAcademico.id != periodo_id
        ).all()
        
        suma_otros = sum(float(p.porcentaje) for p in otros_periodos)
        suma_total = suma_otros + nuevo_porcentaje
        
        if suma_total > 100.0:
            flash(f'Error: La suma de porcentajes ({suma_total}%) excede el 100%. ' 
                  f'Otros periodos: {suma_otros}%. '
                  f'Ingresaste: {nuevo_porcentaje}%. '
                  f'Debe quedar exactamente 100%.', 'danger')
            return redirect(url_for('admin.editar_periodo', periodo_id=periodo_id))
        
        periodo.porcentaje = nuevo_porcentaje
        
        db.session.commit()
        
        periodos_actualizados = PeriodoAcademico.query.filter_by(
            institucion_id=institucion.id,
            ano_lectivo=ano_lectivo
        ).all()
        
        suma_final = sum(float(p.porcentaje) for p in periodos_actualizados)
        
        if abs(suma_final - 100.0) > 0.01:
            flash(f'Periodo actualizado, pero la suma de porcentajes es {suma_final}%. '
                  f'Debe ser exactamente 100%. Edita los otros periodos para corregir.', 'warning')
        else:
            flash(f'Periodo {periodo.nombre or periodo.numero_periodo} actualizado correctamente. '
                  f'Suma de porcentajes: {suma_final}%.', 'success')
        
        return redirect(url_for('admin.periodos'))
    
    return render_template('admin/editar_periodo.html', periodo=periodo)

@bp.route('/periodos/cerrar-notas/<int:periodo_id>')
@login_required
@admin_required
def cerrar_periodo_notas(periodo_id):
    """Cerrar periodo para que docentes no puedan subir notas"""
    institucion = current_user.institucion
    
    periodo = PeriodoAcademico.query.filter_by(
        id=periodo_id,
        institucion_id=institucion.id
    ).first_or_404()
    
    periodo.cierre_forzado = True
    periodo.fecha_autorizacion = datetime.utcnow()
    periodo.autorizado_por = current_user.id
    
    db.session.commit()
    
    flash(f'Periodo {periodo.nombre or periodo.numero_periodo} cerrado para subida de notas.', 'warning')
    return redirect(url_for('admin.periodos'))

@bp.route('/periodos/abrir-notas/<int:periodo_id>')
@login_required
@admin_required
def abrir_periodo_notas(periodo_id):
    """Abrir periodo para que docentes puedan subir notas"""
    institucion = current_user.institucion
    
    periodo = PeriodoAcademico.query.filter_by(
        id=periodo_id,
        institucion_id=institucion.id
    ).first_or_404()
    
    periodo.cierre_forzado = False
    periodo.fecha_autorizacion = datetime.utcnow()
    periodo.autorizado_por = current_user.id
    
    db.session.commit()
    
    flash(f'Periodo {periodo.nombre or periodo.numero_periodo} abierto para subida de notas.', 'success')
    return redirect(url_for('admin.periodos'))

# ============================================
# CURSOS Y GRUPOS (UNIFICADO)
# ============================================

@bp.route('/cursos')
@login_required
@admin_required
def cursos():
    """Lista de cursos con sus grupos"""
    institucion = current_user.institucion
    
    # Consultar cursos
    cursos = Curso.query.filter_by(
        institucion_id=institucion.id
    ).order_by(Curso.orden.asc()).all()
    
    # Precargar grupos con sus directores para evitar consultas adicionales
    for curso in cursos:
        # Esto carga los grupos en memoria
        grupos_lista = curso.grupos.all()
        for grupo in grupos_lista:
            # Acceder al director fuerza la carga si existe
            if grupo.director_grupo_id:
                _ = grupo.director_grupo
    
    return render_template('admin/cursos.html', cursos=cursos)

@bp.route('/cursos/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_curso():
    """Crear nuevo curso (redirige al formulario unificado)"""
    return redirect(url_for('admin.crear_curso_grupo'))

@bp.route('/grupos/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_grupo():
    """Crear nuevo grupo (redirige al formulario unificado)"""
    return redirect(url_for('admin.crear_curso_grupo'))

@bp.route('/cursos-grupos/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_curso_grupo():
    """Crear curso y grupo en un solo paso"""
    institucion = current_user.institucion
    
    docentes = Usuario.query.filter(
    Usuario.institucion_id == institucion.id
    ).all()
    
    if request.method == 'POST':
        grado = request.form.get('grado')
        literal = request.form.get('literal')
        ano_lectivo = int(request.form.get('ano_lectivo', 2026))
        jornada = request.form.get('jornada')
        sede = request.form.get('sede')
        director_grupo_id = request.form.get('director_grupo_id', type=int)
        
        # 1. CREAR O BUSCAR EL CURSO
        nombre_curso = grado
        curso = Curso.query.filter_by(
            institucion_id=institucion.id,
            nombre=nombre_curso
        ).first()
        
        if not curso:
            orden_grados = {
                'PRIMERO': 1, 'SEGUNDO': 2, 'TERCERO': 3, 'CUARTO': 4,
                'QUINTO': 5, 'SEXTO': 6, 'SEPTIMO': 7, 'OCTAVO': 8,
                'NOVENO': 9, 'DECIMO': 10, 'ONCE': 11
            }
            orden = orden_grados.get(grado, 0)
            
            curso = Curso(
                institucion_id=institucion.id,
                nombre=nombre_curso,
                codigo=str(orden),
                orden=orden
            )
            db.session.add(curso)
            db.session.flush()
        
        # 2. CREAR EL GRUPO
        nombre_grupo = f"{grado}-{literal}"
        
        grupo_existente = Grupo.query.filter_by(
            curso_id=curso.id,
            nombre=nombre_grupo,
            ano_lectivo=ano_lectivo
        ).first()
        
        if grupo_existente:
            flash(f'El grupo {nombre_grupo} ya existe para el año {ano_lectivo}.', 'warning')
            return redirect(url_for('admin.crear_curso_grupo'))
        
        grupo = Grupo(
            curso_id=curso.id,
            nombre=nombre_grupo,
            codigo=literal,
            ano_lectivo=ano_lectivo,
            jornada=jornada,
            sede=sede,
            director_grupo_id=director_grupo_id
        )
        
        db.session.add(grupo)
        db.session.commit()
        
        flash(f'Curso y grupo {nombre_grupo} creados correctamente.', 'success')
        return redirect(url_for('admin.cursos'))
    
    return render_template('admin/crear_curso_grupo.html', docentes=docentes)

# ============================================
# GRUPOS
# ============================================

@bp.route('/grupos')
@login_required
@admin_required
def grupos():
    """Lista de grupos"""
    institucion = current_user.institucion
    grupos = Grupo.query.join(Curso).filter(
        Curso.institucion_id == institucion.id
    ).order_by(Grupo.ano_lectivo.desc(), Curso.orden.asc()).all()
    
    return render_template('admin/grupos.html', grupos=grupos)

@bp.route('/cursos/editar/<int:curso_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_curso(curso_id):
    """Editar curso y sus grupos"""
    institucion = current_user.institucion
    
    curso = Curso.query.filter_by(
        id=curso_id,
        institucion_id=institucion.id
    ).first_or_404()
    
    # Obtener grupos de este curso
    grupos = curso.grupos.all()
    
    # Obtener docentes para asignar directores
    docentes = Usuario.query.join(
        usuario_rol, Usuario.id == usuario_rol.c.usuario_id
    ).join(
        Rol, usuario_rol.c.rol_id == Rol.id
    ).filter(
        Usuario.institucion_id == institucion.id,
        Rol.nombre == 'docente'
    ).order_by(
        Usuario.apellidos, Usuario.nombres
    ).all()
    
    if request.method == 'POST':
        # Editar datos del curso
        curso.nombre = request.form.get('nombre')
        curso.codigo = request.form.get('codigo')
        curso.orden = int(request.form.get('orden', 0))
        curso.activo = 'activo' in request.form
        
        # Editar datos del grupo (si hay grupos)
        grupo_id = request.form.get('grupo_id', type=int)
        if grupo_id:
            grupo = Grupo.query.filter_by(
                id=grupo_id,
                curso_id=curso.id
            ).first()
            
            if grupo:
                grupo.jornada = request.form.get('jornada', grupo.jornada)
                grupo.sede = request.form.get('sede', grupo.sede)
                grupo.director_grupo_id = request.form.get('director_grupo_id', type=int)
                grupo.ano_lectivo = int(request.form.get('ano_lectivo', grupo.ano_lectivo))
                grupo.codigo = request.form.get('codigo', grupo.codigo)
                grupo.nombre = f"{curso.nombre}-{grupo.codigo}"
        
        db.session.commit()
        flash(f'Curso y grupo actualizados correctamente.', 'success')
        return redirect(url_for('admin.cursos'))
    
    return render_template('admin/editar_curso.html', 
                         curso=curso, 
                         grupos=grupos,
                         docentes=docentes)

# ============================================
# ASIGNATURAS
# ============================================

@bp.route('/asignaturas')
@login_required
@admin_required
def asignaturas():
    """Lista de asignaturas"""
    institucion = current_user.institucion
    asignaturas = Asignatura.query.filter_by(institucion_id=institucion.id).all()
    return render_template('admin/asignaturas.html', asignaturas=asignaturas)

@bp.route('/asignaturas/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_asignatura():
    """Crear nueva asignatura"""
    if request.method == 'POST':
        institucion = current_user.institucion
        
        asignatura = Asignatura(
            institucion_id=institucion.id,
            nombre=request.form.get('nombre'),
            codigo=request.form.get('codigo'),
            area=request.form.get('area'),
            intensidad_horaria=int(request.form.get('intensidad_horaria', 0)) if request.form.get('intensidad_horaria') else None
        )
        
        db.session.add(asignatura)
        db.session.commit()
        
        flash(f'Asignatura "{asignatura.nombre}" creada correctamente.', 'success')
        return redirect(url_for('admin.asignaturas'))
    
    return render_template('admin/crear_asignatura.html')

@bp.route('/asignaturas/editar/<int:asignatura_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_asignatura(asignatura_id):
    """Editar una asignatura existente"""
    institucion = current_user.institucion
    
    asignatura = Asignatura.query.filter_by(
        id=asignatura_id,
        institucion_id=institucion.id
    ).first_or_404()
    
    if request.method == 'POST':
        asignatura.nombre = request.form.get('nombre')
        asignatura.codigo = request.form.get('codigo')
        asignatura.area = request.form.get('area')
        asignatura.intensidad_horaria = int(request.form.get('intensidad_horaria', 0)) if request.form.get('intensidad_horaria') else None
        asignatura.activa = 'activa' in request.form
        
        db.session.commit()
        
        flash(f'Asignatura "{asignatura.nombre}" actualizada correctamente.', 'success')
        return redirect(url_for('admin.asignaturas'))
    
    return render_template('admin/editar_asignatura.html', asignatura=asignatura)

# ============================================
# ESCALA VALORATIVA
# ============================================

@bp.route('/escala', methods=['GET', 'POST'])
@login_required
@admin_required
def escala_valorativa():
    """Configurar escala valorativa MEN"""
    institucion = current_user.institucion
    
    config = ConfiguracionInstitucion.query.filter_by(institucion_id=institucion.id).first()
    if not config:
        config = ConfiguracionInstitucion(institucion_id=institucion.id)
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        config.usar_escala_men = 'usar_escala_men' in request.form
        
        config.rango_superior_min = float(request.form.get('rango_superior_min', 4.6))
        config.rango_superior_max = float(request.form.get('rango_superior_max', 5.0))
        config.rango_alto_min = float(request.form.get('rango_alto_min', 4.0))
        config.rango_alto_max = float(request.form.get('rango_alto_max', 4.5))
        config.rango_basico_min = float(request.form.get('rango_basico_min', 3.0))
        config.rango_basico_max = float(request.form.get('rango_basico_max', 3.9))
        config.rango_bajo_min = float(request.form.get('rango_bajo_min', 1.0))
        config.rango_bajo_max = float(request.form.get('rango_bajo_max', 2.9))
        
        config.nota_minima_aprobacion = float(request.form.get('nota_minima_aprobacion', 3.0))
        
        db.session.commit()
        flash('Escala valorativa actualizada correctamente.', 'success')
        return redirect(url_for('admin.escala_valorativa'))
    
    return render_template('admin/escala.html', config=config)

# ============================================
# FIRMAS DIGITALES
# ============================================

@bp.route('/firmas')
@login_required
@admin_required
def firmas():
    """Lista de firmas digitales"""
    institucion = current_user.institucion
    firmas = FirmaDigital.query.filter_by(institucion_id=institucion.id).all()
    return render_template('admin/firmas.html', firmas=firmas)

@bp.route('/firmas/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_firma():
    """Crear nueva firma digital"""
    if request.method == 'POST':
        institucion = current_user.institucion
        
        firma = FirmaDigital(
            institucion_id=institucion.id,
            cargo=request.form.get('cargo'),
            nombre_persona=request.form.get('nombre_persona'),
            titulo=request.form.get('titulo')
        )
        
        db.session.add(firma)
        db.session.commit()
        
        flash(f'Firma de {firma.cargo} creada correctamente.', 'success')
        return redirect(url_for('admin.firmas'))
    
    return render_template('admin/crear_firma.html')

# ============================================
# MATRICULAR ESTUDIANTE INDIVIDUAL
# ============================================

@bp.route('/estudiantes/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_estudiante():
    """Formulario para matricular un estudiante individual"""
    institucion = current_user.institucion
    grupos = Grupo.query.join(Curso).filter(
        Curso.institucion_id == institucion.id,
        Grupo.ano_lectivo == 2026
    ).all()
    
    return render_template('admin/crear_estudiante.html', grupos=grupos)

@bp.route('/estudiantes/guardar', methods=['POST'])
@login_required
@admin_required
def guardar_estudiante():
    """Guardar estudiante matriculado individualmente"""
    institucion = current_user.institucion
    
    existe = Estudiante.query.filter_by(
        numero_documento=request.form.get('numero_documento')
    ).first()
    
    if existe:
        flash(f'Ya existe un estudiante con documento {request.form.get("numero_documento")}.', 'danger')
        return redirect(url_for('admin.crear_estudiante'))
    
    estudiante = Estudiante(
        institucion_id=institucion.id,
        tipo_documento=request.form.get('tipo_documento', 'TI'),
        numero_documento=request.form.get('numero_documento'),
        nombres=request.form.get('nombres'),
        apellidos=request.form.get('apellidos'),
        genero=request.form.get('genero') or None,
        fecha_nacimiento=request.form.get('fecha_nacimiento') or None,
        telefono=request.form.get('telefono') or None,
        direccion=request.form.get('direccion') or None,
        email=request.form.get('email') or None,
        grupo_id=int(request.form.get('grupo_id')),
        ano_lectivo=int(request.form.get('ano_lectivo', 2026)),
        acudiente_nombre=request.form.get('acudiente_nombre') or None,
        acudiente_documento=request.form.get('acudiente_documento') or None,
        acudiente_telefono=request.form.get('acudiente_telefono') or None,
        acudiente_email=request.form.get('acudiente_email') or None
    )
    
    db.session.add(estudiante)
    db.session.commit()
    
    flash(f'Estudiante {estudiante.nombre_completo()} matriculado exitosamente en {estudiante.grupo.nombre}.', 'success')
    return redirect(url_for('admin.crear_estudiante'))

# ============================================
# IMPORTAR ESTUDIANTES DESDE EXCEL
# ============================================

@bp.route('/importar-estudiantes', methods=['GET'])
@login_required
@admin_required
def importar_estudiantes():
    """Página para importar estudiantes desde Excel"""
    institucion = current_user.institucion
    grupos = Grupo.query.join(Curso).filter(Curso.institucion_id == institucion.id).all()
    
    resultado = None
    if 'resultado_importacion' in request.args:
        import json
        resultado = json.loads(request.args.get('resultado_importacion'))
    
    return render_template('admin/importar_estudiantes.html', grupos=grupos, resultado=resultado)

@bp.route('/procesar-excel', methods=['POST'])
@login_required
@admin_required
def procesar_excel():
    """Procesar archivo Excel de estudiantes con validaciones"""
    institucion = current_user.institucion
    
    if 'archivo' not in request.files:
        flash('No se seleccionó ningún archivo.', 'danger')
        return redirect(url_for('admin.importar_estudiantes'))
    
    archivo = request.files['archivo']
    
    if archivo.filename == '':
        flash('No se seleccionó ningún archivo.', 'danger')
        return redirect(url_for('admin.importar_estudiantes'))
    
    if not archivo.filename.endswith(('.xlsx', '.xls')):
        flash('El archivo debe ser Excel (.xlsx o .xls).', 'danger')
        return redirect(url_for('admin.importar_estudiantes'))
    
    try:
        df = pd.read_excel(archivo)
        
        # Verificar columnas requeridas
        columnas_requeridas = ['tipo_documento', 'numero_documento', 'nombres', 'apellidos']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            flash(f'Faltan columnas requeridas: {", ".join(columnas_faltantes)}', 'danger')
            return redirect(url_for('admin.importar_estudiantes'))
        
        creados = 0
        existentes = 0
        errores = 0
        detalles_errores = []
        
        grupo_id_default = request.form.get('grupo_id_default', type=int)
        
        for index, fila in df.iterrows():
            try:
                # Validar campos obligatorios
                tipo_doc = str(fila.get('tipo_documento', '')).strip().upper()
                num_doc = str(fila.get('numero_documento', '')).strip()
                nombres = str(fila.get('nombres', '')).strip()
                apellidos = str(fila.get('apellidos', '')).strip()
                
                if not tipo_doc:
                    errores += 1
                    detalles_errores.append(f'Fila {index + 2}: tipo_documento está vacío')
                    continue
                
                if not num_doc:
                    errores += 1
                    detalles_errores.append(f'Fila {index + 2}: numero_documento está vacío')
                    continue
                
                if not nombres:
                    errores += 1
                    detalles_errores.append(f'Fila {index + 2}: nombres está vacío')
                    continue
                
                if not apellidos:
                    errores += 1
                    detalles_errores.append(f'Fila {index + 2}: apellidos está vacío')
                    continue
                
                # Verificar si ya existe
                existe = Estudiante.query.filter_by(numero_documento=num_doc).first()
                if existe:
                    existentes += 1
                    continue
                
                # Validar grupo
                grupo_id = grupo_id_default
                if 'grupo_id' in fila and pd.notna(fila['grupo_id']):
                    try:
                        grupo_id = int(fila['grupo_id'])
                    except:
                        errores += 1
                        detalles_errores.append(f'Fila {index + 2}: grupo_id no es un número válido')
                        continue
                
                grupo_existe = Grupo.query.get(grupo_id)
                if not grupo_existe:
                    errores += 1
                    detalles_errores.append(f'Fila {index + 2}: El grupo ID {grupo_id} no existe')
                    continue
                
                # Validar fecha
                fecha_nac = None
                if 'fecha_nacimiento' in fila and pd.notna(fila['fecha_nacimiento']):
                    try:
                        fecha_nac = pd.to_datetime(fila['fecha_nacimiento']).date()
                    except:
                        errores += 1
                        detalles_errores.append(f'Fila {index + 2}: fecha_nacimiento inválida (use AAAA-MM-DD)')
                        continue
                
                # Validar año lectivo
                ano_lectivo = 2026
                if 'ano_lectivo' in fila and pd.notna(fila['ano_lectivo']):
                    try:
                        ano_lectivo = int(fila['ano_lectivo'])
                    except:
                        pass  # Usa 2026 por defecto
                
                # Validar género
                genero = None
                if 'genero' in fila and pd.notna(fila['genero']):
                    gen = str(fila['genero']).strip().upper()
                    if gen in ['M', 'F']:
                        genero = gen
                
                # Crear estudiante
                estudiante = Estudiante(
                    institucion_id=institucion.id,
                    tipo_documento=tipo_doc,
                    numero_documento=num_doc,
                    nombres=nombres,
                    apellidos=apellidos,
                    genero=genero,
                    fecha_nacimiento=fecha_nac,
                    grupo_id=grupo_id,
                    ano_lectivo=ano_lectivo
                )
                
                db.session.add(estudiante)
                creados += 1
                
            except Exception as e:
                errores += 1
                detalles_errores.append(f'Fila {index + 2}: Error inesperado - {str(e)}')
        
        db.session.commit()
        
        import json
        resultado = {
            'creados': creados,
            'existentes': existentes,
            'errores': errores,
            'detalles_errores': detalles_errores
        }
        
        flash(f'Importación completada: {creados} creados, {existentes} existentes, {errores} errores.', 'success')
        return redirect(url_for('admin.importar_estudiantes', resultado_importacion=json.dumps(resultado)))
        
    except Exception as e:
        flash(f'Error al procesar el archivo: {str(e)}', 'danger')
        return redirect(url_for('admin.importar_estudiantes'))

# ============================================
# VER Y GESTIONAR ESTUDIANTES
# ============================================

@bp.route('/estudiantes')
@login_required
@admin_required
def estudiantes():
    """Lista de estudiantes matriculados"""
    institucion = current_user.institucion
    
    grupo_id = request.args.get('grupo_id', type=int)
    busqueda = request.args.get('busqueda', '')
    
    query = Estudiante.query.filter_by(institucion_id=institucion.id)
    
    if grupo_id:
        query = query.filter_by(grupo_id=grupo_id)
    
    if busqueda:
        query = query.filter(
            db.or_(
                Estudiante.nombres.ilike(f'%{busqueda}%'),
                Estudiante.apellidos.ilike(f'%{busqueda}%'),
                Estudiante.numero_documento.ilike(f'%{busqueda}%')
            )
        )
    
    estudiantes = query.order_by(Estudiante.apellidos, Estudiante.nombres).all()
    
    grupos = Grupo.query.join(Curso).filter(
        Curso.institucion_id == institucion.id
    ).order_by(Curso.orden, Grupo.nombre).all()
    
    return render_template('admin/estudiantes.html',
                         estudiantes=estudiantes,
                         grupos=grupos,
                         grupo_id=grupo_id,
                         busqueda=busqueda)

@bp.route('/estudiantes/cambiar-grupo/<int:estudiante_id>', methods=['GET'])
@login_required
@admin_required
def cambiar_grupo(estudiante_id):
    """Formulario para cambiar de grupo a un estudiante"""
    institucion = current_user.institucion
    
    estudiante = Estudiante.query.filter_by(
        id=estudiante_id,
        institucion_id=institucion.id
    ).first_or_404()
    
    grupos = Grupo.query.join(Curso).filter(
        Curso.institucion_id == institucion.id,
        Grupo.id != estudiante.grupo_id
    ).order_by(Curso.orden, Grupo.nombre).all()
    
    return render_template('admin/cambiar_grupo.html',
                         estudiante=estudiante,
                         grupos=grupos)

@bp.route('/estudiantes/cambiar-grupo/<int:estudiante_id>', methods=['POST'])
@login_required
@admin_required
def guardar_cambio_grupo(estudiante_id):
    """Guardar el cambio de grupo del estudiante"""
    institucion = current_user.institucion
    
    estudiante = Estudiante.query.filter_by(
        id=estudiante_id,
        institucion_id=institucion.id
    ).first_or_404()
    
    nuevo_grupo_id = request.form.get('nuevo_grupo_id', type=int)
    motivo = request.form.get('motivo', 'otro')
    observacion = request.form.get('observacion', '')
    
    nuevo_grupo = Grupo.query.join(Curso).filter(
        Grupo.id == nuevo_grupo_id,
        Curso.institucion_id == institucion.id
    ).first()
    
    if not nuevo_grupo:
        flash('El grupo seleccionado no existe.', 'danger')
        return redirect(url_for('admin.cambiar_grupo', estudiante_id=estudiante_id))
    
    grupo_anterior = estudiante.grupo.nombre if estudiante.grupo else 'Ninguno'
    
    estudiante.grupo_id = nuevo_grupo_id
    
    if motivo == 'promocion':
        estudiante.ano_lectivo = nuevo_grupo.ano_lectivo
    
    db.session.commit()
    
    flash(f'Estudiante {estudiante.nombre_completo()} trasladado de {grupo_anterior} a {nuevo_grupo.nombre}.', 'success')
    return redirect(url_for('admin.estudiantes'))

# ============================================
# CARGA ACADÉMICA
# ============================================

@bp.route('/carga-academica', methods=['GET'])
@login_required
@admin_required
def carga_academica():
    """Página para asignar carga académica"""
    institucion = current_user.institucion
    
    docentes = Usuario.query.join(
    usuario_rol, Usuario.id == usuario_rol.c.usuario_id
    ).join(
    Rol, usuario_rol.c.rol_id == Rol.id
    ).filter(
    Usuario.institucion_id == institucion.id,
    Rol.nombre == 'docente'
    ).order_by(
    Usuario.apellidos, Usuario.nombres
    ).all()
    
    grupos = Grupo.query.join(Curso).filter(
        Curso.institucion_id == institucion.id
    ).order_by(Curso.orden, Grupo.nombre).all()
    
    asignaturas = Asignatura.query.filter_by(
        institucion_id=institucion.id,
        activa=True
    ).order_by(Asignatura.nombre).all()
    
    cargas = CargaAcademica.query.join(Grupo).join(Curso).filter(
        Curso.institucion_id == institucion.id
    ).order_by(CargaAcademica.ano_lectivo.desc()).all()
    
    return render_template('admin/carga_academica.html',
                         docentes=docentes,
                         grupos=grupos,
                         asignaturas=asignaturas,
                         cargas=cargas)

@bp.route('/carga-academica/guardar', methods=['POST'])
@login_required
@admin_required
def guardar_carga():
    """Guardar nueva asignación de carga académica"""
    docente_id = request.form.get('docente_id', type=int)
    grupo_id = request.form.get('grupo_id', type=int)
    asignatura_id = request.form.get('asignatura_id', type=int)
    ano_lectivo = request.form.get('ano_lectivo', type=int, default=2026)
    
    existe = CargaAcademica.query.filter_by(
        docente_id=docente_id,
        grupo_id=grupo_id,
        asignatura_id=asignatura_id,
        ano_lectivo=ano_lectivo
    ).first()
    
    if existe:
        flash('Esta carga académica ya está asignada.', 'warning')
        return redirect(url_for('admin.carga_academica'))
    
    carga = CargaAcademica(
        docente_id=docente_id,
        grupo_id=grupo_id,
        asignatura_id=asignatura_id,
        ano_lectivo=ano_lectivo,
        activa=True
    )
    
    db.session.add(carga)
    db.session.commit()
    
    flash('Carga académica asignada correctamente.', 'success')
    return redirect(url_for('admin.carga_academica'))

@bp.route('/carga-academica/eliminar/<int:carga_id>')
@login_required
@admin_required
def eliminar_carga(carga_id):
    """Eliminar una asignación de carga académica"""
    institucion = current_user.institucion
    
    carga = CargaAcademica.query.join(Grupo).join(Curso).filter(
        CargaAcademica.id == carga_id,
        Curso.institucion_id == institucion.id
    ).first_or_404()
    
    db.session.delete(carga)
    db.session.commit()
    
    flash('Carga académica eliminada correctamente.', 'success')
    return redirect(url_for('admin.carga_academica'))

# ============================================
# CREAR DOCENTES
# ============================================

@bp.route('/docentes/crear', methods=['GET'])
@login_required
@admin_required
def crear_docente():
    """Formulario para crear un nuevo docente"""
    return render_template('admin/crear_docente.html')

@bp.route('/docentes/guardar', methods=['POST'])
@login_required
@admin_required
def guardar_docente():
    """Guardar nuevo docente"""
    institucion = current_user.institucion
    
    username = request.form.get('username')
    email = request.form.get('email')
    
    if Usuario.query.filter_by(username=username).first():
        flash(f'El usuario "{username}" ya existe.', 'danger')
        return redirect(url_for('admin.crear_docente'))
    
    if Usuario.query.filter_by(email=email).first():
        flash(f'El email "{email}" ya está registrado.', 'danger')
        return redirect(url_for('admin.crear_docente'))
    
    docente = Usuario(
        username=username,
        email=email,
        nombres=request.form.get('nombres'),
        apellidos=request.form.get('apellidos'),
        telefono=request.form.get('telefono') or None,
        institucion_id=institucion.id
    )
    docente.set_password(request.form.get('password'))
    
    rol_docente = Rol.query.filter_by(nombre='docente').first()
    if rol_docente:
        docente.roles.append(rol_docente)
    
    db.session.add(docente)
    db.session.commit()
    
    flash(f'Docente {docente.nombre_completo()} creado exitosamente.', 'success')
    return redirect(url_for('admin.carga_academica'))

@bp.route('/descargar-plantilla')
@login_required
@admin_required
def descargar_plantilla():
    """Descargar plantilla Excel para importar estudiantes"""
    import pandas as pd
    from io import BytesIO
    
    # Crear DataFrame de ejemplo
    datos = {
        'tipo_documento': ['TI', 'TI', 'TI'],
        'numero_documento': ['1234567890', '1234567891', '1234567892'],
        'nombres': ['Juan Carlos', 'Maria Alejandra', 'Carlos Andres'],
        'apellidos': ['Perez Gomez', 'Lopez Garcia', 'Martinez Ruiz'],
        'genero': ['M', 'F', 'M'],
        'fecha_nacimiento': ['2010-05-15', '2010-08-22', '2010-03-10'],
        'grupo_id': [1, 1, 1],
        'ano_lectivo': [2026, 2026, 2026]
    }
    
    df = pd.DataFrame(datos)
    
    # Guardar en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Estudiantes')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='plantilla_estudiantes.xlsx'
    )