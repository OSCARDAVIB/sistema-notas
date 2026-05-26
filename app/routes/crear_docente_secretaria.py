from app import create_app, db
from app.models import Usuario, Rol, Institucion, CargaAcademica, Grupo, Asignatura, Curso

app = create_app()

with app.app_context():
    # Obtener la institucion de prueba
    institucion = Institucion.query.filter_by(nombre='Colegio de Prueba').first()
    
    if not institucion:
        print("ERROR: No existe la institucion 'Colegio de Prueba'.")
        print("Ejecuta primero: python crear_admin.py")
        exit()
    
    # 1. Crear DOCENTE
    docente = Usuario.query.filter_by(username='profesor').first()
    
    if not docente:
        docente = Usuario(
            username='profesor',
            email='profesor@prueba.edu',
            nombres='Carlos',
            apellidos='Rodriguez',
            institucion_id=institucion.id
        )
        docente.set_password('profesor123')
        
        rol_docente = Rol.query.filter_by(nombre='docente').first()
        if rol_docente:
            docente.roles.append(rol_docente)
        
        db.session.add(docente)
        db.session.commit()
        
        print("Docente creado:")
        print("  Usuario: profesor")
        print("  Contrasena: profesor123")
    else:
        print("El docente 'profesor' ya existe.")
    
    # 2. Crear SECRETARIA
    secretaria = Usuario.query.filter_by(username='secretaria').first()
    
    if not secretaria:
        secretaria = Usuario(
            username='secretaria',
            email='secretaria@prueba.edu',
            nombres='Ana',
            apellidos='Martinez',
            institucion_id=institucion.id
        )
        secretaria.set_password('secretaria123')
        
        rol_secretaria = Rol.query.filter_by(nombre='secretaria').first()
        if rol_secretaria:
            secretaria.roles.append(rol_secretaria)
        
        db.session.add(secretaria)
        db.session.commit()
        
        print("\nSecretaria creada:")
        print("  Usuario: secretaria")
        print("  Contrasena: secretaria123")
    else:
        print("\nLa secretaria 'secretaria' ya existe.")
    
    # 3. Crear algunos datos de prueba si no existen
    # Curso
    curso = Curso.query.filter_by(institucion_id=institucion.id, nombre='Sexto').first()
    if not curso:
        curso = Curso(institucion_id=institucion.id, nombre='Sexto', codigo='6', orden=6)
        db.session.add(curso)
        db.session.commit()
        print("\nCurso 'Sexto' creado.")
    
    # Grupo
    grupo = Grupo.query.filter_by(curso_id=curso.id, nombre='6-1').first()
    if not grupo:
        grupo = Grupo(curso_id=curso.id, nombre='6-1', codigo='A', ano_lectivo=2026)
        db.session.add(grupo)
        db.session.commit()
        print("Grupo '6-1' creado.")
    
    # Asignatura
    asignatura = Asignatura.query.filter_by(institucion_id=institucion.id, nombre='Matematicas').first()
    if not asignatura:
        asignatura = Asignatura(institucion_id=institucion.id, nombre='Matematicas', codigo='MAT', area='Matematicas')
        db.session.add(asignatura)
        db.session.commit()
        print("Asignatura 'Matematicas' creada.")
    
    # Carga academica para el docente
    carga = CargaAcademica.query.filter_by(docente_id=docente.id, grupo_id=grupo.id, asignatura_id=asignatura.id).first()
    if not carga:
        carga = CargaAcademica(
            docente_id=docente.id,
            asignatura_id=asignatura.id,
            grupo_id=grupo.id,
            ano_lectivo=2026
        )
        db.session.add(carga)
        db.session.commit()
        print("\nCarga academica asignada al docente.")
    
    print("\n✅ Todo listo para probar!")