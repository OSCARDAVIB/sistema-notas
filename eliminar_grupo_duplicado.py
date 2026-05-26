from app import create_app, db
from app.models import Grupo, Estudiante

app = create_app()

with app.app_context():
    # Buscar el grupo duplicado 5°B
    grupo_duplicado = Grupo.query.filter_by(nombre='5°B').first()
    
    if grupo_duplicado:
        print(f"Grupo encontrado: ID {grupo_duplicado.id} - {grupo_duplicado.nombre}")
        
        # Verificar si tiene estudiantes
        estudiantes = Estudiante.query.filter_by(grupo_id=grupo_duplicado.id).all()
        
        if estudiantes:
            print(f"⚠️  Este grupo tiene {len(estudiantes)} estudiantes.")
            print("Debes moverlos al grupo 5-2 primero.")
            
            # Mover estudiantes al grupo 5-2
            grupo_correcto = Grupo.query.filter_by(nombre='5-2').first()
            if grupo_correcto:
                for est in estudiantes:
                    est.grupo_id = grupo_correcto.id
                    print(f"  → {est.nombre_completo()} movido a {grupo_correcto.nombre}")
                
                db.session.commit()
                print("✅ Estudiantes movidos correctamente.")
        else:
            print("✅ El grupo no tiene estudiantes.")
        
        # Eliminar el grupo duplicado
        db.session.delete(grupo_duplicado)
        db.session.commit()
        print(f"✅ Grupo '{grupo_duplicado.nombre}' eliminado.")
    else:
        print("No se encontró el grupo duplicado '5°B'.")
    
    # Verificar grupos restantes
    print("\nGrupos actuales en el sistema:")
    grupos = Grupo.query.all()
    for g in grupos:
        print(f"  ID: {g.id} | {g.nombre} ({g.curso.nombre})")