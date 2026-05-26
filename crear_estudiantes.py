from app import create_app, db
from app.models import Estudiante, Institucion, Grupo

app = create_app()

with app.app_context():
    # Obtener la institucion y grupo
    institucion = Institucion.query.filter_by(nombre='Colegio de Prueba').first()
    grupo = Grupo.query.filter_by(nombre='6-1').first()
    
    if not institucion or not grupo:
        print("ERROR: No existe la institucion o el grupo.")
        exit()
    
    # Lista de estudiantes de prueba
    estudiantes_data = [
        {'tipo_documento': 'TI', 'numero_documento': '1234567890', 'nombres': 'Juan', 'apellidos': 'Perez Gomez', 'genero': 'M'},
        {'tipo_documento': 'TI', 'numero_documento': '1234567891', 'nombres': 'Maria', 'apellidos': 'Lopez Garcia', 'genero': 'F'},
        {'tipo_documento': 'TI', 'numero_documento': '1234567892', 'nombres': 'Carlos', 'apellidos': 'Martinez Ruiz', 'genero': 'M'},
        {'tipo_documento': 'TI', 'numero_documento': '1234567893', 'nombres': 'Ana', 'apellidos': 'Sanchez Torres', 'genero': 'F'},
        {'tipo_documento': 'TI', 'numero_documento': '1234567894', 'nombres': 'Luis', 'apellidos': 'Gonzalez Diaz', 'genero': 'M'},
    ]
    
    creados = 0
    for data in estudiantes_data:
        # Verificar si ya existe
        existe = Estudiante.query.filter_by(numero_documento=data['numero_documento']).first()
        if not existe:
            estudiante = Estudiante(
                institucion_id=institucion.id,
                tipo_documento=data['tipo_documento'],
                numero_documento=data['numero_documento'],
                nombres=data['nombres'],
                apellidos=data['apellidos'],
                genero=data['genero'],
                grupo_id=grupo.id,
                ano_lectivo=2026
            )
            db.session.add(estudiante)
            creados += 1
    
    db.session.commit()
    
    print(f"{creados} estudiantes creados exitosamente.")
    print(f"Total de estudiantes en el grupo: {Estudiante.query.filter_by(grupo_id=grupo.id).count()}")