from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from conexion.mysql_connection import get_db_connection

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"  # Necesario para flash

# Carpeta para subir fotos
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        cedula = request.form.get('cedula', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        foto_file = request.files.get('foto')

        # Validación de campos vacíos
        if not all([nombre, apellido, cedula, email, telefono, direccion]):
            flash("Todos los campos obligatorios deben llenarse.", "danger")
            return render_template('registrar.html', nombre=nombre, apellido=apellido,
                                   cedula=cedula, email=email, telefono=telefono,
                                   direccion=direccion)

        # Validar cédula única
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM afiliados WHERE cedula = %s", (cedula,))
        existe = cursor.fetchone()
        if existe:
            flash("La cédula ya está registrada.", "danger")
            cursor.close()
            conn.close()
            return render_template('registrar.html', nombre=nombre, apellido=apellido,
                                   cedula=cedula, email=email, telefono=telefono,
                                   direccion=direccion)

        # Guardar foto si existe
        foto_filename = None
        if foto_file and foto_file.filename != '':
            foto_filename = secure_filename(foto_file.filename)
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], foto_filename)
            foto_file.save(foto_path)

        # Insertar en la base de datos
        cursor.execute("""
            INSERT INTO afiliados (nombre, apellido, cedula, email, telefono, direccion, foto)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nombre, apellido, cedula, email, telefono, direccion, foto_filename))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Afiliado registrado correctamente.", "success")
        return redirect(url_for('registrar'))

    return render_template('registrar.html')


@app.route('/afiliados')
def listar_afiliados():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM afiliados ORDER BY id DESC")
    afiliados = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('afiliados.html', afiliados=afiliados)


if __name__ == '__main__':
    app.run(debug=True)
