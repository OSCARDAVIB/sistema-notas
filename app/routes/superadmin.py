from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Usuario, Rol, Institucion
from app.models import Usuario, Rol, Institucion, Nota

bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

# Decorador para verificar que sea superadmin
def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_superadmin():
            flash('No tienes permiso para acceder a esta página.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@bp.route('/dashboard')
@login_required
@superadmin_required
def dashboard():
    """Panel principal del Super Admin"""
    total_instituciones = Institucion.query.count()
    total_usuarios = Usuario.query.count()
    instituciones_activas = Institucion.query.filter_by(activa=True).count()
    instituciones_inactivas = Institucion.query.filter_by(activa=False).count()
    
    # Últimas 5 instituciones registradas
    ultimas_instituciones = Institucion.query.order_by(
        Institucion.fecha_registro.desc()
    ).limit(5).all()
    
    # Últimos 5 usuarios creados
    ultimos_usuarios = Usuario.query.order_by(
        Usuario.fecha_creacion.desc()
    ).limit(5).all()
    
    return render_template('superadmin/dashboard.html',
                         total_instituciones=total_instituciones,
                         total_usuarios=total_usuarios,
                         instituciones_activas=instituciones_activas,
                         instituciones_inactivas=instituciones_inactivas,
                         ultimas_instituciones=ultimas_instituciones,
                         ultimos_usuarios=ultimos_usuarios)

@bp.route('/instituciones')
@login_required
@superadmin_required
def instituciones():
    """Lista de instituciones"""
    instituciones = Institucion.query.all()
    return render_template('superadmin/instituciones.html', instituciones=instituciones)

@bp.route('/instituciones/crear', methods=['GET', 'POST'])
@login_required
@superadmin_required
def crear_institucion():
    """Crear nueva institución"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        codigo_dane = request.form.get('codigo_dane')
        nit = request.form.get('nit')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        
        # Verificar que no exista
        if Institucion.query.filter_by(nombre=nombre).first():
            flash('Ya existe una institución con ese nombre.', 'danger')
            return redirect(url_for('superadmin.crear_institucion'))
        
        institucion = Institucion(
            nombre=nombre,
            codigo_dane=codigo_dane,
            nit=nit,
            direccion=direccion,
            telefono=telefono,
            email=email
        )
        
        db.session.add(institucion)
        db.session.commit()
        
        flash(f'Institución "{nombre}" creada exitosamente.', 'success')
        return redirect(url_for('superadmin.instituciones'))
    
    return render_template('superadmin/crear_institucion.html')

@bp.route('/usuarios')
@login_required
@superadmin_required
def usuarios():
    """Lista de usuarios del sistema"""
    usuarios = Usuario.query.all()
    return render_template('superadmin/usuarios.html', usuarios=usuarios)

@bp.route('/usuarios/crear', methods=['GET', 'POST'])
@login_required
@superadmin_required
def crear_usuario():
    """Crear nuevo usuario con rol seleccionable"""
    # Obtener todos los roles disponibles para el select
    roles = Rol.query.all()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        rol_id = request.form.get('rol_id')  # <-- NUEVO: obtener el rol seleccionado
        
        # Verificar que no exista
        if Usuario.query.filter_by(username=username).first():
            flash('Ya existe un usuario con ese nombre.', 'danger')
            return redirect(url_for('superadmin.crear_usuario'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Ya existe un usuario con ese email.', 'danger')
            return redirect(url_for('superadmin.crear_usuario'))
        
        usuario = Usuario(
            username=username,
            email=email,
            nombres=nombres,
            apellidos=apellidos
        )
        usuario.set_password(password)
        
        # Asignar el rol seleccionado
        if rol_id:
            rol = Rol.query.get(int(rol_id))
            if rol:
                usuario.roles.append(rol)
        else:
            # Si no seleccionó, por defecto superadmin
            rol_superadmin = Rol.query.filter_by(nombre='superadmin').first()
            if rol_superadmin:
                usuario.roles.append(rol_superadmin)
        
        db.session.add(usuario)
        db.session.commit()
        
        flash(f'Usuario "{username}" creado exitosamente con rol {rol.nombre if rol else "superadmin"}.', 'success')
        return redirect(url_for('superadmin.usuarios'))
    
    return render_template('superadmin/crear_usuario.html', roles=roles)

# ============================================
# EDITAR Y ELIMINAR INSTITUCIONES
# ============================================

@bp.route('/instituciones/editar/<int:institucion_id>', methods=['GET', 'POST'])
@login_required
@superadmin_required
def editar_institucion(institucion_id):
    """Editar una institución existente"""
    institucion = Institucion.query.get_or_404(institucion_id)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        
        # Verificar que no exista otra con el mismo nombre
        existe = Institucion.query.filter(
            Institucion.nombre == nombre,
            Institucion.id != institucion_id
        ).first()
        
        if existe:
            flash('Ya existe otra institución con ese nombre.', 'danger')
            return redirect(url_for('superadmin.editar_institucion', institucion_id=institucion_id))
        
        institucion.nombre = nombre
        institucion.codigo_dane = request.form.get('codigo_dane')
        institucion.nit = request.form.get('nit')
        institucion.direccion = request.form.get('direccion')
        institucion.telefono = request.form.get('telefono')
        institucion.email = request.form.get('email')
        institucion.activa = 'activa' in request.form
        
        db.session.commit()
        flash(f'Institución "{institucion.nombre}" actualizada correctamente.', 'success')
        return redirect(url_for('superadmin.instituciones'))
    
    return render_template('superadmin/editar_institucion.html', institucion=institucion)


@bp.route('/instituciones/eliminar/<int:institucion_id>', methods=['POST'])
@login_required
@superadmin_required
def eliminar_institucion(institucion_id):
    """Eliminar una institución"""
    institucion = Institucion.query.get_or_404(institucion_id)
    
    nombre = institucion.nombre
    db.session.delete(institucion)
    db.session.commit()
    
    flash(f'Institución "{nombre}" eliminada correctamente.', 'success')
    return redirect(url_for('superadmin.instituciones'))


# ============================================
# EDITAR Y ELIMINAR USUARIOS
# ============================================

@bp.route('/usuarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
@superadmin_required
def editar_usuario(usuario_id):
    """Editar un usuario existente"""
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Verificar que no exista otro con el mismo username
        existe_username = Usuario.query.filter(
            Usuario.username == username,
            Usuario.id != usuario_id
        ).first()
        
        if existe_username:
            flash('Ya existe otro usuario con ese nombre.', 'danger')
            return redirect(url_for('superadmin.editar_usuario', usuario_id=usuario_id))
        
        # Verificar que no exista otro con el mismo email
        existe_email = Usuario.query.filter(
            Usuario.email == email,
            Usuario.id != usuario_id
        ).first()
        
        if existe_email:
            flash('Ya existe otro usuario con ese email.', 'danger')
            return redirect(url_for('superadmin.editar_usuario', usuario_id=usuario_id))
        
        usuario.username = username
        usuario.email = email
        usuario.nombres = request.form.get('nombres')
        usuario.apellidos = request.form.get('apellidos')
        
        # Actualizar contraseña solo si se escribió una nueva
        nueva_password = request.form.get('password')
        if nueva_password:
            usuario.set_password(nueva_password)
        
        usuario.activo = 'activo' in request.form
        
        db.session.commit()
        flash(f'Usuario "{usuario.username}" actualizado correctamente.', 'success')
        return redirect(url_for('superadmin.usuarios'))
    
    return render_template('superadmin/editar_usuario.html', usuario=usuario)


@bp.route('/usuarios/eliminar/<int:usuario_id>', methods=['POST'])
@login_required
@superadmin_required
def eliminar_usuario(usuario_id):
    """Desactivar un usuario (no eliminarlo si tiene registros asociados)"""
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # No permitir eliminarse a sí mismo
    if usuario.id == current_user.id:
        flash('No puedes eliminar tu propio usuario.', 'danger')
        return redirect(url_for('superadmin.usuarios'))
    
    username = usuario.username
    
    # Verificar si tiene notas registradas
    tiene_notas = db.session.query(Nota).filter_by(docente_id=usuario.id).first() is not None
    
    # Verificar si tiene carga académica
    tiene_carga = len(usuario.cargas_academicas) > 0 if hasattr(usuario, 'cargas_academicas') else False
    
    if tiene_notas or tiene_carga:
        # Tiene registros asociados: solo desactivar
        usuario.activo = False
        db.session.commit()
        flash(f'Usuario "{username}" tiene notas o carga académica registrada. Se ha desactivado en lugar de eliminar.', 'warning')
    else:
        # No tiene registros: eliminar completamente
        db.session.delete(usuario)
        db.session.commit()
        flash(f'Usuario "{username}" eliminado correctamente.', 'success')
    
    return redirect(url_for('superadmin.usuarios'))