from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import (
    Estudiante, Grupo, Curso, Nota, PeriodoAcademico,
    Institucion, Asignatura
)

import unicodedata

def normalizar_texto(texto):
    """Quita tildes y convierte ñ -> n, todo a mayúsculas"""
    if not texto:
        return ""
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    texto = texto.replace('ñ', 'n').replace('Ñ', 'N')
    return texto.upper()

def codigo_asignatura(nombre):
    """Convierte el nombre de una asignatura al codigo personalizado del colegio"""
    nombre_norm = normalizar_texto(nombre)
    
    codigos = {
        'MATEMATICAS': 'Mat.',
        'ESPANOL': 'Esp.',
        'INGLES': 'Ing.',
        'CIENCIAS NATURALES': 'C. Nat.',
        'CIENCIAS SOCIALES': 'C. Soc.',
        'EDUCACION ARTISTICA': 'Art.',
        'EDUCACION FISICA': 'E. Fis.',
        'ETICA Y VALORES': 'Et y Val.',
        'EDUCACION RELIGIOSA': 'Rel.',
        'TECNOLOGIA E INFORMATICA': 'Tec.',
        'COMPORTAMIENTO': 'Comp',
    }
    
    return codigos.get(nombre_norm, nombre_norm[:3])

bp = Blueprint('secretaria', __name__, url_prefix='/secretaria')

# Registrar normalizar_texto como filtro de Jinja2 para usar en templates
@bp.app_template_filter('normalizar')
def normalizar_filter(texto):
    """Filtro Jinja2 para normalizar texto (quitar tildes, ñ -> n, mayusculas)"""
    if not texto:
        return ""
    import unicodedata
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    texto = texto.replace('ñ', 'n').replace('Ñ', 'N')
    return texto.upper()

# Registrar filtro para codigo de asignatura
@bp.app_template_filter('codigo_asignatura')
def codigo_asignatura_filter(nombre):
    """Filtro Jinja2 para obtener codigo corto de asignatura"""
    return codigo_asignatura(nombre)

# Registrar funcion normalizar_texto como filtro de Jinja2
@bp.app_template_global()
def normalizar_texto_jinja(texto):
    """Version de normalizar_texto para usar en templates"""
    return normalizar_texto(texto)

# Decorador para verificar que sea secretaria
def secretaria_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_secretaria():
            flash('No tienes permiso para acceder a esta pagina.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@bp.route('/dashboard')
@login_required
@secretaria_required
def dashboard():
    """Panel principal de secretaria"""
    institucion = current_user.institucion
    
    total_estudiantes = Estudiante.query.filter_by(
        institucion_id=institucion.id,
        activo=True
    ).count()
    
    total_grupos = Grupo.query.join(Curso).filter(
        Curso.institucion_id == institucion.id
    ).count()
    
    return render_template('secretaria/dashboard.html',
                         total_estudiantes=total_estudiantes,
                         total_grupos=total_grupos)

@bp.route('/estudiantes')
@login_required
@secretaria_required
def estudiantes():
    """Lista de estudiantes"""
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
    
    estudiantes = query.all()
    grupos = Grupo.query.join(Curso).filter(
        Curso.institucion_id == institucion.id
    ).all()
    
    return render_template('secretaria/estudiantes.html',
                         estudiantes=estudiantes,
                         grupos=grupos,
                         grupo_id=grupo_id,
                         busqueda=busqueda)

@bp.route('/estudiante/<int:estudiante_id>')
@login_required
@secretaria_required
def ver_estudiante(estudiante_id):
    """Ver detalle de un estudiante"""
    estudiante = Estudiante.query.get_or_404(estudiante_id)
    
    notas = Nota.query.filter_by(estudiante_id=estudiante_id).all()
    
    notas_por_periodo = {}
    for nota in notas:
        periodo_nombre = f"{nota.periodo.ano_lectivo} - Periodo {nota.periodo.numero_periodo}"
        if periodo_nombre not in notas_por_periodo:
            notas_por_periodo[periodo_nombre] = []
        notas_por_periodo[periodo_nombre].append(nota)
    
    return render_template('secretaria/ver_estudiante.html',
                         estudiante=estudiante,
                         notas_por_periodo=notas_por_periodo)

@bp.route('/boletin-directo/<int:estudiante_id>')
@login_required
@secretaria_required
def boletin_directo(estudiante_id):
    """Generar boletín directo - redirige al último periodo disponible"""
    estudiante = Estudiante.query.get_or_404(estudiante_id)
    
    # Verificar que el estudiante pertenezca a la institución
    if estudiante.institucion_id != current_user.institucion_id:
        flash('No tienes permiso para ver este estudiante.', 'danger')
        return redirect(url_for('secretaria.estudiantes'))
    
    # Buscar el último periodo activo del año lectivo del estudiante
    # O el periodo más reciente disponible
    periodo = PeriodoAcademico.query.filter_by(
        institucion_id=current_user.institucion_id,
        ano_lectivo=estudiante.ano_lectivo
    ).order_by(PeriodoAcademico.numero_periodo.desc()).first()
    
    if not periodo:
        # Si no hay periodo del año del estudiante, buscar cualquier periodo activo
        periodo = PeriodoAcademico.query.filter_by(
            institucion_id=current_user.institucion_id,
            activo=True
        ).order_by(PeriodoAcademico.ano_lectivo.desc(),
                   PeriodoAcademico.numero_periodo.desc()).first()
    
    if not periodo:
        flash('No hay periodos académicos disponibles para generar el boletín.', 'warning')
        return redirect(url_for('secretaria.estudiantes'))
    
    # Redirigir directamente a generar_boletin con el periodo encontrado
    return redirect(url_for('secretaria.generar_boletin',
                          estudiante_id=estudiante_id,
                          periodo_id=periodo.id))   

@bp.route('/boletines')
@login_required
@secretaria_required
def boletines():
    """Pagina para generar boletines - individual o por curso"""
    institucion = current_user.institucion
    
    # La secretaria puede ver TODOS los periodos (activos e inactivos)
    # para poder imprimir boletines de periodos anteriores
    periodos = PeriodoAcademico.query.filter_by(
        institucion_id=institucion.id
    ).order_by(PeriodoAcademico.ano_lectivo.desc(),
               PeriodoAcademico.numero_periodo).all()
    
    grupos = Grupo.query.join(Curso).filter(
        Curso.institucion_id == institucion.id,
        Grupo.activo == True
    ).order_by(Curso.orden, Grupo.nombre).all()
    
    estudiantes = []
    busqueda = request.args.get('busqueda', '').strip()

    # ============================================
    # CORRECCIÓN: El if debe estar indentado dentro de la función
    # ============================================
    if busqueda:
        try:
            # ============================================
            # BUSQUEDA FLEXIBLE: quitar tildes del termino de busqueda
            # ============================================
            busqueda_norm = normalizar_texto(busqueda) if busqueda else ""

            # Obtener todos los estudiantes activos y filtrar en Python
            todos_estudiantes = Estudiante.query.filter(
                Estudiante.institucion_id == institucion.id,
                Estudiante.activo == True
            ).order_by(
                Estudiante.apellidos,
                Estudiante.nombres
            ).all()

            estudiantes = []

            for est in todos_estudiantes:
                try:
                    nombres_norm = normalizar_texto(est.nombres) if est.nombres else ""
                    apellidos_norm = normalizar_texto(est.apellidos) if est.apellidos else ""
                    documento = est.numero_documento or ""

                    # Buscar en nombre, apellido o documento
                    # (normalizado o original)
                    if (
                        busqueda_norm in nombres_norm or
                        busqueda_norm in apellidos_norm or
                        busqueda in documento or
                        busqueda in (est.nombres or "") or
                        busqueda in (est.apellidos or "")
                    ):
                        estudiantes.append(est)

                except Exception as e:
                    # Si un estudiante da error, saltarlo y continuar
                    continue

            # ============================================

        except Exception as e:
            flash(f'Error en la búsqueda: {str(e)}', 'danger')
            estudiantes = []
            # CORRECCIÓN: No retornar aquí, dejar que el return final maneje la respuesta

    # ============================================
    # CORRECCIÓN: Este return debe estar fuera del if busqueda
    # para que funcione tanto con búsqueda como sin búsqueda
    # ============================================
    return render_template('secretaria/boletines.html',
                         periodos=periodos,
                         grupos=grupos,
                         estudiantes=estudiantes,
                         busqueda=busqueda)

# ============================================
# FUNCION AUXILIAR: OBTENER PESOS REALES DE LOS PERIODOS
# ============================================

def obtener_pesos_periodos(ano_lectivo, institucion_id):
    """Obtiene los pesos (porcentajes) reales de los periodos desde la base de datos"""
    periodos_ano = PeriodoAcademico.query.filter_by(
        ano_lectivo=ano_lectivo,
        institucion_id=institucion_id
    ).order_by(PeriodoAcademico.numero_periodo).all()
    
    pesos = {}
    total_porcentaje = 0.0
    
    for p in periodos_ano:
        porcentaje = float(p.porcentaje) if p.porcentaje else 0.0
        pesos[p.numero_periodo] = porcentaje / 100.0
        total_porcentaje += porcentaje
    
    return pesos, total_porcentaje, periodos_ano

@bp.route('/generar-boletin/<int:estudiante_id>/<int:periodo_id>')
@login_required
@secretaria_required
def generar_boletin(estudiante_id, periodo_id):
    """Generar boletin individual con formato MEN"""
    estudiante = Estudiante.query.get_or_404(estudiante_id)
    periodo = PeriodoAcademico.query.get_or_404(periodo_id)
    
    # ============================================
    # NUEVO: OBTENER PESOS REALES DE LA BASE DE DATOS
    # ============================================
    pesos, total_porcentaje, periodos = obtener_pesos_periodos(
        periodo.ano_lectivo,
        current_user.institucion_id
    )
    
    # Validar que los porcentajes sumen 100%
    if abs(total_porcentaje - 100.0) > 0.01:
        flash(f'Advertencia: Los porcentajes de los periodos suman {total_porcentaje}%, deberian sumar 100%. Contacta al administrador.', 'warning')
    # ============================================
    
    notas_periodo = {1: {}, 2: {}, 3: {}, 4: {}}
    ponderados = {}
    observaciones = []
    
    for p in periodos:
        notas = Nota.query.filter_by(
            estudiante_id=estudiante_id,
            periodo_id=p.id
        ).all()
        
        for nota in notas:
            asignatura_nombre = normalizar_texto(nota.asignatura.nombre)
            notas_periodo[p.numero_periodo][asignatura_nombre] = "{:.1f}".format(float(nota.nota))
            
            if nota.observacion:
                observaciones.append(f"{nota.asignatura.nombre}: {nota.observacion}")
    
    # Calcular ponderados usando los pesos reales de la base de datos
    asignaturas_vistas = set()
    for p_num in notas_periodo:
        asignaturas_vistas.update(notas_periodo[p_num].keys())
    
    for asig in asignaturas_vistas:
        total_ponderado = 0
        
        for p_num in notas_periodo:
            if asig in notas_periodo[p_num]:
                try:
                    nota = float(notas_periodo[p_num][asig].replace(',', '.'))
                    # Usar el peso real del periodo desde la base de datos
                    if p_num in pesos:
                        total_ponderado += nota * pesos[p_num]
                except:
                    pass
        
        if total_ponderado > 0:
            ponderados[asig] = "{:.1f}".format(total_ponderado)
    
    return render_template('secretaria/boletin_pdf.html',
                         estudiante=estudiante,
                         periodo=periodo,
                         notas_periodo=notas_periodo,
                         ponderados=ponderados,
                         observaciones=observaciones,
                         institucion=current_user.institucion)

@bp.route('/generar-boletines-curso/<int:grupo_id>/<int:periodo_id>')
@login_required
@secretaria_required
def generar_boletines_curso(grupo_id, periodo_id):
    """Generar boletines de TODO un grupo/curso"""
    grupo = Grupo.query.get_or_404(grupo_id)
    periodo = PeriodoAcademico.query.get_or_404(periodo_id)
    
    if grupo.curso.institucion_id != current_user.institucion_id:
        flash('No tienes permiso para acceder a este grupo.', 'danger')
        return redirect(url_for('secretaria.boletines'))
    
    estudiantes = Estudiante.query.filter_by(
        grupo_id=grupo_id,
        activo=True
    ).order_by(Estudiante.apellidos, Estudiante.nombres).all()
    
    if not estudiantes:
        flash('No hay estudiantes activos en este grupo.', 'warning')
        return redirect(url_for('secretaria.boletines'))
    
    # ============================================
    # NUEVO: OBTENER PESOS REALES DE LA BASE DE DATOS
    # ============================================
    pesos, total_porcentaje, periodos = obtener_pesos_periodos(
        periodo.ano_lectivo,
        current_user.institucion_id
    )
    
    # Validar que los porcentajes sumen 100%
    if abs(total_porcentaje - 100.0) > 0.01:
        flash(f'Advertencia: Los porcentajes de los periodos suman {total_porcentaje}%, deberian sumar 100%. Contacta al administrador.', 'warning')
    # ============================================
    
    boletines_data = []
    
    for estudiante in estudiantes:
        notas_periodo = {1: {}, 2: {}, 3: {}, 4: {}}
        ponderados = {}
        observaciones = []
        
        for p in periodos:
            notas = Nota.query.filter_by(
                estudiante_id=estudiante.id,
                periodo_id=p.id
            ).all()
            
            for nota in notas:
                asignatura_nombre = normalizar_texto(nota.asignatura.nombre)
                notas_periodo[p.numero_periodo][asignatura_nombre] = "{:.1f}".format(float(nota.nota))
                
                if nota.observacion:
                    observaciones.append(f"{nota.asignatura.nombre}: {nota.observacion}")
        
        # Calcular ponderados usando los pesos reales de la base de datos
        asignaturas_vistas = set()
        for p_num in notas_periodo:
            asignaturas_vistas.update(notas_periodo[p_num].keys())
        
        for asig in asignaturas_vistas:
            total_ponderado = 0
            
            for p_num in notas_periodo:
                if asig in notas_periodo[p_num]:
                    try:
                        nota = float(notas_periodo[p_num][asig].replace(',', '.'))
                        # Usar el peso real del periodo desde la base de datos
                        if p_num in pesos:
                            total_ponderado += nota * pesos[p_num]
                    except:
                        pass
            
            if total_ponderado > 0:
                ponderados[asig] = "{:.1f}".format(total_ponderado)
        
        boletines_data.append({
            'estudiante': estudiante,
            'notas_periodo': notas_periodo,
            'ponderados': ponderados,
            'observaciones': observaciones
        })
    
    return render_template('secretaria/boletines_curso.html',
                         grupo=grupo,
                         periodo=periodo,
                         boletines_data=boletines_data,
                         institucion=current_user.institucion)

@bp.route('/reporte-grupo', methods=['GET'])
@login_required
@secretaria_required
def reporte_grupo():
    """Reporte consolidado de notas por grupo"""
    institucion = current_user.institucion
    
    grupo_id = request.args.get('grupo_id', type=int)
    periodo_id = request.args.get('periodo_id', type=int)
    tipo_reporte = request.args.get('tipo', 'periodo')
    
    grupos = Grupo.query.join(Curso).filter(
        Curso.institucion_id == institucion.id,
        Grupo.activo == True
    ).order_by(Curso.orden, Grupo.nombre).all()
    
    periodos = PeriodoAcademico.query.filter_by(
        institucion_id=institucion.id
    ).order_by(PeriodoAcademico.ano_lectivo.desc(),
               PeriodoAcademico.numero_periodo).all()
    
    grupo = None
    periodo = None
    estudiantes = []
    asignaturas_ordenadas = []
    notas_estudiantes = {}
    
    ORDEN_ASIGNATURAS = [
        'MATEMATICAS',
        'ESPANOL',
        'INGLES',
        'CIENCIAS NATURALES',
        'CIENCIAS SOCIALES',
        'EDUCACION ARTISTICA',
        'EDUCACION FISICA',
        'ETICA Y VALORES',
        'EDUCACION RELIGIOSA',
        'TECNOLOGIA E INFORMATICA',
        'COMPORTAMIENTO'
    ]
    
    if grupo_id:
        grupo = Grupo.query.get(grupo_id)
        
        estudiantes = Estudiante.query.filter_by(
            grupo_id=grupo_id,
            activo=True
        ).order_by(Estudiante.apellidos, Estudiante.nombres).all()
        
        asignaturas_db = Asignatura.query.filter_by(
            institucion_id=institucion.id,
            activa=True
        ).all()
        
        asignaturas_dict = {}
        for asig in asignaturas_db:
            nombre_norm = normalizar_texto(asig.nombre)
            asignaturas_dict[nombre_norm] = asig
        
        asignaturas_ordenadas = []
        for nombre_norm in ORDEN_ASIGNATURAS:
            if nombre_norm in asignaturas_dict:
                asignaturas_ordenadas.append(asignaturas_dict[nombre_norm])
        
        for asig in asignaturas_db:
            nombre_norm = normalizar_texto(asig.nombre)
            if nombre_norm not in ORDEN_ASIGNATURAS:
                asignaturas_ordenadas.append(asig)
        
        # ============================================
        # NUEVO: OBTENER PESOS REALES PARA REPORTE FINAL
        # ============================================
        pesos = {}
        if tipo_reporte == 'final' and estudiantes:
            # Obtener el año lectivo del primer estudiante (todos son del mismo grupo)
            ano_lectivo = estudiantes[0].ano_lectivo
            pesos, total_porcentaje, _ = obtener_pesos_periodos(
                ano_lectivo,
                institucion.id
            )
            
            if abs(total_porcentaje - 100.0) > 0.01:
                flash(f'Advertencia: Los porcentajes de los periodos suman {total_porcentaje}%, deberian sumar 100%. Contacta al administrador.', 'warning')
        # ============================================
        
        for est in estudiantes:
            notas_estudiantes[est.id] = {}
            
            if tipo_reporte == 'periodo' and periodo_id:
                periodo = PeriodoAcademico.query.get(periodo_id)
                notas = Nota.query.filter_by(
                    estudiante_id=est.id,
                    periodo_id=periodo_id
                ).all()
                
                for nota in notas:
                    nombre_norm = normalizar_texto(nota.asignatura.nombre)
                    notas_estudiantes[est.id][nombre_norm] = float(nota.nota)
                    
            else:
                notas = Nota.query.filter_by(estudiante_id=est.id).all()
                
                notas_por_asig = {}
                for nota in notas:
                    nombre_norm = normalizar_texto(nota.asignatura.nombre)
                    if nombre_norm not in notas_por_asig:
                        notas_por_asig[nombre_norm] = {}
                    notas_por_asig[nombre_norm][nota.periodo.numero_periodo] = float(nota.nota)
                
                # Calcular promedio ponderado usando pesos reales
                for asig_nombre, periodos_notas in notas_por_asig.items():
                    total = 0
                    for p_num, nota in periodos_notas.items():
                        if p_num in pesos:
                            total += nota * pesos[p_num]
                    if total > 0:
                        notas_estudiantes[est.id][asig_nombre] = round(total, 1)
    
    return render_template('secretaria/reporte_grupo.html',
                         grupos=grupos,
                         periodos=periodos,
                         grupo=grupo,
                         periodo=periodo,
                         tipo_reporte=tipo_reporte,
                         asignaturas=asignaturas_ordenadas,
                         estudiantes=estudiantes,
                         notas_estudiantes=notas_estudiantes)