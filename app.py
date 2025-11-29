

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import mysql.connector
import config
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from datetime import date
from mysql.connector.errors import IntegrityError
from flask import flash
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__)

# ----------------- Conexión a la base de datos ------------------

def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos MySQL
    usando los datos definidos en el archivo config.py
    """
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME
    )

# ----------------- Categorías ------------------

@app.route('/registrar_categoria', methods=['GET', 'POST'])
def registrar_categoria():
    """
    Registrar una nueva categoría. Valida que no exista el nombre y que no esté vacío.
    En POST inserta la categoría y redirige a consultar categorías.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        descripcion = request.form['descripcion'].strip()
        
        errores = []

        # Validar que nombre no esté vacío
        if not nombre:
            errores.append("El nombre de la categoría es obligatorio.")
        
        # Validar que no exista ya ese nombre en la BD
        cursor.execute("SELECT id_categoria FROM categorias WHERE nombre = %s", (nombre,))
        if cursor.fetchone():
            errores.append("El nombre de la categoría ya está registrado.")
        
        if errores:
            cursor.close()
            conn.close()
            return render_template('registrar_categoria.html',
                                   error=' '.join(errores),
                                   nombre=nombre,
                                   descripcion=descripcion)

        # Insertar categoría nueva
        cursor.execute("INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s)", (nombre, descripcion))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/consultar_categorias')
    
    cursor.close()
    conn.close()
    return render_template('registrar_categoria.html')

@app.route('/consultar_categorias')
def consultar_categorias():
    """
    Mostrar todas las categorías con opción de ordenarlas por nombre ascendente o descendente.
    """
    orden = request.args.get('orden', 'nombre_asc')

    sql = "SELECT * FROM categorias"
    if orden == 'nombre_desc':
        sql += " ORDER BY nombre DESC"
    elif orden == 'nombre_asc':
        sql += " ORDER BY nombre ASC"
    else:
        sql += " ORDER BY id_categoria ASC"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql)
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('consultar_categorias.html', categorias=categorias, orden=orden)


# ----------------- Participantes ------------------

@app.route('/registrar_participante', methods=['GET', 'POST'])
def registrar_participante():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        correo = request.form['correo'].strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form['direccion'].strip()
        edad = request.form['edad'].strip()
        genero = request.form['genero'].strip()
        ocupacion = request.form['ocupacion'].strip()
        usuario = request.form['usuario'].strip()
        password = request.form['password'].strip()
        fecha_registro = date.today()

        errores = []

        # Validaciones básicas
        if not nombre:
            errores.append("El nombre completo es obligatorio.")
        if not correo:
            errores.append("El correo electrónico es obligatorio.")
        if not telefono:
            errores.append("El teléfono es obligatorio.")

        # Validar duplicados
        cursor.execute("SELECT id_participante FROM participantes WHERE nombre = %s", (nombre,))
        if cursor.fetchone():
            errores.append("Ya existe un participante con ese nombre completo.")

        cursor.execute("SELECT id_participante FROM participantes WHERE correo = %s", (correo,))
        if cursor.fetchone():
            errores.append("Ya existe un participante con ese correo electrónico.")

        cursor.execute("SELECT id_participante FROM participantes WHERE telefono = %s", (telefono,))
        if cursor.fetchone():
            errores.append("Ya existe un participante con ese teléfono.")

        if usuario:
            cursor.execute("SELECT id_participante FROM participantes WHERE usuario = %s", (usuario,))
            if cursor.fetchone():
                errores.append("Ese nombre de usuario ya está en uso.")

        if errores:
            cursor.close()
            conn.close()
            return render_template('registrar_participante.html',
                                   error=' '.join(errores),
                                   nombre=nombre,
                                   correo=correo,
                                   telefono=telefono,
                                   direccion=direccion,
                                   edad=edad,
                                   genero=genero,
                                   ocupacion=ocupacion,
                                   usuario=usuario)

        # Solo generar hash si se proporciona una contraseña
        password_hash = generate_password_hash(password) if password else None

        # Preparar campos base
        campos = ["nombre", "correo", "telefono", "direccion", "edad", "genero", "ocupacion", "fecha_registro"]
        valores = [nombre, correo, telefono, direccion, int(edad) if edad else None, genero, ocupacion, fecha_registro]

        # Agregar usuario y contraseña solo si se proporciona alguno
        if usuario or password:
            campos.insert(-1, "usuario")
            campos.insert(-1, "password")
            valores.insert(-1, usuario)
            valores.insert(-1, password_hash)

        # Construir query dinámicamente
        query = f"""
            INSERT INTO participantes ({', '.join(campos)})
            VALUES ({', '.join(['%s'] * len(valores))})
        """
        cursor.execute(query, valores)
        conn.commit()

        cursor.close()
        conn.close()
        return redirect('/consultar_participantes')

    cursor.close()
    conn.close()
    return render_template('registrar_participante.html')

@app.route('/consultar_participantes')
def consultar_participantes():
    """
    Mostrar participantes registrados, con opción a búsqueda.
    """
    busqueda = request.args.get('busqueda', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if busqueda:
        sql = """
            SELECT * FROM participantes
            WHERE nombre LIKE %s OR correo LIKE %s OR telefono LIKE %s OR fecha_registro LIKE %s
        """
        # Usamos %busqueda% para que busque en cualquier parte de la cadena
        like_busqueda = f"%{busqueda}%"
        cursor.execute(sql, (like_busqueda, like_busqueda, like_busqueda, like_busqueda))
    else:
        cursor.execute("SELECT * FROM participantes")

    participantes = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('consultar_participantes.html', participantes=participantes)


# ----------------- Cursos ------------------

@app.route('/registrar_curso', methods=['GET', 'POST'])
def registrar_curso():
    """
    Registrar un nuevo curso con validaciones y selección de categoría.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        descripcion = request.form['descripcion'].strip()
        duracion = request.form.get('duracion', '').strip()
        categoria = request.form.get('categoria')

        errores = []

        # Validaciones básicas
        if not nombre:
            errores.append("El nombre del curso es obligatorio.")
        if not descripcion:
            errores.append("La descripción es obligatoria.")
        if not categoria:
            errores.append("Debe seleccionar una categoría.")

        # Validar categoría existente
        cursor.execute("SELECT id_categoria FROM categorias WHERE id_categoria = %s", (categoria,))
        if not cursor.fetchone():
            errores.append("La categoría seleccionada no es válida.")

        # Validar que no exista otro curso con el mismo nombre
        cursor.execute("SELECT * FROM cursos WHERE nombre = %s", (nombre,))
        if cursor.fetchone():
            errores.append("Ya existe un curso con ese nombre.")

        if errores:
            cursor.execute("SELECT * FROM categorias ORDER BY nombre ASC")
            categorias = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template('registrar_curso.html',
                                   categorias=categorias,
                                   error=' '.join(errores),
                                   nombre=nombre,
                                   descripcion=descripcion,
                                   duracion=duracion,
                                   categoria_seleccionada=categoria)

        cursor.execute(
            "INSERT INTO cursos (nombre, descripcion, duracion, id_categoria) VALUES (%s, %s, %s, %s)",
            (nombre, descripcion, duracion or None, categoria))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/consultar_cursos')

    # GET
    cursor.execute("SELECT * FROM categorias ORDER BY nombre ASC")
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('registrar_curso.html', categorias=categorias)

@app.route('/consultar_cursos')
def consultar_cursos():
    """
    Consultar y listar todos los cursos, con opción de búsqueda por nombre, descripción o categoría.
    """
    buscar = request.args.get('buscar', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if buscar:
        query = """
            SELECT cursos.*, categorias.nombre AS categoria
            FROM cursos
            LEFT JOIN categorias ON cursos.id_categoria = categorias.id_categoria
            WHERE cursos.nombre LIKE %s
               OR cursos.descripcion LIKE %s
               OR categorias.nombre LIKE %s
        """
        valores = (f"%{buscar}%", f"%{buscar}%", f"%{buscar}%")
        cursor.execute(query, valores)
    else:
        query = """
            SELECT cursos.*, categorias.nombre AS categoria
            FROM cursos
            LEFT JOIN categorias ON cursos.id_categoria = categorias.id_categoria
        """
        cursor.execute(query)

    cursos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('consultar_cursos.html', cursos=cursos)


# ----------------- Inscripciones ------------------

@app.route('/inscribir', methods=['GET', 'POST'])
def inscribir():
    """
    Inscribir a un participante en un curso. Evita inscripciones duplicadas.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        id_participante = request.form['id_participante']
        id_curso = request.form['id_curso']
        fecha_inscripcion = date.today()

        # Verificar si ya está inscrito
        cursor.execute("""
            SELECT * FROM inscripciones 
            WHERE id_participante = %s AND id_curso = %s
        """, (id_participante, id_curso))
        ya_inscrito = cursor.fetchone()

        if ya_inscrito:
            flash('El participante ya está inscrito en este curso.', 'warning')
        else:
            cursor.execute("""
                INSERT INTO inscripciones (id_curso, id_participante, fecha)
                VALUES (%s, %s, %s)
            """, (id_curso, id_participante, fecha_inscripcion))
            conn.commit()
            flash('Participante inscrito exitosamente al curso.', 'success')

        cursor.close()
        conn.close()
        return redirect(url_for('inscribir'))

    # Si GET, mostrar lista de participantes y cursos
    cursor.execute("SELECT * FROM participantes")
    participantes = cursor.fetchall()
    cursor.execute("SELECT * FROM cursos")
    cursos = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('inscribir.html', participantes=participantes, cursos=cursos)

@app.route('/consultar_inscripciones')
def consultar_inscripciones():
    """
    Mostrar todas las inscripciones realizadas con información de participantes y cursos.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.id_inscripcion, p.nombre AS participante, c.nombre AS curso, i.fecha
        FROM inscripciones i
        JOIN participantes p ON i.id_participante = p.id_participante
        JOIN cursos c ON i.id_curso = c.id_curso
        ORDER BY i.fecha DESC
    """)
    inscripciones = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('consultar_inscripciones.html', inscripciones=inscripciones)

# ----------------- Funciones auxiliares para cursos y categorías ------------------

def obtener_curso_por_id(id):
    """
    Retorna un curso dado su id.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cursos WHERE id_curso = %s", (id,))
    curso = cursor.fetchone()
    cursor.close()
    conn.close()
    return curso

def obtener_todas_las_categorias():
    """
    Retorna todas las categorías.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM categorias")
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    return categorias


# ----------------- Editar y eliminar cursos ------------------

@app.route('/editar_curso/<int:id>', methods=['GET'])
def editar_curso(id):
    """
    Mostrar formulario para editar un curso dado su id.
    """
    curso = obtener_curso_por_id(id)
    categorias = obtener_todas_las_categorias()
    if curso:
        return render_template('editar_curso.html', curso=curso, categorias=categorias)
    else:
        flash('Curso no encontrado')
        return redirect(url_for('consultar_cursos'))

@app.route('/editar_curso/<int:id>', methods=['POST'])
def actualizar_curso(id):
    """
    Actualizar la información de un curso.
    """
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    duracion = int(request.form['duracion'])
    id_categoria = int(request.form['categoria'])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cursos 
        SET nombre = %s, descripcion = %s, duracion = %s, id_categoria = %s
        WHERE id_curso = %s
    """, (nombre, descripcion, duracion, id_categoria, id))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Curso actualizado exitosamente')
    return redirect(url_for('consultar_cursos'))

@app.route('/eliminar_curso/<int:id>', methods=['POST', 'GET'])
def eliminar_curso(id):
    """
    Elimina un curso dado su id. Si tiene inscripciones, se muestra una advertencia.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM cursos WHERE id_curso = %s", (id,))
        conn.commit()
        flash('Curso eliminado exitosamente.', 'success')
    except IntegrityError:
        flash('No se puede eliminar el curso porque tiene participantes inscritos o dependencias asociadas.', 'warning')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('consultar_cursos'))

# ----------------- Editar y eliminar categorías ------------------

@app.route('/editar_categoria/<int:id>', methods=['GET', 'POST'])
def editar_categoria(id):
    """
    Editar categoría. GET muestra el formulario, POST actualiza.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        nuevo_nombre = request.form['nombre']
        nueva_descripcion = request.form['descripcion']
        cursor.execute("UPDATE categorias SET nombre=%s, descripcion=%s WHERE id_categoria=%s",
                       (nuevo_nombre, nueva_descripcion, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('consultar_categorias'))
    else:
        cursor.execute("SELECT * FROM categorias WHERE id_categoria = %s", (id,))
        categoria = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template('editar_categoria.html', categoria=categoria)

@app.route('/eliminar_categoria/<int:id>')
def eliminar_categoria(id):
    """
    Elimina una categoría dado su id.
    Si tiene cursos asociados, muestra un mensaje de advertencia.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM categorias WHERE id_categoria = %s", (id,))
        conn.commit()
        flash('Categoría eliminada correctamente.', 'success')
    except IntegrityError:
        flash('No se puede eliminar la categoría porque tiene cursos asociados.', 'warning')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('consultar_categorias'))


# ----------------- Editar y eliminar participantes ------------------

@app.route('/editar_participante/<int:id>', methods=['GET', 'POST'])
def editar_participante(id):
    """
    Editar participante. GET muestra formulario, POST actualiza con validaciones.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        correo = request.form['correo'].strip()
        telefono = request.form['telefono'].strip()
        direccion = request.form['direccion'].strip()
        edad = request.form['edad'].strip()
        genero = request.form['genero'].strip()
        ocupacion = request.form['ocupacion'].strip()
        usuario = request.form['usuario'].strip()
        nueva_password = request.form['password'].strip()

        # Validación básica.
        if not nombre or not correo or not telefono:
            cursor.close()
            conn.close()
            return "El nombre, correo electrónico y teléfono son obligatorios.", 400

        # Verificar si el nombre de usuario realmente cambió
        cursor.execute("SELECT usuario FROM participantes WHERE id_participante = %s", (id,))
        usuario_actual = str(cursor.fetchone()['usuario'] or "")

        # Validar que el nuevo nombre de usuario no esté en uso si fue cambiado
        if usuario and usuario != usuario_actual:
            cursor.execute("""
                SELECT id_participante FROM participantes 
                WHERE usuario = %s AND id_participante != %s
            """, (usuario, id))
            resultado = cursor.fetchone()
            print("Resultado de verificación duplicado:", resultado)

            if resultado:
                cursor.close()
                conn.close()
                return "Ese nombre de usuario ya está en uso.", 400

        # Si se proporcionó nueva contraseña, actualizarla
        if nueva_password:
            hashed_password = generate_password_hash(nueva_password)
            cursor.execute("""
                UPDATE participantes SET
                    nombre = %s,
                    correo = %s,
                    telefono = %s,
                    direccion = %s,
                    edad = %s,
                    genero = %s,
                    ocupacion = %s,
                    usuario = %s,
                    password = %s
                WHERE id_participante = %s
            """, (nombre, correo, telefono, direccion, edad, genero, ocupacion, usuario, hashed_password, id))
        else:
            # Sin cambio de contraseña
            cursor.execute("""
                UPDATE participantes SET
                    nombre = %s,
                    correo = %s,
                    telefono = %s,
                    direccion = %s,
                    edad = %s,
                    genero = %s,
                    ocupacion = %s,
                    usuario = %s
                WHERE id_participante = %s
            """, (nombre, correo, telefono, direccion, edad, genero, ocupacion, usuario, id))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/consultar_participantes')

    # GET: Mostrar el formulario con datos actuales
    cursor.execute("SELECT * FROM participantes WHERE id_participante = %s", (id,))
    participante = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('editar_participante.html', participante=participante)

@app.route('/eliminar_participante/<int:id>')
def eliminar_participante(id):
    """
    Elimina un participante dado su id.
    Si tiene inscripciones asociadas, muestra un mensaje de advertencia.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM participantes WHERE id_participante = %s", (id,))
        conn.commit()
        flash('Participante eliminado correctamente.', 'success')
    except IntegrityError:
        flash('No se puede eliminar el participante porque tiene inscripciones asociadas.', 'warning')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('consultar_participantes'))

# ----------------- Editar y eliminar inscripciones ------------------

@app.route('/editar_inscripcion/<int:id>', methods=['GET', 'POST'])
def editar_inscripcion(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Obtener datos del formulario
        id_participante = request.form['id_participante']
        id_curso = request.form['id_curso']
        fecha = request.form['fecha']  # formato 'YYYY-MM-DD'

        # Actualizar registro en la base de datos
        cursor.execute("""
            UPDATE inscripciones 
            SET id_participante = %s, id_curso = %s, fecha = %s
            WHERE id_inscripcion = %s
        """, (id_participante, id_curso, fecha, id))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Inscripción actualizada correctamente.', 'success')
        return redirect(url_for('consultar_inscripciones'))

    # Si es GET, mostrar formulario con datos actuales
    cursor.execute("""
        SELECT * FROM inscripciones WHERE id_inscripcion = %s
    """, (id,))
    inscripcion = cursor.fetchone()

    # También obtenemos todos los participantes y cursos para los select
    cursor.execute("SELECT id_participante, nombre FROM participantes")
    participantes = cursor.fetchall()
    cursor.execute("SELECT id_curso, nombre FROM cursos")
    cursos = cursor.fetchall()

    cursor.close()
    conn.close()

    if inscripcion is None:
        flash('Inscripción no encontrada.', 'danger')
        return redirect(url_for('consultar_inscripciones'))

    return render_template('editar_inscripcion.html',
                           inscripcion=inscripcion,
                           participantes=participantes,
                           cursos=cursos)

@app.route('/eliminar_inscripcion/<int:id>')
def eliminar_inscripcion(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inscripciones WHERE id_inscripcion = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Inscripción eliminada correctamente.', 'success')
    return redirect(url_for('consultar_inscripciones'))

# ----------------- Dashboard ------------------

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total de cursos
    cursor.execute("SELECT COUNT(*) AS total_cursos FROM cursos")
    total_cursos = cursor.fetchone()['total_cursos']

    # Total de participantes
    cursor.execute("SELECT COUNT(*) AS total_participantes FROM participantes")
    total_participantes = cursor.fetchone()['total_participantes']

    # Cursos con más inscripciones
    cursor.execute("""
        SELECT c.nombre, COUNT(i.id_participante) AS total_inscritos
        FROM inscripciones i
        JOIN cursos c ON i.id_curso = c.id_curso
        GROUP BY i.id_curso
        ORDER BY total_inscritos DESC
        LIMIT 5
    """)
    cursos_populares = cursor.fetchall()

    # Distribución de participantes por categoría
    cursor.execute("""
        SELECT cat.nombre AS categoria, COUNT(ins.id_participante) AS inscritos
        FROM inscripciones ins
        JOIN cursos c ON ins.id_curso = c.id_curso
        JOIN categorias cat ON c.id_categoria = cat.id_categoria
        GROUP BY cat.id_categoria
    """)
    distribucion_categorias = cursor.fetchall()

    # Inscripciones mensuales
    cursor.execute("""
        SELECT DATE_FORMAT(fecha, '%Y-%m') AS mes, COUNT(*) AS total
        FROM inscripciones
        GROUP BY mes
        ORDER BY mes
    """)
    inscripciones_mensuales = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('dashboard.html',
                           total_cursos=total_cursos,
                           total_participantes=total_participantes,
                           cursos_populares=cursos_populares,
                           distribucion_categorias=distribucion_categorias,
                           inscripciones_mensuales=inscripciones_mensuales)

# ----------------- Login ------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Buscar usuario en la tabla participantes
        cursor.execute("SELECT * FROM participantes WHERE usuario = %s", (usuario,))
        participante = cursor.fetchone()

        cursor.close()
        conn.close()

        if participante:
            # Verificar la contraseña
            if check_password_hash(participante['password'], password):
                session['usuario'] = participante['usuario']
                session['nombre'] = participante['nombre']
                session['id_participante'] = participante['id_participante']
                return redirect('/')
            else:
                flash('Contraseña incorrecta.', 'error')
        else:
            flash('Usuario no encontrado.', 'error')

        return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)  # Elimina al usuario de la sesión
    return redirect('/')

# ----------------- Exportaciones ------------------

@app.route('/exportar_participantes_excel')
def exportar_participantes_excel():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute('SELECT id_participante, nombre, correo, telefono, direccion, edad, genero, ocupacion, fecha_registro, usuario, password FROM participantes')
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()

    columnas = ['ID', 'Nombre', 'Correo', 'Teléfono', 'Dirección', 'Edad', 'Género', 'Ocupación', 'Fecha Registro', 'Usuario', 'Contraseña']
    df = pd.DataFrame(datos, columns=columnas)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Participantes')
    output.seek(0)

    return send_file(output, download_name='participantes.xlsx', as_attachment=True)

@app.route('/exportar_participantes_pdf')
def exportar_participantes_pdf():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute('SELECT id_participante, nombre, correo, telefono, direccion, edad, genero, ocupacion, fecha_registro, usuario, password FROM participantes')
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()

    columnas = ['ID', 'Nombre', 'Correo', 'Teléfono', 'Dirección', 'Edad', 'Género', 'Ocupación', 'Fecha Registro', 'Usuario', 'Contraseña']

    estilos = getSampleStyleSheet()
    estilo_celda = estilos["Normal"]
    estilo_celda.fontSize = 6
    estilo_celda.leading = 7

    tabla_datos = [columnas]  # encabezado sin Paragraph

    for fila in datos:
        fila_parrafos = [Paragraph(str(campo), estilo_celda) for campo in fila]
        tabla_datos.append(fila_parrafos)

    col_widths = [
        0.8*cm,   # ID
        3.2*cm,   # Nombre
        3.5*cm,   # Correo
        1.7*cm,   # Teléfono
        5*cm,     # Dirección
        0.9*cm,   # Edad
        1.5*cm,   # Género
        1.8*cm,   # Ocupación
        1.9*cm,   # Fecha registro
        2*cm,     # Usuario
        5*cm      # Contraseña
    ]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

    t = Table(tabla_datos, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
    ]))

    doc.build([t])
    buffer.seek(0)
    return send_file(buffer, download_name='participantes.pdf', as_attachment=True)

@app.route('/exportar_inscripciones_excel')
def exportar_inscripciones_excel():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute('SELECT id_inscripcion, id_curso, id_participante, fecha FROM inscripciones')
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()

    columnas = ['ID Inscripción', 'ID Curso', 'ID Participante', 'Fecha']
    df = pd.DataFrame(datos, columns=columnas)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Inscripciones')
    output.seek(0)

    return send_file(output, download_name='inscripciones.xlsx', as_attachment=True)

@app.route('/exportar_inscripciones_pdf')
def exportar_inscripciones_pdf():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute('SELECT id_inscripcion, id_curso, id_participante, fecha FROM inscripciones')
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()

    columnas = ['ID Inscripción', 'ID Curso', 'ID Participante', 'Fecha']
    tabla = [columnas] + list(datos)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    t = Table(tabla)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    doc.build([t])
    buffer.seek(0)

    return send_file(buffer, download_name='inscripciones.pdf', as_attachment=True)

@app.route('/exportar_cursos_excel')
def exportar_cursos_excel():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute('SELECT id_curso, nombre, descripcion, duracion, id_categoria FROM cursos')
    cursos = cursor.fetchall()
    cursor.close()
    conexion.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Cursos"

    encabezados = ['ID', 'Nombre', 'Descripción', 'Duración', 'ID Categoría']
    ws.append(encabezados)

    for curso in cursos:
        ws.append(curso)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name='cursos.xlsx', as_attachment=True)

@app.route('/exportar_cursos_pdf')
def exportar_cursos_pdf():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute('SELECT id_curso, nombre, descripcion, duracion, id_categoria FROM cursos')
    cursos = cursor.fetchall()
    cursor.close()
    conexion.close()

    columnas = ['ID', 'Nombre', 'Descripción', 'Duración', 'ID Categoría']

    estilos = getSampleStyleSheet()
    estilo_celda = estilos["Normal"]
    estilo_celda.fontSize = 6
    estilo_celda.leading = 7

    tabla_datos = [columnas]
    for curso in cursos:
        fila_parrafos = [Paragraph(str(c), estilo_celda) for c in curso]
        tabla_datos.append(fila_parrafos)

    col_widths = [
        1.2*cm,   # ID
        3*cm,     # Nombre
        6*cm,     # Descripción
        2*cm,     # Duración
        4*cm,     # Asignatura
        2.5*cm    # ID Categoría
    ]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

    t = Table(tabla_datos, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
    ]))

    doc.build([t])
    buffer.seek(0)
    return send_file(buffer, download_name='cursos.pdf', as_attachment=True)


# ----------------- Página principal ------------------

@app.route('/')
def index():
    """
    Página de inicio de la aplicación.
    """
    return render_template('index.html')


# ----------------- Configuración y arranque ------------------

if __name__ == '__main__':
    app.secret_key = 'tu_clave_secreta_aqui'
    app.run(debug=True)
