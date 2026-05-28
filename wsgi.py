from app import create_app, db
from flask_migrate import Migrate
import os

app = create_app()
migrate = Migrate(app, db)

<<<<<<< HEAD
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
=======
# Render asigna el puerto automáticamente
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
>>>>>>> 7f7db7a76aec5781e95821a46c657efa6bff9abd
