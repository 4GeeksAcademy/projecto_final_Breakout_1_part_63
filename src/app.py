"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from flask_cors import CORS
from functools import wraps
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError
from api.commands import setup_commands
from api.admin import setup_admin
from api.routes import api
from api.models import db
from api.models import Students_Group, Group, Todo, Submission, Status, User, Reading
from api.utils import APIException, generate_sitemap
from flask_migrate import Migrate
from flask import Flask, request, jsonify, url_for, send_from_directory, session, redirect
import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
# from flask_swagger import swagger
# from models import Person

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CLIENT_SECRETS_FILE = "google_credentials/client_secret.json"
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events"
]


def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"msg": "Acceso no autorizado"}), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper


def get_calendar_service():
    token_path = "google_credentials/token.json"
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds:
        raise Exception(
            "Google no está conectado. Primero hacé /google/login y completá el consentimiento.")

    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../dist/')
app = Flask(__name__)
app.secret_key = "super-secret-key"
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
jwt = JWTManager(app)
app.url_map.strict_slashes = False

CORS(app)

# database condiguration
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

# add the admin
setup_admin(app)

# add the admin
setup_commands(app)

# Add all endpoints form the API with a "api" prefix
print(">>> Registrando blueprint API")
app.register_blueprint(api, url_prefix='/api')

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

# any other endpoint will try to serve it like a static file


@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # avoid cache memory
    return response


@app.route('/prueba', methods=['GET'])
def prueba():
    users = User.query.all()
    return jsonify([user.serialize() for user in users]), 200
# MOSTRAR LECTURAS


@app.route('/readings', methods=['GET'])
def get_all_readings():
    readings = Reading.query.all()
    readings_serialized = []
    for reading in readings:
        readings_serialized.append(reading.serialize())
    return ({'Tus lecturas pendientes': readings})

# CREAR LECTURAS POR PROFESOR


@app.route('/readings/create', methods=['POST'])
def create_new_reading():
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({'msg': 'Necesitas llenar el body'}), 400
    if 'title' not in body:
        return jsonify({'msg': 'Necesitas poner un titulo a la lectura'}), 400
    if 'content' not in body:
        return jsonify({'msg': 'Necesitas agregar contenido'}),400
    if 'teacher_id' not in body:
        return jsonify({'msg': 'Necesitas agregar teacher_id'}),400
    if 'group_id' not in body:
        return jsonify({'msg': 'Necesitas agregar group_id'}),400
    new_reading = Reading()
    new_reading.title = body['title']
    new_reading.content = body['content']
    new_reading.teacher_id = body['teacher_id']
    new_reading.group_id = body['group_id']
    db.session.add(new_reading)
    db.session.commit()

    return jsonify({'msg': f'lectura {new_reading.title}agregada'})


# MODIFICAR LECTURA
@app.route('/editreading/<int:reading_id>', methods=['PUT'])
def edit_reading(reading_id):
    reading = Reading.query.get(reading_id)
    if reading is None:
        return jsonify({'msg': f'Lectura {reading_id} no encontrada'}), 404

    body = request.get_json(silent=True)
    if 'title' in body:
        reading.title = body['title']
    if 'content' in body:
        reading.content = body['content']
    db.session.commit()

    return jsonify({'msg': f'Lectura {reading.name} actualizada'}), 200

# ELIMINAR READING


@app.route('/deletereading/<int:reading_id>', methods=['DELETE'])
def delete_reading(reading_id):
    reading = Reading.query.get(reading_id)
    if reading is None:
        return jsonify({'msg': f'Lectura {reading_id} no encontrada'}), 404

    db.session.delete(reading)
    db.session.commit()

    return jsonify(f'Se ha eliminado correctamente la lectura {reading.title} '), 200


#                  ENDPOINT REGISTER


@app.route("/register", methods=["POST"])
def register():
    try:
        body = request.get_json(silent=True)

        if not body:
            return jsonify({"msg": "Debes enviar información en el body"}), 400

        required_fields = ["email", "password", "name"]
        for field in required_fields:
            if field not in body:
                return jsonify({"msg": f"El campo {field} es obligatorio"}), 400

        if User.query.filter_by(email=body["email"]).first():
            return jsonify({"msg": "Este email ya está en uso"}), 409

        new_user = User(
            email=body["email"],
            password=body["password"],
            name=body["name"],
            role="STUDENT",
            is_active=True
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"msg": "Estudiante registrado correctamente"}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Error de integridad en la base de datos"}), 409

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "msg": "Error interno del servidor",
            "error": str(e)
        }), 500

#             ENDPOINT LOGIN


@app.route("/login", methods=["POST"])
def login():
    try:
        body = request.get_json(silent=True)

        if body is None:
            return jsonify({'msg': 'Debes enviar información en el body'}), 400

        if 'email' not in body or 'password' not in body:
            return jsonify({'msg': 'Email y password son obligatorios'}), 400

        user = User.query.filter_by(email=body['email']).first()

        if not user or user.password != body['password']:
            return jsonify({'msg': 'Credenciales incorrectas'}), 401

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "role": user.role
            }
        )

        return jsonify({
            "access_token": access_token,
            "role": user.role
        }), 200

    except Exception as e:
        return jsonify({
            'msg': 'Error interno del servidor',
            'error': str(e)
        }), 500

#             ENDPOINTS GROUP


@app.route("/groups", methods=["POST"])
@role_required("ADMIN")
def create_group():
    try:
        body = request.get_json(silent=True) or {}

        if "name" not in body or "teacher_id" not in body:
            return jsonify({"msg": "Faltan datos obligatorios: name, teacher_id"}), 400

        description = body.get("description")
        if description is None or str(description).strip() == "":
            description = "Sin descripción"

        admin_id = int(get_jwt_identity())

        group = Group(
            name=body["name"],
            description=description,
            admin_id=admin_id,
            teacher_id=int(body["teacher_id"])
        )

        db.session.add(group)
        db.session.commit()

        return jsonify({"msg": "Grupo creado", "group_id": group.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error creando grupo", "error": str(e)}), 500


@app.route("/groups", methods=["GET"])
@role_required("ADMIN", "TEACHER")
def get_groups():
    identity = get_jwt_identity()

    if identity["role"] == "ADMIN":
        groups = Group.query.filter_by(admin_id=identity["user_id"]).all()
    else:
        groups = Group.query.filter_by(teacher_id=identity["user_id"]).all()

    return jsonify([
        {
            "id": g.id,
            "name": g.name,
            "description": g.description
        } for g in groups
    ]), 200


@app.route("/groups/<int:group_id>", methods=["GET"])
@role_required("ADMIN", "TEACHER")
def get_group(group_id):
    group = Group.query.get(group_id)

    if not group:
        return jsonify({"msg": "Grupo no encontrado"}), 404

    return jsonify({
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "teacher_id": group.teacher_id
    }), 200


@app.route("/groups/<int:group_id>/teacher", methods=["POST"])
@role_required("ADMIN")
def assign_teacher(group_id):
    body = request.get_json()

    if not body or "teacher_id" not in body:
        return jsonify({"msg": "teacher_id requerido"}), 400

    group = Group.query.get(group_id)
    if not group:
        return jsonify({"msg": "Grupo no encontrado"}), 404

    group.teacher_id = body["teacher_id"]
    db.session.commit()

    return jsonify({"msg": "Profesor asignado"}), 200


@app.route("/groups/<int:group_id>/students", methods=["POST"])
@jwt_required()
@role_required("ADMIN")
def add_student_to_group(group_id):
    body = request.get_json()

    if not body or "user_id" not in body:
        return jsonify({"msg": "user_id es requerido"}), 400

    group = Group.query.get(group_id)
    if not group:
        return jsonify({"msg": "Grupo no encontrado"}), 404

    user = User.query.get(body["user_id"])
    if not user or user.role != "STUDENT":
        return jsonify({"msg": "Usuario no válido"}), 400

    exists = Students_Group.query.filter_by(
        user_id=user.id,
        group_id=group_id
    ).first()

    if exists:
        return jsonify({"msg": "El estudiante ya está en el grupo"}), 409

    student_group = Students_Group(
        user_id=user.id,
        group_id=group_id
    )

    db.session.add(student_group)
    db.session.commit()

    return jsonify({"msg": "Estudiante agregado al grupo"}), 201


@app.route("/groups/<int:group_id>/students", methods=["GET"])
@jwt_required()
@role_required("TEACHER", "ADMIN")
def get_group_students(group_id):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"msg": "Grupo no encontrado"}), 404

    students = []
    for sg in group.students:
        students.append({
            "user_id": sg.user.id,
            "name": sg.user.name,
            "email": sg.user.email
        })

    return jsonify(students), 200


@app.route("/groups/<int:group_id>/students/<int:user_id>", methods=["DELETE"])
@jwt_required()
@role_required("ADMIN")
def remove_student_from_group(group_id, user_id):
    student_group = Students_Group.query.filter_by(
        group_id=group_id,
        user_id=user_id
    ).first()

    if not student_group:
        return jsonify({"msg": "Relación no encontrada"}), 404

    db.session.delete(student_group)
    db.session.commit()

    return jsonify({"msg": "Estudiante removido del grupo"}), 200


@app.route("/my-groups", methods=["GET"])
@jwt_required()
@role_required("STUDENT")
def get_my_groups():
    current_user = get_jwt_identity()

    relations = Students_Group.query.filter_by(
        user_id=current_user["id"]
    ).all()

    result = []
    for sg in relations:
        result.append({
            "group_id": sg.group.id,
            "group_name": sg.group.name,
            "description": sg.group.description
        })

    return jsonify(result), 200


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)


# SUBMISION POST SUBE TAREA DE UN ESTUDIANTE CON ID
@app.route("/submission", methods=["POST"])
def submission():
    try:
        body = request.get_json(silent=True)
        if body is None:
            return jsonify({'msg': 'Debes enviar información en el body'}), 400

        todo_id = body.get("todo_id")
        student_id = body.get("student_id")
        description = body.get("description")
        response_url = body.get("response_url")

        if todo_id is None or student_id is None:
            return jsonify({"msg": "todo_id y student_id son obligatorios"}), 400

        if not description and not response_url:
            return jsonify({"msg": "Debes enviar description o response_url"}), 400

        todo = Todo.query.get(todo_id)
        if not todo:
            return jsonify({"msg": "La tarea no existe"}), 404

        user = User.query.get(student_id)
        if not user:
            return jsonify({"msg": "Usuario no existe"}), 404

        if user.role.lower() != "student":  # el student tiene q venir en minuscula sino ponerle un .lower()
            return jsonify({"msg": "Solo un alumno puede crear una entrega"}), 403

        new_submission = Submission(

            description=description,
            response_url=response_url,
            todo_id=todo_id,
            student_id=student_id

        )

        db.session.add(new_submission)
        db.session.commit()

        return jsonify({
            "msg": "Entrega creada",
            "submission": {
                "id": new_submission.id,
                "todo_id": new_submission.todo_id,
                "student_id": new_submission.student_id,
                "description": new_submission.description,
                "response_url": new_submission.response_url

            }



        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Errpr interno del servidor", "error": str(e)}), 500

# SUBMISION PUT EDITA TAREA SUBIDA POR UN ESTUDIANTE CON ID


@app.route("/submission/<int:submission_id>", methods=["PUT"])
def update_submission(submission_id):

    try:
        body = request.get_json(silent=True) or {}

        description = body.get("description")
        response_url = body.get("response_url")

        if description is None and response_url is None:
            return jsonify({"msg": "No hay nada que actualizar"}), 400

        student_id = body.get("student_id")

        if student_id is None:
            return jsonify({"msg": "student_id es obligatorio"}), 400

        user = User.query.get(student_id)

        if not user:
            return jsonify({"msg": "Usuario no existe"}), 404

        if user.role.lower() != "student":
            return jsonify({"msg": "Solo un alumno puede modificar una entrega"}), 403

        submission = Submission.query.get(submission_id)
        if not submission:
            return jsonify({"msg": "No existe la entrega"}), 404

        if submission.student_id != student_id:
            return jsonify({"msg": "No autorizado para modificar esta entrega"}), 403

        if description is not None:
            submission.description = description

        if response_url is not None:
            submission.response_url = response_url

        db.session.commit()

        return jsonify({
            "msg": "Entrega actualizada",
            "submission": {
                "id": submission.id,
                "description": submission.description,
                "response_url": submission.response_url,
                "todo_id": submission.todo_id,
                "student_id": submission.student_id

            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error interno del servidor", "error": str(e)}), 500


# SUBMISION DELETE TAREA SUBIDA POR UN ESTUDIANTE CON ID
@app.route("/submission/<int:submission_id>", methods=["DELETE"])
def delete_submission(submission_id):
    try:
        body = request.get_json(silent=True) or {}
        student_id = body.get("student_id")

        if student_id is None:
            return jsonify({"msg": "student_id es obligatorio"}), 400

        user = User.query.get(student_id)
        if not user:
            return jsonify({"msg": "Usuario no existe"}), 404

        if user.role.lower() != "student":
            return jsonify({"msg": "Solo un alumno puede eliminar una entrega"}), 403

        submission = Submission.query.get(submission_id)
        if not submission:
            return jsonify({"msg": "No existe la entrega"}), 404

        if submission.student_id != student_id:
            return jsonify({"msg": "No autorizado para Eliminar esta entrega"}), 403

        db.session.delete(submission)
        db.session.commit()

        return jsonify({
            "msg": "Entrega borrada",
            "submission": {
                "id": submission.id,
                "todo_id": submission.todo_id,
                "student_id": submission.student_id,
                "description": submission.description,
                "response_url": submission.response_url

            }

        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error interno del servidor", "error": str(e)}), 500

# SUBMISION GET TAREA SUBIDA POR UN ESTUDIANTE CON ID


@app.route("/submission/<int:submission_id>", methods=["GET"])
def get_submission(submission_id):

    try:

        submission = Submission.query.get(submission_id)

        if not submission:
            return jsonify({"msg": "No existe la entrega"}), 404

        return jsonify({
            "msg": "Vista de entrega",
            "submission": {
                "id": submission.id,
                "todo_id": submission.todo_id,
                "student_id": submission.student_id,
                "description": submission.description,
                "response_url": submission.response_url

            }

        }), 200

    except Exception as e:

        return jsonify({"msg": "Error interno del servidor", "error": str(e)}), 500


# SUBMISION GET LISTA DE TAREAS SUBIDA POR ESTUDIANTES
@app.route("/submissions", methods=["GET"])
def get_submissions():

    try:

        student_id = request.args.get("student_id")
        todo_id = request.args.get("todo_id")

        if student_id is None and todo_id is None:
            return jsonify({"msg": " No existe student_id o todo_id"}), 400

        if todo_id is not None:
            todo = Todo.query.get(todo_id)
            if todo is None:
                return jsonify({"msg": "La tarea no existe"}), 404

        if student_id is not None:
            user = User.query.get(student_id)
            if user is None:
                return jsonify({"msg": "No existe el estudiante"}), 404

        query = Submission.query
        if student_id is not None:
            query = query.filter_by(student_id=student_id)

        if todo_id is not None:
            query = query.filter_by(todo_id=todo_id)

        submissions = query.all()

        return jsonify({
            "msg": "Listado de entrega",
            "submissions": [
                {
                    "id": submission.id,
                    "todo_id": submission.todo_id,
                    "student_id": submission.student_id,
                    "description": submission.description,
                    "response_url": submission.response_url

                } for submission in submissions
            ]

        }), 200

    except Exception as e:

        return jsonify({"msg": "Error interno del servidor", "error": str(e)}), 500


@app.route('/register-staff', methods=['POST'])
def register_staff():
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"msg": "Complete los campos requeridos"}), 400
    if 'email' not in body:
        return jsonify({"msg": "El campo email no puede estar vacío"}), 400
    if 'password' not in body:
        return jsonify({"msg": "El campo password no puede estar vacío"}), 400
    if 'name' not in body:
        return jsonify({"msg": "El campo name no puede estar vacío"}), 400
    if 'role' not in body:
        return jsonify({"msg": "Determine el rol del nuevo usuario"}), 400
    existing_user = User.query.filter_by(email=body['email']).first()
    if existing_user:
        return jsonify({"msg": "User already exists"}), 400
    new_admin = User(
        email=body['email'],
        password=body['password'],
        name=body['name'],
        role=body['role'],
        is_active=True
    )
    db.session.add(new_admin)
    db.session.commit()
    return jsonify({"msg": f"Usuario {body['role']} registrado exitosamente"}), 201


@app.route('/todos-creation', methods=['POST'])
@jwt_required()
@role_required("TEACHER", "ADMIN")

def create_todo():
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"msg": "Complete los campos requeridos"}), 400
    if 'title' not in body:
        return jsonify({"msg": "El campo title no puede estar vacío"}), 400
    if 'description' not in body:
        return jsonify({"msg": "El campo description no puede estar vacío"}), 400
    if 'due_date' not in body:
        return jsonify({"msg": "El campo due_date no puede estar vacío"}), 400
    if 'teacher_id' not in body:
        return jsonify({"msg": "El campo teacher_id no puede estar vacío"}), 400
    if 'group_id' not in body:
        return jsonify({"msg": "El campo group_id no puede estar vacío"}), 400
    if 'student_id' not in body:
        return jsonify({"msg": "El campo student_id no puede estar vacío"}), 400
   
    teacher_id = identity["user_id"] if isinstance(identity,dict) else identity
   
    new_todo = Todo(
        title=body['title'],
        description=body['description'],
        due_date=body['due_date'],
        teacher_id=teacher_id,
        group_id=body['group_id'],
        student_id=body('student_id')
       
    )
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({
        "msg": "Todo created successfully",
        "todo_id": new_todo.id
    }), 201


@app.route('/todos', methods=['GET'])
def get_todos():
    todos = Todo.query.all()
    todos_list = []
    for todo in todos:
        todos_list.append({
            'id': todo.id,
            'title': todo.title,
            'description': todo.description,
            'due_date': todo.due_date.isoformat(),
            'teacher_id': todo.teacher_id,
            'group_id': todo.group_id,
            'student_id': todo.student_id
        })
    return jsonify(todos_list), 200


@app.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo_by_id(todo_id):
    todo = Todo.query.get(todo_id)
    if not todo:
        return jsonify({"msg": "Tarea no encontrada"}), 404
    todo_data = {
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'due_date': todo.due_date.isoformat(),
        'teacher_id': todo.teacher_id,
        'group_id': todo.group_id,
    }
    return jsonify(todo_data), 200


@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if not todo:
        return jsonify({"msg": "tarea no encontrada"}), 404
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"msg": "Complete los campos requeridos"}), 400
    if 'title' in body:
        todo.title = body['title']
    if 'description' in body:
        todo.description = body['description']
    if 'due_date' in body:
        todo.due_date = body['due_date']
    db.session.commit()
    return jsonify({"msg": "Cambios aplicados a la tarea"}), 200


@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if not todo:
        return jsonify({"msg": "tarea no encontrada"}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({"msg": "tarea eliminada exitosamente"}), 200


@app.route('/statuses', methods=['GET'])
def get_statuses():
    statuses = Status.query.all()
    statuses_list = []
    for status in statuses:
        statuses_list.append({
            'id': status.id,
            'name': status.name,
            'state': status.state,
            'feedback': status.feedback
        })
    return jsonify(statuses_list), 200


@app.route('/statuses/<int:status_id>', methods=['GET'])
def get_status_by_id(status_id):
    status = Status.query.get(status_id)
    if not status:
        return jsonify({"msg": "No hay calificación disponible"}), 404
    status_data = {
        'id': status.id,
        'name': status.name,
        'state': status.state,
        'feedback': status.feedback
    }
    return jsonify(status_data), 200


@app.route('/statuses/<int:status_id>', methods=['PUT'])
def update_status(status_id):
    status = Status.query.get(status_id)
    if not status:
        return jsonify({"msg": "No hay calificación disponible"}), 404
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"msg": "Complete los campos requeridos"}), 400
    if 'state' in body:
        status.state = body['state']
    if 'feedback' in body:
        status.feedback = body['feedback']
    db.session.commit()
    return jsonify({"msg": "Calificación actualizada exitosamente"}), 200


@app.route('/statuses/<int:status_id>', methods=['POST'])
def create_status(status_id):
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"msg": "Complete los campos requeridos"}), 400
    if 'submission_id' not in body:
        return jsonify({"msg": "El campo submission_id no puede estar vacío"}), 400
    if 'state' not in body:
        return jsonify({"msg": "El campo state no puede estar vacío"}), 400
    new_status = Status(
        submission_id=body['submission_id'],
        state=body['state'],
        feedback=body.get('feedback', '')
    )
    db.session.add(new_status)
    db.session.commit()
    return jsonify({"msg": "Calificación creada exitosamente"}), 201

#         API CALENDARIO DE GOOGLE


@app.route("/google/ping", methods=["GET"])
def google_ping():
    return jsonify({"msg": "Google Calendar listo"}), 200


@app.route("/google/events", methods=["POST"])
def create_google_event():
    try:
        body = request.get_json(silent=True) or {}

        title = body.get("title")
        due_date = body.get("due_date")
        description = body.get("description", "")
        calendar_id = body.get("calendar_id", "primary")

        emails = body.get("emails", [])

        if not title or not due_date:
            return jsonify({"msg": "Campos 'title' y 'due_date' son obligatorios"}), 400

        if emails and (not isinstance(emails, list) or not all(isinstance(e, str) for e in emails)):
            return jsonify({"msg": "El campo 'emails' debe ser una lista de strings"}), 400

        service = get_calendar_service()

        event_body = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": due_date,
                "timeZone": "America/Montevideo"
            },
            "end": {
                "dateTime": due_date,
                "timeZone": "America/Montevideo"
            }
        }

        if emails:
            event_body["attendees"] = [{"email": e} for e in emails]

        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event_body,
            sendUpdates="all"
        ).execute()

        return jsonify({
            "msg": "Evento creado en Google Calendar",
            "google_event_id": created_event.get("id"),
            "htmlLink": created_event.get("htmlLink"),
            "attendees": [a.get("email") for a in created_event.get("attendees", [])]
        }), 201

    except Exception as e:
        return jsonify({"msg": "Error creando evento", "error": str(e)}), 500


@app.route("/google/events/<int:event_id>/invite", methods=["POST"])
@role_required("TEACHER", "ADMIN")
def invite_users_to_event(event_id):
    body = request.get_json(silent=True)
    if not body or "emails" not in body:
        return jsonify({"msg": "Debe enviar una lista de emails para invitar"}), 400

    invited_emails = body["emails"]
    return jsonify({"msg": f"Invitaciones enviadas a {len(invited_emails)} usuarios", "emails": invited_emails}), 200


@app.route("/todos-creation", methods=["POST"])
@role_required("TEACHER", "ADMIN")
def create_todo_automatic():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"msg": "Debe enviar datos para la tarea"}), 400
    if "title" not in body or "description" not in body or "due_date" not in body:
        return jsonify({"msg": "Campos 'title', 'description' y 'due_date' son obligatorios"}), 400

    new_todo = Todo(
        title=body["title"],
        description=body["description"],
        due_date=body["due_date"],
        teacher_id=get_jwt_identity()["user_id"],
        group_id=body.get("group_id"),
        student_id=body.get("student_id")
    )

    db.session.add(new_todo)
    db.session.commit()

    return jsonify({"msg": "Tarea automática creada exitosamente", "todo_id": new_todo.id}), 201

#             Crear un evento en el calendario


@app.route("/google/create-event", methods=["POST"])
@jwt_required()
def google_create_event():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    import datetime

    body = request.get_json(silent=True)
    if not body or 'summary' not in body or 'start' not in body or 'end' not in body:
        return jsonify({"msg": "Campos obligatorios: summary, start, end"}), 400

    creds = Credentials(
        token=os.getenv("GOOGLE_ACCESS_TOKEN"),
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    )

    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": body["summary"],
        "description": body.get("description", ""),
        "start": {"dateTime": body["start"], "timeZone": "UTC"},
        "end": {"dateTime": body["end"], "timeZone": "UTC"},
        "attendees": [{"email": e} for e in body.get("attendees", [])],
    }

    created_event = service.events().insert(
        calendarId="primary", body=event).execute()
    return jsonify({"msg": "Evento creado", "event": created_event}), 201

#                Crear un evento en el calendario


@app.route("/google/list-events", methods=["GET"])
@jwt_required()
def google_list_events():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    import datetime

    creds = Credentials(
        token=os.getenv("GOOGLE_ACCESS_TOKEN"),
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    )

    service = build("calendar", "v3", credentials=creds)

    now = datetime.datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(calendarId="primary", timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    return jsonify({"events": events}), 200

    #              Actualizar un evento existente


@app.route("/google/update-event/<event_id>", methods=["PUT"])
@jwt_required()
def google_update_event(event_id):
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"msg": "Cuerpo vacío"}), 400

    creds = Credentials(
        token=os.getenv("GOOGLE_ACCESS_TOKEN"),
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    )

    service = build("calendar", "v3", credentials=creds)
    event = service.events().get(calendarId="primary", eventId=event_id).execute()

    for key in ["summary", "description", "start", "end", "attendees"]:
        if key in body:
            if key in ["start", "end"]:
                event[key] = {"dateTime": body[key], "timeZone": "UTC"}
            elif key == "attendees":
                event[key] = [{"email": e} for e in body[key]]
            else:
                event[key] = body[key]

    updated_event = service.events().update(
        calendarId="primary", eventId=event_id, body=event).execute()
    return jsonify({"msg": "Evento actualizado", "event": updated_event}), 200

#                Eliminar un evento


@app.route("/google/delete-event/<event_id>", methods=["DELETE"])
@jwt_required()
def google_delete_event(event_id):
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    creds = Credentials(
        token=os.getenv("GOOGLE_ACCESS_TOKEN"),
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    )

    service = build("calendar", "v3", credentials=creds)
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return jsonify({"msg": "Evento eliminado"}), 200

#                Login de google


@app.route("/google/login")
def google_login():
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="https://potential-acorn-r4gvrv455x47h54xq-3001.app.github.dev/google/callback"
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    session["state"] = state
    return redirect(authorization_url)

#                callback google


@app.route("/google/callback")
def google_callback():
    state = session.get("state")

    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri="https://potential-acorn-r4gvrv455x47h54xq-3001.app.github.dev/google/callback"
    )

    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    os.makedirs("google_credentials", exist_ok=True)
    with open("google_credentials/token.json", "w") as token:
        token.write(credentials.to_json())

    return jsonify({"msg": "Google Calendar conectado correctamente"})


@app.route("/google/calendars", methods=["GET"])
def google_calendars():
    try:
        service = get_calendar_service()
        calendars = service.calendarList().list().execute()

        return jsonify({
            "msg": "Calendarios obtenidos correctamente",
            "calendars": calendars.get("items", [])
        }), 200

    except Exception as e:
        return jsonify({
            "msg": "Error obteniendo calendarios",
            "error": str(e)
        }), 500


@app.route("/google/events", methods=["GET"])
def list_google_events():
    try:
        service = get_calendar_service()

        calendar_id = request.args.get("calendar_id", "primary")
        max_results = int(request.args.get("maxResults", 10))

        now = datetime.now(timezone.utc).isoformat()

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])

        simplified = []
        for e in events:
            simplified.append({
                "id": e.get("id"),
                "summary": e.get("summary"),
                "htmlLink": e.get("htmlLink"),
                "start": (e.get("start") or {}).get("dateTime") or (e.get("start") or {}).get("date"),
                "end": (e.get("end") or {}).get("dateTime") or (e.get("end") or {}).get("date"),
                "attendees": [a.get("email") for a in e.get("attendees", [])] if e.get("attendees") else []
            })

        return jsonify({
            "msg": "Eventos obtenidos correctamente",
            "count": len(simplified),
            "events": simplified
        }), 200

    except Exception as e:
        return jsonify({"msg": "Error listando eventos", "error": str(e)}), 500


@app.route("/google/events/<event_id>", methods=["DELETE"])
def delete_google_event(event_id):
    try:
        service = get_calendar_service()

        calendar_id = request.args.get("calendar_id", "primary")

        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
            sendUpdates="all"
        ).execute()

        return jsonify({
            "msg": "Evento eliminado correctamente",
            "deleted_event_id": event_id
        }), 200

    except Exception as e:
        return jsonify({
            "msg": "Error eliminando evento",
            "error": str(e)
        }), 500


@app.route("/google/events/<event_id>", methods=["PUT"])
def update_google_event(event_id):
    try:
        body = request.get_json(silent=True) or {}
        if not body:
            return jsonify({"msg": "Debe enviar campos para actualizar"}), 400

        service = get_calendar_service()
        calendar_id = body.get("calendar_id", "primary")

        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        if "title" in body:
            event["summary"] = body["title"]
        if "description" in body:
            event["description"] = body["description"]

        if "due_date" in body:
            tz = body.get("timeZone", "America/Montevideo")
            event["start"] = {"dateTime": body["due_date"], "timeZone": tz}
            event["end"] = {"dateTime": body["due_date"], "timeZone": tz}

        if "attendees" in body:
            event["attendees"] = [{"email": e} for e in body["attendees"]]

        updated = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event,
            sendUpdates="all"
        ).execute()

        return jsonify({
            "msg": "Evento actualizado correctamente",
            "google_event_id": updated.get("id"),
            "htmlLink": updated.get("htmlLink"),
            "updated_summary": updated.get("summary"),
        }), 200

    except Exception as e:
        return jsonify({
            "msg": "Error actualizando evento",
            "error": str(e)
        }), 500


@app.route("/teacher/todos", methods=["POST"])
@role_required("TEACHER", "ADMIN")
def create_todo_with_google_event():

    try:
        body = request.get_json(silent=True) or {}

        title = body.get("title")
        description = body.get("description", "")
        due_date_str = body.get("due_date")
        group_id = body.get("group_id")

        if not title or not due_date_str or not group_id:
            return jsonify({
                "msg": "Campos obligatorios: title, due_date, group_id"
            }), 400

        try:
            dt_start = datetime.fromisoformat(
                due_date_str.replace("Z", "+00:00"))
        except Exception:
            return jsonify({"msg": "due_date debe ser ISO. Ej: 2026-02-10T23:59:00"}), 400

        dt_end = dt_start + timedelta(minutes=30)

        teacher_id = int(get_jwt_identity())

        group = Group.query.get(int(group_id))
        if not group:
            return jsonify({
                "msg": f"No existe un grupo con group_id={group_id}"
            }), 400

        students_rel = list(group.students) if hasattr(
            group, "students") else []
        if not students_rel:
            return jsonify({
                "msg": f"El grupo {group_id} no tiene estudiantes. Agregá alumnos antes."
            }), 400

        attendees_emails = []
        student_ids = []

        for rel in students_rel:
            if not getattr(rel, "user", None):
                continue
            if not rel.user.email:
                continue
            attendees_emails.append(rel.user.email)
            student_ids.append(rel.user.id)

        if not student_ids:
            return jsonify({
                "msg": "No se encontraron estudiantes válidos con email en el grupo."
            }), 400

        service = get_calendar_service()
        google_event_body = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": dt_start.isoformat(),
                "timeZone": "America/Montevideo"
            },
            "end": {
                "dateTime": dt_end.isoformat(),
                "timeZone": "America/Montevideo"
            },
            "attendees": [{"email": e} for e in attendees_emails]
        }

        created_event = service.events().insert(
            calendarId="primary",
            body=google_event_body,
            sendUpdates="all"
        ).execute()

        created_todos = []
        for sid in student_ids:
            new_todo = Todo(
                title=title,
                description=description,
                due_date=dt_start,
                teacher_id=teacher_id,
                group_id=int(group_id),
                student_id=int(sid)
            )
            db.session.add(new_todo)
            created_todos.append(new_todo)

        db.session.commit()

        return jsonify({
            "msg": "Tarea creada (1 por alumno) + evento creado en Google Calendar",
            "google_event_id": created_event.get("id"),
            "htmlLink": created_event.get("htmlLink"),
            "attendees": attendees_emails,
            "todos_created": [
                {"todo_id": t.id, "student_id": t.student_id} for t in created_todos
            ]
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "msg": "Error guardando la tarea en DB",
            "error": str(e)
        }), 500


@app.route("/google/events/<event_id>", methods=["GET"])
@role_required("TEACHER", "ADMIN")
def get_google_event(event_id):
    try:
        service = get_calendar_service()
        event = service.events().get(calendarId="primary", eventId=event_id).execute()

        return jsonify({
            "msg": "Evento obtenido correctamente",
            "event": {
                "id": event.get("id"),
                "summary": event.get("summary"),
                "description": event.get("description"),
                "start": event.get("start"),
                "end": event.get("end"),
                "attendees": [a.get("email") for a in event.get("attendees", [])],
                "htmlLink": event.get("htmlLink")
            }
        }), 200
    except Exception as e:
        return jsonify({"msg": "Error obteniendo evento", "error": str(e)}), 500
