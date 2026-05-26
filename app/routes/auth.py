from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario, Rol

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    """Página principal - redirige según el rol"""
    if current_user.is_authenticated:
        if current_user.es_superadmin():
            return redirect(url_for('superadmin.dashboard'))
        elif current_user.es_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.es_docente():
            return redirect(url_for('docente.dashboard'))
        elif current_user.es_secretaria():
            return redirect(url_for('secretaria.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(usuario)
            flash(f'Bienvenido, {usuario.nombre_completo()}!', 'success')
            return redirect(url_for('auth.index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))