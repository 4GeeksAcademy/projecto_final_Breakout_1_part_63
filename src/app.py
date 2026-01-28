"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from api.utils import APIException, generate_sitemap
from api.models import Students_Group, Group, Todo, Submission, Status, User
from api.models import db
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from functools import wraps
from flask_cors import CORS

# from models import Person




def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            identity = get_jwt_identity()
            if identity["role"] not in roles:
                return jsonify({"msg": "Acceso no autorizado"}), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper


ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../dist/')
app = Flask(__name__)
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

        user = None
        role = None

        users_models = [
            ('Student', "STUDENT"),
            ('Teacher', "TEACHER"),
            ('Admin', "ADMIN")
        ]

        for model, r in users_models:
            user = model.query.filter_by(email=body['email']).first()
            if user:
                role = r
                break

        if not user or user.password != body['password']:
            return jsonify({'msg': 'Credenciales incorrectas'}), 401

        access_token = create_access_token(
            identity={
                "user_id": user.id,
                "role": role
            }
        )

        return jsonify({
            "access_token": access_token,
            "role": role
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
    body = request.get_json()

    if not body or "name" not in body or "teacher_id" not in body:
        return jsonify({"msg": "Faltan datos obligatorios"}), 400

    admin_id = get_jwt_identity()["user_id"]

    group = Group(
        name=body["name"],
        description=body.get("description"),
        admin_id=admin_id,
        teacher_id=body["teacher_id"]
    )

    db.session.add(group)
    db.session.commit()

    return jsonify({"msg": "Grupo creado", "group_id": group.id}), 201


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


@app.route('/register/staff', methods=['POST'])
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
    new_todo = Todo(
        title=body['title'],
        description=body['description'],
        due_date=body['due_date'],
    )
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({"msg": "Todo created successfully"}), 201


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
