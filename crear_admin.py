from app import create_app, db
from app.models import Usuario, Rol, Institucion

app = create_app()

with app.app_context():
    # 1. Crear una institucion de prueba si no existe
    institucion = Institucion.query.filter_by(nombre='Colegio de Prueba').first()
    
    if not institucion:
        institucion = Institucion(
            nombre='Colegio de Prueba',
            codigo_dane='123456789',
            nit='900123456',
            direccion='Calle 123 # 45-67, Bogota',
            telefono='6011234567',
            email='colegio@prueba.edu'
        )
        db.session.add(institucion)
        db.session.commit()
        print("Institucion 'Colegio de Prueba' creada.")
    else:
        print("La institucion ya existe.")
    
    # 2. Crear usuario admin si no existe
    admin = Usuario.query.filter_by(username='director').first()
    
    if not admin:
        admin = Usuario(
            username='director',
            email='director@prueba.edu',
            nombres='Juan',
            apellidos='Perez',
            institucion_id=institucion.id
        )
        admin.set_password('director123')
        
        # Asignar rol admin
        rol_admin = Rol.query.filter_by(nombre='admin').first()
        if rol_admin:
            admin.roles.append(rol_admin)
        
        db.session.add(admin)
        db.session.commit()
        
        print("\nUsuario admin creado exitosamente:")
        print("  Usuario: director")
        print("  Contrasena: director123")
        print("  Institucion: Colegio de Prueba")
    else:
        print("\nEl usuario 'director' ya existe.")