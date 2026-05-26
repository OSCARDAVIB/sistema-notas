from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Listar todas las tablas
    resultado = db.session.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """))
    
    print("=== TABLAS EN LA BASE DE DATOS ===")
    for fila in resultado:
        print(f"  - {fila[0]}")
    print("==================================")
    
    # Buscar tablas que contengan "periodo"
    resultado2 = db.session.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%periodo%'
        ORDER BY table_name;
    """))
    
    print("\n=== TABLAS CON 'periodo' EN EL NOMBRE ===")
    for fila in resultado2:
        print(f"  - {fila[0]}")
    print("==========================================")