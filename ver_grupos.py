from app import create_app
from app.models import Grupo, Curso

app = create_app()

with app.app_context():
    grupos = Grupo.query.all()
    print("GRUPOS DISPONIBLES:")
    print("-" * 50)
    for g in grupos:
        print(f"ID: {g.id} | Nombre: {g.nombre} | Curso: {g.curso.nombre} | Año: {g.ano_lectivo}")
    print("-" * 50)