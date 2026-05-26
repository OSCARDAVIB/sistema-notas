from app import create_app, db
from app.models import Usuario, Rol

app = create_app()

with app.app_context():
    # Verificar si ya existe un superadmin
    superadmin = Usuario.query.filter_by(username='admin').first()
    
    if superadmin:
        print("El usuario 'admin' ya existe.")
    else:
        # Crear usuario superadmin
        usuario = Usuario(
            username='admin',
            email='admin@sistema.edu',
            nombres='Super',
            apellidos='Administrador'
        )
        usuario.set_password('admin123')
        
        # Asignar rol superadmin
        rol = Rol.query.filter_by(nombre='superadmin').first()
        if rol:
            usuario.roles.append(rol)
        
        db.session.add(usuario)
        db.session.commit()
        
        print("Usuario superadmin creado exitosamente.")
        print("Usuario: admin")
        print("Contrasena: admin123")