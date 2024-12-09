from flask import Flask, request, jsonify, send_from_directory, session
from sqlalchemy.exc import IntegrityError
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin  # Asegúrate de tener flask_cors instalado
from werkzeug.security import check_password_hash
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory, abort
import base64
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from datetime import datetime
import re
from models import TarjetaCredito
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import qrcode
import random
import string
from datetime import datetime
from io import BytesIO
from flask import send_file
from random import randint 






# Instancia de la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos para Laragon (MySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/glamshop'  # Cambia las credenciales si es necesario
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'tu_clave_secreta_aqui'


# Configuración de la carpeta de subida con la ruta completa
app.config['UPLOAD_FOLDER'] = 'C:\\Users\\lxusb\\OneDrive\\Escritorio\\GLAMDEFINITIVO\\productos'

# Inicializa SQLAlchemy
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Habilitar CORS en la aplicación Flask
CORS(app)
CORS(app, resources={r"/ubicaciones/*": {"origins": "http://localhost:4200"}})
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})
app.secret_key = 'tu_clave_secreta_super_segura'  # Configuración de la clave secreta



# Modelo de la tabla 'productos'
class Producto(db.Model):
    __tablename__ = 'producto'  # Nombre de la tabla coincide con la base de datos
    id = db.Column(db.Integer, primary_key=True)
    nombre_producto = db.Column(db.String(80), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    imagen = db.Column(db.String(120), nullable=False)

# Modelo de la tabla usuarios
class Usuario(db.Model):
    __tablename__ = 'usuarios'  # Nombre de la tabla coincide con la base de datos
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(15), nullable=True)
    contrasena = db.Column(db.String(255), nullable=False)  # Se almacena la contraseña como un hash
    email = db.Column(db.String(100), unique=True, nullable=False)
    rol = db.Column(db.String(50), nullable=False, default='user')

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'telefono': self.telefono,
            'contrasena': self.contrasena,
            'email': self.email,
            'rol': self.rol
        }

# --------------------- RUTAS DE USUARIOS ---------------------

# Ruta para el inicio de sesión
@app.route('/login', methods=['POST', 'OPTIONS'])
@cross_origin()
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Datos no proporcionados'}), 400

        email = data.get('email')
        contrasena = data.get('contrasena')

        if not email or not contrasena:
            return jsonify({'message': 'Correo electrónico y contraseña requeridos'}), 400

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario:
            if usuario.contrasena == contrasena:  # Comparar contraseñas (deberían estar hasheadas en un entorno real)
                # Guardar el user_id en la sesión
                session['user_id'] = usuario.id  # <--- Línea añadida para guardar el user_id en la sesión
                return jsonify({
                    'token': 'example_token',
                    'nombre': usuario.nombre,
                    'rol': usuario.rol,
                    'message': 'Inicio de sesión exitoso'
                }), 200
            else:
                return jsonify({'message': 'Credenciales inválidas'}), 401
        else:
            return jsonify({'message': 'Credenciales inválidas'}), 401

    except Exception as e:
        return jsonify({'message': 'Error en el servidor'}), 500


# Ruta para registrar un nuevo usuario
@app.route('/registrar', methods=['POST'])
@cross_origin()
def registrar_usuario():
    try:
        # Obtener los datos del formulario
        datos = request.get_json()
        email = datos.get('email')
        nombre = datos.get('nombre')
        telefono = datos.get('telefono')
        contrasena = datos.get('contrasena')

        nuevo_usuario = Usuario(email=email, nombre=nombre, telefono=telefono, contrasena=contrasena)

        db.session.add(nuevo_usuario)
        db.session.commit()

        return jsonify({'mensaje': 'Usuario registrado exitosamente'}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'El correo electrónico ya está en uso'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --------------------- RUTAS DE PRODUCTOS ---------------------

# Ruta para obtener todos los productos
@app.route('/productos', methods=['GET'])
@cross_origin()
def obtener_productos():
    productos = Producto.query.all()
    resultado = [
        {
            "id": producto.id,
            "nombre_producto": producto.nombre_producto,
            "precio": producto.precio,
            "descripcion": producto.descripcion,
            "categoria": producto.categoria,
            "imagen": f'http://127.0.0.1:5000/api/imagenes/{producto.imagen}'
        } for producto in productos
    ]
    return jsonify(resultado), 200

# --------------------- NUEVA RUTA: BUSCAR PRODUCTOS ---------------------

@app.route('/productos/buscar', methods=['GET'])
@cross_origin()
def buscar_productos():
    termino = request.args.get('q', '')

    productos = Producto.query.filter(Producto.nombre_producto.ilike(f"%{termino}%")).all()

    resultado = [
        {
            "id": producto.id,
            "nombre_producto": producto.nombre_producto,
            "precio": producto.precio,
            "descripcion": producto.descripcion,
            "categoria": producto.categoria,
            "imagen": f'http://127.0.0.1:5000/api/imagenes/{producto.imagen}'
        } for producto in productos
    ]

    return jsonify(resultado), 200

# --------------------- RUTA ACTUALIZAR PRODUCTOS ---------------------

@app.route('/productos/<int:producto_id>', methods=['PUT', 'OPTIONS'])
@cross_origin()
def actualizar_producto(producto_id):
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'Preflight check passed'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        return response

    try:
        producto = Producto.query.get(producto_id)

        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        # Verificar que la imagen haya sido enviada (si aplica)
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen.filename != '':
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], imagen.filename)
                imagen.save(imagen_path)
                producto.imagen = imagen.filename

        # Actualizar los datos del producto
        nombre_producto = request.form.get('nombre_producto')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        categoria = request.form.get('categoria')

        if nombre_producto:
            producto.nombre_producto = nombre_producto
        if precio:
            producto.precio = float(precio)
        if descripcion:
            producto.descripcion = descripcion
        if categoria:
            producto.categoria = categoria

        db.session.commit()

        return jsonify({"message": "Producto actualizado exitosamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --------------------- RUTA PARA SERVIR IMÁGENES ---------------------

@app.route('/api/imagenes/<path:filename>', methods=['GET'])
@cross_origin()
def obtener_imagen(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)





@app.route('/registrarProducto', methods=['POST'])
def registrar_producto():
    try:
        # Validar y obtener los datos del producto
        producto_json = request.form.get('producto')
        if not producto_json:
            return jsonify({'error': 'No se proporcionaron datos del producto'}), 400

        # Convertir el JSON del producto a un diccionario de Python
        import json
        producto_data = json.loads(producto_json)

        # Cargar el archivo
        file = request.files.get('archivo')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            return jsonify({'error': 'Archivo no válido o faltante'}), 400

        # Crear y guardar el producto en la base de datos
        nuevo_producto = Producto(
            nombre_producto=producto_data.get('nombre_producto'),
            precio=float(producto_data.get('precio', 0)),
            descripcion=producto_data.get('descripcion'),
            categoria=producto_data.get('categoria'),
            imagen=filename
        )

        db.session.add(nuevo_producto)
        db.session.commit()

        return jsonify({
            'message': 'Producto registrado con éxito',
            'producto': {
                'id': nuevo_producto.id,
                'nombre_producto': nuevo_producto.nombre_producto,
                'precio': nuevo_producto.precio,
                'descripcion': nuevo_producto.descripcion,
                'categoria': nuevo_producto.categoria,
                'imagen': nuevo_producto.imagen
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Función para validar las extensiones permitidas
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/productos/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    try:
        producto = Producto.query.get(id)
        if not producto:
            return jsonify({'mensaje': 'Producto no encontrado'}), 404

        db.session.delete(producto)
        db.session.commit()

        return jsonify({'mensaje': 'Producto eliminado correctamente'}), 200

    except Exception as e:
        print(f"Error al eliminar el producto: {e}")
        return jsonify({'mensaje': 'Ocurrió un error al eliminar el producto'}), 500











# Endpoint para obtener todos los usuarios
@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    usuarios = Usuario.query.all()
    usuarios_json = [{'id': usuario.id, 'nombre': usuario.nombre, 'email': usuario.email, 'rol': usuario.rol, 'telefono': usuario.telefono} for usuario in usuarios]
    return jsonify(usuarios_json), 200

# Endpoint para eliminar un usuario
@app.route('/usuarios/<int:id>', methods=['DELETE'])
def eliminar_usuario(id):
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404
    try:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({'mensaje': 'Usuario eliminado correctamente'}), 200
    except Exception as e:
        return jsonify({'mensaje': f'Error al eliminar el usuario: {e}'}), 500

# Endpoint para actualizar un usuario
@app.route('/usuarios/<int:id>', methods=['PUT'])
def actualizar_usuario(id):
    datos = request.get_json()
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404
    try:
        usuario.nombre = datos.get('nombre', usuario.nombre)
        usuario.email = datos.get('email', usuario.email)
        usuario.rol = datos.get('rol', usuario.rol)
        usuario.telefono = datos.get('telefono', usuario.telefono)
        db.session.commit()
        return jsonify({'mensaje': 'Usuario actualizado correctamente'}), 200
    except Exception as e:
        return jsonify({'mensaje': f'Error al actualizar el usuario: {e}'}), 500




#DOCIENTOS
@app.route('/docientos', methods=['GET'])
def obtener_docientos():
    try:
        # Consulta a la base de datos para obtener todos los registros de la tabla `producto`
        docientos = Producto.query.filter(Producto.precio < 200).all()
        
        # Convertir los registros a un array de diccionarios
        resultado = [
            {
                'id': producto.id,
                'nombre': producto.nombre_producto,
                'precio': producto.precio,
                'descripcion': producto.descripcion,
                'categoria': producto.categoria,
                'imagen': f'http://127.0.0.1:5000/api/imagenes/{producto.imagen}'
            }
            for producto in docientos
        ]
        
        # Devolver la respuesta en formato JSON
        return jsonify(resultado)
        
    except Exception as e:
        # Devolver un error si ocurre algún problema
        return jsonify({"error": str(e)}), 500
    
    
    
    
    
    
    
@app.route('/productos0909', methods=['GET'])
def obtener_productos_0909():
    productos = Producto.query.all()
    productos_json = [
        {
            'id': p.id,
            'nombre_producto': p.nombre_producto,
            'precio': p.precio,
            'descripcion': p.descripcion,
            'categoria': p.categoria,
            'imagen': f"http://localhost:5000/api/imagenes{p.imagen}"  # Ruta accesible desde el frontend
        }
        for p in productos
    ]
    return jsonify(productos_json)



# Definir el modelo Carrito
class Carrito(db.Model):
    __tablename__ = 'carritos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)

    usuario = db.relationship('Usuario', backref=db.backref('carritos', lazy=True))
    producto = db.relationship('Producto', backref=db.backref('carritos', lazy=True))



#carrito


@app.route('/carrito/<int:usuario_id>', methods=['POST'])
def agregar_al_carrito(usuario_id):
    data = request.get_json()
    producto_id = data.get('producto_id')
    cantidad = data.get('cantidad')

    # Validación
    producto = Producto.query.get(producto_id)
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404

    # Verificar si el producto ya está en el carrito
    item_carrito = Carrito.query.filter_by(usuario_id=usuario_id, producto_id=producto_id).first()
    if item_carrito:
        item_carrito.cantidad += cantidad  # Actualizar cantidad si ya existe
    else:
        item_carrito = Carrito(usuario_id=usuario_id, producto_id=producto_id, cantidad=cantidad)
        db.session.add(item_carrito)
    
    db.session.commit()
    return jsonify({'mensaje': 'Producto agregado al carrito exitosamente'})




@app.route('/carrito/<int:producto_id>', methods=['DELETE'])
def eliminar_producto_carrito(producto_id):
    try:
        # Buscar el registro en la tabla `carritos` donde `producto_id` coincide
        carrito = Carrito.query.filter_by(producto_id=producto_id).first()

        if not carrito:
            return jsonify({'error': 'Producto no encontrado en el carrito'}), 404

        # Eliminar el registro del carrito
        db.session.delete(carrito)
        db.session.commit()
        return jsonify({'mensaje': 'Producto eliminado con éxito del carrito'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
# Endpoint para obtener el carrito
@app.route('/carrito', methods=['GET'])
def obtener_carrito():
    try:
        # Obtener todos los productos en el carrito
        carrito_items = Carrito.query.all()
        resultado = [
            {
                'id': item.producto.id,
                'nombre_producto': item.producto.nombre_producto,
                'precio': item.producto.precio,
                'descripcion': item.producto.descripcion,
                'categoria': item.producto.categoria,
              'imagen': f"http://localhost:5000/api/imagenes/{item.producto.imagen.lstrip('/')}",
# Adaptar la ruta de la imagen
                'cantidad': item.cantidad
            }
            for item in carrito_items
        ]
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
    
@app.route('/api/imagenes/<path:filename>', methods=['GET'])
def enviar_imagen(filename):
    directorio_imagenes = os.path.join(os.getcwd(), 'imagenes')  # Cambia esto a la ruta correcta
    
    # Verificar si el archivo existe antes de enviarlo
    if not os.path.exists(os.path.join(directorio_imagenes, filename)):
        abort(404)  # Si el archivo no existe, enviar un error 404

    return send_from_directory(directorio_imagenes, filename)
    

    
    
@app.route('/carrito/<int:usuario_id>', methods=['POST'])
def agregar_producto_al_carrito(usuario_id):
    try:
        data = request.get_json()
        producto_id = data.get('producto_id')
        cantidad = data.get('cantidad', 1)

        nuevo_item = Carrito(usuario_id=usuario_id, producto_id=producto_id, cantidad=cantidad)
        db.session.add(nuevo_item)
        db.session.commit()

        return jsonify({"mensaje": "Producto agregado al carrito"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/carrito/<int:producto_id>', methods=['PUT'])
def actualizar_cantidad(producto_id):
    try:
        # Obtener datos del request
        data = request.get_json()
        nueva_cantidad = data.get('cantidad')

        # Validar que nueva_cantidad es válida
        if not nueva_cantidad or not isinstance(nueva_cantidad, int) or nueva_cantidad < 1:
            return jsonify({"error": "Cantidad inválida"}), 400

        # Buscar el producto en el carrito
        item_carrito = Carrito.query.filter_by(producto_id=producto_id).first()
        
        if item_carrito:
            # Actualizar la cantidad en la base de datos
            item_carrito.cantidad = nueva_cantidad
            db.session.commit()
            return jsonify({"mensaje": "Cantidad actualizada con éxito"}), 200
        else:
            return jsonify({"error": "Producto no encontrado en el carrito"}), 404

    except Exception as e:
        # Manejar cualquier excepción que ocurra y devolver un error 500
        return jsonify({"error": str(e)}), 500
    
    
    
    #todi

    # Ruta para obtener todos los productos

@app.route('/imagenes/<path:nombre_imagen>', methods=['GET'])
def obtener_imagen_por_nombre(nombre_imagen):
    # Especifica la ruta completa a la carpeta "imagenes"
    ruta_completa = 'C:\\Users\\lxusb\\OneDrive\\Escritorio\\GLAMDEFINITIVO\\productos'
    return send_from_directory(ruta_completa, nombre_imagen)

# Ruta para obtener todos los productos
@app.route('/', methods=['GET'])
def obtener_todo():
    productos = Producto.query.all()  # Asumiendo que estás utilizando una base de datos y un ORM como SQLAlchemy
    productos_lista = []

    for p in productos:
        # Construimos la URL para cada imagen de producto
        url_imagen = f"http://localhost:5000/imagenes/{p.imagen}"

        productos_lista.append({
            'id': p.id,
            'nombre_producto': p.nombre_producto,
            'precio': p.precio,
            'descripcion': p.descripcion,
            'categoria': p.categoria,
            'imagen': url_imagen  # Aquí se hace referencia a la URL de la imagen
        })

    return jsonify(productos_lista)




#tarjeta
# Modelo de la base de datos
class PagoTarjeta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titular = db.Column(db.String(100))
    numero_tarjeta = db.Column(db.String(16))
    fecha_expiracion = db.Column(db.String(5))
    cvv = db.Column(db.String(3))

    def __init__(self, titular, numero_tarjeta, fecha_expiracion, cvv):
        self.titular = titular
        self.numero_tarjeta = numero_tarjeta
        self.fecha_expiracion = fecha_expiracion
        self.cvv = cvv

# Esquema de Marshmallow
class PagoTarjetaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PagoTarjeta

# Inicializar el esquema
pago_tarjeta_schema = PagoTarjetaSchema()

@app.route('/pagar', methods=['POST'])
def procesar_pago():
    try:
        # Obtener los datos de la tarjeta del request
        datos = request.get_json()
        print('Datos recibidos:', datos)
        
        titular = datos.get('titular')
        print('Titular:', titular)
        
        numero_tarjeta = datos.get('numero_tarjeta')
        print('Número de tarjeta:', numero_tarjeta)
        
        fecha_expiracion = datos.get('fecha_expiracion')
        print('Fecha de expiración:', fecha_expiracion)
        
        cvv = datos.get('cvv')
        print('CVV:', cvv)

        # Crear una nueva instancia de PagoTarjeta
        nueva_tarjeta = PagoTarjeta(titular, numero_tarjeta, fecha_expiracion, cvv)

        # Guardar en la base de datos
        print('Añadiendo tarjeta a la sesión de base de datos...')
        db.session.add(nueva_tarjeta)
        print('Guardando los cambios en la base de datos...')
        db.session.commit()

        # Serializar y devolver la respuesta con el nuevo objeto
        result = pago_tarjeta_schema.dump(nueva_tarjeta)
        return jsonify(result), 201

    except db.exc.SQLAlchemyError as db_err:
        print('Error de la base de datos:', str(db_err))
        return jsonify({'error': 'Error al interactuar con la base de datos', 'details': str(db_err)}), 400
    except Exception as e:
        print('Error ocurrido:', str(e))
        return jsonify({'error': str(e)}), 400



#TABLA TARJETA

# Esquema de Marshmallow utilizando SQLAlchemyAutoSchema
class PagoTarjetaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PagoTarjeta
        load_instance = True

# Inicializar el esquema
pago_tarjeta_schema = PagoTarjetaSchema()
pagos_tarjeta_schema = PagoTarjetaSchema(many=True)

# Ruta para obtener todas las tarjetas
@app.route('/tarjetas', methods=['GET'])
def obtener_tarjetas():
    todas_tarjetas = PagoTarjeta.query.all()
    result = pagos_tarjeta_schema.dump(todas_tarjetas)
    return jsonify(result), 200

# Ruta para eliminar una tarjeta por ID
@app.route('/tarjetas/<int:id>', methods=['DELETE'])
def eliminar_tarjeta(id):
    tarjeta = PagoTarjeta.query.get(id)
    if not tarjeta:
        return jsonify({'error': 'Tarjeta no encontrada'}), 404
    try:
        db.session.delete(tarjeta)
        db.session.commit()
        return jsonify({'message': 'Tarjeta eliminada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': 'Error al eliminar la tarjeta', 'details': str(e)}), 400

# Ruta para editar una tarjeta
@app.route('/tarjetas/<int:id>', methods=['PUT'])
def editar_tarjeta(id):
    tarjeta = PagoTarjeta.query.get(id)
    if not tarjeta:
        return jsonify({'error': 'Tarjeta no encontrada'}), 404
    try:
        datos = request.get_json()
        tarjeta.titular = datos.get('titular', tarjeta.titular)
        tarjeta.numero_tarjeta = datos.get('numero_tarjeta', tarjeta.numero_tarjeta)
        tarjeta.fecha_expiracion = datos.get('fecha_expiracion', tarjeta.fecha_expiracion)
        tarjeta.cvv = datos.get('cvv', tarjeta.cvv)
        db.session.commit()
        return pago_tarjeta_schema.jsonify(tarjeta), 200
    except Exception as e:
        return jsonify({'error': 'Error al actualizar la tarjeta', 'details': str(e)}), 400
    
# Ruta para eliminar una tarjeta
@app.route('/tarjetas/<int:id>', methods=['DELETE'])
def eliminar_tarjeta_por_id(id):
    tarjeta = PagoTarjeta.query.get(id)
    if not tarjeta:
        return jsonify({'error': 'Tarjeta no encontrada'}), 404
    try:
        db.session.delete(tarjeta)
        db.session.commit()
        return jsonify({'message': 'Tarjeta eliminada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': 'Error al eliminar la tarjeta', 'details': str(e)}), 400





#UBICACION
# Definición del modelo de la tabla ubicacion
class Ubicacion(db.Model):
    __tablename__ = 'ubicacion' 
    id = db.Column(db.Integer, primary_key=True)
    codigo_postal = db.Column(db.String(10), nullable=False)
    colonia = db.Column(db.String(100), nullable=False)
    numero_exterior = db.Column(db.String(20), nullable=False)
    calle = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)

@app.route('/ubicacion', methods=['POST'])
def submit_ubicacion():
    data = request.get_json()
    try:
        nueva_ubicacion = Ubicacion(
            codigo_postal=data['codigo_postal'],
            colonia=data['colonia'],
            numero_exterior=data['numero_exterior'],
            calle=data['calle'],
            descripcion=data.get('descripcion', '')
        )
        db.session.add(nueva_ubicacion)
        db.session.commit()
        return jsonify({'message': 'Ubicación guardada con éxito'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400







#EDITAR UBICACION
# Ruta para obtener todas las ubicaciones
@app.route('/ubicaciones', methods=['GET'])
def obtener_ubicaciones():
    ubicaciones = Ubicacion.query.all()
    return jsonify([{
        'id': u.id,
        'codigo_postal': u.codigo_postal,
        'colonia': u.colonia,
        'numero_exterior': u.numero_exterior,
        'calle': u.calle,
        'descripcion': u.descripcion
    } for u in ubicaciones])

# Ruta para obtener una ubicación por ID
@app.route('/ubicaciones/<int:id>', methods=['GET'])
def obtener_ubicacion(id):
    ubicacion = Ubicacion.query.get_or_404(id)
    return jsonify({
        'id': ubicacion.id,
        'codigo_postal': ubicacion.codigo_postal,
        'colonia': ubicacion.colonia,
        'numero_exterior': ubicacion.numero_exterior,
        'calle': ubicacion.calle,
        'descripcion': ubicacion.descripcion
    })

# Ruta para crear una nueva ubicación
@app.route('/ubicaciones', methods=['POST'])
def crear_ubicacion():
    data = request.json
    nueva_ubicacion = Ubicacion(
        codigo_postal=data['codigo_postal'],
        colonia=data['colonia'],
        numero_exterior=data['numero_exterior'],
        calle=data['calle'],
        descripcion=data['descripcion']
    )
    db.session.add(nueva_ubicacion)
    db.session.commit()
    return jsonify({'message': 'Ubicación creada con éxito'}), 201

# Ruta para actualizar una ubicación existente
@app.route('/ubicaciones/<int:id>', methods=['PUT'])
def actualizar_ubicacion(id):
    data = request.json
    ubicacion = Ubicacion.query.get_or_404(id)

    ubicacion.codigo_postal = data.get('codigo_postal', ubicacion.codigo_postal)
    ubicacion.colonia = data.get('colonia', ubicacion.colonia)
    ubicacion.numero_exterior = data.get('numero_exterior', ubicacion.numero_exterior)
    ubicacion.calle = data.get('calle', ubicacion.calle)
    ubicacion.descripcion = data.get('descripcion', ubicacion.descripcion)

    db.session.commit()
    return jsonify({'message': 'Ubicación actualizada con éxito'})




# Ruta para eliminar una ubicación
@app.route('/ubicaciones/<int:id>', methods=['DELETE'])
def eliminar_ubicacion(id):
    ubicacion = Ubicacion.query.get_or_404(id)
    db.session.delete(ubicacion)
    db.session.commit()
    return jsonify({'message': 'Ubicación eliminada con éxito'})







#DASH
# Endpoint para el dashboard
@app.route('/api/dashboard', methods=['GET'])
def obtener_dashboard():
    try:
        total_productos = Producto.query.count()
        total_pagos = PagoTarjeta.query.count()
        total_ubicaciones = Ubicacion.query.count()
        total_usuarios = Usuario.query.count()

        return jsonify({
            'productos': total_productos,
            'pagos': total_pagos,
            'ubicaciones': total_ubicaciones,
            'usuarios': total_usuarios
        }), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener los datos', 'message': str(e)}), 500

# Ruta para verificar el estado del servidor
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Servidor funcionando correctamente'}), 200




#QR
@app.route('/user', methods=['GET'])
def get_user():
    try:
        # Obtener el user_id desde los argumentos de la URL
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({"error": "El parámetro user_id es requerido"}), 400

        # Consultar el usuario en la tabla usuarios
        user = Usuario.query.get(user_id)
        if not user:
            return jsonify({"error": f"Usuario con ID {user_id} no encontrado"}), 404

        return jsonify({
            "id": user.id,
            "nombre": user.nombre,
            "email": user.email,
            "telefono": user.telefono
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500



## Obtener productos del carrito del usuario autenticado
@app.route('/cart', methods=['GET'])
def get_cart():
    try:
        # Obtener el user_id desde los argumentos de la URL
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({"error": "El parámetro user_id es requerido"}), 400

        # Consultar los items del carrito relacionados con el usuario
        carrito_items = Carrito.query.filter_by(usuario_id=user_id).all()
        if not carrito_items:
            return jsonify({"error": f"No hay productos en el carrito para el usuario con ID {user_id}"}), 404

        productos = []
        total_a_pagar = 0  # Inicializar total

        for item in carrito_items:
            producto = Producto.query.get(item.producto_id)
            if producto:
                subtotal = producto.precio * item.cantidad
                total_a_pagar += subtotal  # Sumar al total
                productos.append({
                    "id": producto.id,
                    "nombre_producto": producto.nombre_producto,
                    "precio": producto.precio,
                    "cantidad": item.cantidad,
                    "subtotal": subtotal
                })

        return jsonify({
            "productos": productos,
            "total_a_pagar": total_a_pagar  # Agregar el total al carrito
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500





## Obtener ubicaciones del usuario autenticado
@app.route('/ubicacion', methods=['GET'])
def get_ubicaciones():
    ubicaciones = Ubicacion.query.all()
    if not ubicaciones:
        return jsonify({"error": "No se encontraron ubicaciones"}), 404

    return jsonify([
        {
            "id": ubicacion.id,
            "codigo_postal": ubicacion.codigo_postal,
            "colonia": ubicacion.colonia,
            "calle": ubicacion.calle,
            "numero_exterior": ubicacion.numero_exterior,
            "descripcion": ubicacion.descripcion
        } for ubicacion in ubicaciones
    ])


@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:
        data = request.get_json()
        if not data or 'ubicacion_id' not in data:
            return jsonify({"error": "Faltan datos necesarios"}), 400

        ubicacion_id = data['ubicacion_id']
        
        # Genera un código aleatorio de orden
        codigo_orden = f"ORD-{randint(1000, 9999)}"

        # Obtener datos adicionales del usuario y productos
        user_id = 1  # ID del usuario autenticado, se debe ajustar según tu lógica
        user = Usuario.query.get(user_id)
        carrito_items = Carrito.query.filter_by(usuario_id=user_id).all()

        productos = []
        total_a_pagar = 0  # Inicializar total

        for item in carrito_items:
            producto = Producto.query.get(item.producto_id)
            if producto:
                subtotal = producto.precio * item.cantidad
                total_a_pagar += subtotal  # Sumar al total
                productos.append({
                    "producto": producto.nombre_producto,
                    "cantidad": item.cantidad,
                    "precio": producto.precio,
                    "subtotal": subtotal
                })

        # Datos para incluir en el QR
        qr_data = {
            "orden": codigo_orden,
            "ubicacion_id": ubicacion_id,
            "usuario": {
                "nombre": user.nombre,
                "email": user.email,
                "telefono": user.telefono
            },
            "productos": productos,
            "total_a_pagar": total_a_pagar  # Agregar el total al QR
        }

        # Generar el QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Guardar la imagen en memoria
        buffer = BytesIO()
        img.save(buffer, 'PNG')
        buffer.seek(0)

        # Retornar la imagen como archivo descargable
        return send_file(buffer, mimetype='image/png', as_attachment=True, download_name=f"{codigo_orden}.png")
    except Exception as e:
        print(f"Error al generar el QR: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500




# Punto de entrada principal de la aplicación
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, host='127.0.0.1', port=5000)
