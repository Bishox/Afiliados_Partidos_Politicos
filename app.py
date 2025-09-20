from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.utils import secure_filename
import os
from conexion.mysql_connection import get_db_connection

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"

# Carpeta para subir fotos
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.login_message = "Debes iniciar sesión para acceder a esta página."
login_manager.init_app(app)
login_manager.login_view = 'login'


# Modelo de usuario
class User(UserMixin):
    def __init__(self, id, username, email, password, telefono):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.telefono = telefono

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_data:
        return User(**user_data)
    return None

# INDEX
@app.route('/')
def index():
    return render_template('index.html')

# REGISTRO DE USUARIO
@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if current_user.is_authenticated:
        return redirect(url_for('listar_afiliados'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        telefono = request.form.get('telefono').strip()

        if not all([username, email, password, telefono]):
            flash("Todos los campos son obligatorios.", "danger")
            return render_template('register_user.html', username=username, email=email, telefono=telefono)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Validar que el email sea único
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        exists = cursor.fetchone()
        if exists:
            flash("El correo electrónico ya está registrado.", "danger")
            cursor.close()
            conn.close()
            return render_template('register_user.html', username=username, email=email, telefono=telefono)

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users (username, email, password, telefono)
            VALUES (%s, %s, %s, %s)
        """, (username, email, hashed_password, telefono))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Cuenta creada correctamente. Inicia sesión.", "success")
        return redirect(url_for('login'))

    return render_template('register_user.html')

# LOGIN CON EMAIL
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('listar_afiliados'))

    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data and check_password_hash(user_data['password'], password):
            user = User(**user_data)
            login_user(user)
            flash("¡Has iniciado sesión correctamente!", "success")
            return redirect(url_for('listar_afiliados'))
        else:
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template('login.html', email=email)

    return render_template('login.html')

# LOGOUT
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "success")
    return redirect(url_for('login'))

# REGISTRO DE AFILIADOS (PROTEGIDO)
@app.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        cedula = request.form.get('cedula', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        foto_file = request.files.get('foto')

        if not all([nombre, apellido, cedula, email, telefono, direccion]):
            flash("Todos los campos obligatorios deben llenarse.", "danger")
            return render_template('registrar.html', nombre=nombre, apellido=apellido,
                                   cedula=cedula, email=email, telefono=telefono,
                                   direccion=direccion)

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

        foto_filename = None
        if foto_file and foto_file.filename != '':
            foto_filename = secure_filename(foto_file.filename)
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], foto_filename)
            foto_file.save(foto_path)

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

# LISTAR AFILIADOS (PROTEGIDO)
@app.route('/afiliados')
@login_required
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
