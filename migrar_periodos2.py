from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Agregar columnas si no existen (nombre correcto de la tabla: periodos_academicos)
        db.session.execute(text("""
            ALTER TABLE periodos_academicos 
            ADD COLUMN IF NOT EXISTS fecha_cierre_notas DATE,
            ADD COLUMN IF NOT EXISTS cierre_forzado BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS autorizado_por INTEGER,
            ADD COLUMN IF NOT EXISTS fecha_autorizacion TIMESTAMP;
        """))
        
        # Actualizar fechas de cierre (igualar a fecha_fin)
        db.session.execute(text("""
            UPDATE periodos_academicos 
            SET fecha_cierre_notas = fecha_fin 
            WHERE fecha_cierre_notas IS NULL;
        """))
        
        db.session.commit()
        print("✅ Columnas agregadas y fechas actualizadas correctamente.")
        print("Ahora el sistema bloqueara notas despues de la fecha de cierre.")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")