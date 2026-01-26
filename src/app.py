"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from api.utils import APIException, generate_sitemap
from api.models import Students_Group, Group, Todo, Submission, Status, User, Reading
from api.models import db
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import JWTManager, create_access_token
# from models import Person

ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../dist/')
app = Flask(__name__)
app.url_map.strict_slashes = False

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


@app.route("/register", methods=["POST"])
def register():
    try:
        body = request.get_json(silent=True)

        if body is None:
            return jsonify({'msg': 'Debes enviar información en el body'}), 400

        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in body:
                return jsonify({'msg': f'El campo {field} es obligatorio'}), 400

        if (
            Student.query.filter_by(email=body['email']).first()
            or Teacher.query.filter_by(email=body['email']).first()
            or Admin.query.filter_by(email=body['email']).first()
        ):
            return jsonify({'msg': 'Este email ya está en uso'}), 409

        new_student = Student(
            email=body['email'],
            password=body['password'],
            first_name=body['first_name'],
            last_name=body['last_name']
        )

        db.session.add(new_student)
        db.session.commit()

        return jsonify({'msg': 'Student creado exitosamente'}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'msg': 'Error de integridad en la base de datos'}), 409

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'msg': 'Error interno del servidor',
            'error': str(e)
        }), 500


@app.route("/login", methods=["POST"])
def login():
    try:
        body = request.get_json(silent=True)

        if body is None:
            return jsonify({'msg': 'Debes enviar información en el body'}), 400

        if 'email' not in body or 'password' not in body:
            return jsonify({'msg': 'Email y password son obligatorios'}), 400

        user = Student.query.filter_by(email=body['email']).first()
        role = "Student"

        if not user:
            user = Teacher.query.filter_by(email=body['email']).first()
            role = "Teacher"

        if not user:
            user = Admin.query.filter_by(email=body['email']).first()
            role = "Admin"

        if not user or user.password != body['password']:
            return jsonify({'msg': 'Credenciales incorrectas'}), 401

        access_token = create_access_token(
            identity={
                "id": user.id,
                "role": role
            }
        )

        return jsonify({
            'access_token': access_token,
            'role': role
        }), 200

    except Exception as e:
        return jsonify({
            'msg': 'Error interno del servidor',
            'error': str(e)
        }), 500


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)


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
    existing_user = models.User.query.filter_by(email=body['email']).first()
    if existing_user:
        return jsonify({"msg": "User already exists"}), 400
    new_admin = models.User(
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
    new_todo = models.Todo(
        title=body['title'],
        description=body['description'],
        due_date=body['due_date'],
    )
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({"msg": "Todo created successfully"}), 201

@app.route('/todos', methods=['GET'])
def get_todos():
    todos = models.Todo.query.all()
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
    todo = models.Todo.query.get(todo_id)
    if not todo:
        return jsonify({"msg": "Todo not found"}), 404
    todo_data = {
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'due_date': todo.due_date.isoformat(),
        'teacher_id': todo.teacher_id,
        'group_id': todo.group_id,
        'student_id': todo.student_id
    }
    return jsonify(todo_data), 200

@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = models.Todo.query.get(todo_id)
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
    todo = models.Todo.query.get(todo_id)
    if not todo:
        return jsonify({"msg": "tarea no encontrada"}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({"msg": "tarea eliminada exitosamente"}), 200

@app.route('/statuses', methods=['GET'])
def get_statuses():
    statuses = models.Status.query.all()
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
    status = models.Status.query.get(status_id)
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
    status = models.Status.query.get(status_id)
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
    new_status = models.Status(
        submission_id=body['submission_id'],
        state=body['state'],
        feedback=body.get('feedback', '')
    )
    db.session.add(new_status)
    db.session.commit()

    
    return jsonify({"msg": "Calificación creada exitosamente"}), 201

#MOSTRAR LECTURAS A ESTUDIANTES 
@app.route('private/readings', methonds=['GET'])
# @jwt_required()
def get_all_readings():
    readings_query = Reading.query.all()
    readings_query_serialized = []
    for readings in readings_query:
        readings_query_serialized.append(readings_query.serialize())
    return ({'Tus lecturas pendientes': readings})

#CREAR LECTURAS POR PROFESOR 
@app.route('private/readings/create', methods=['POST'])
# @jwt_required()
def create_new_reading():
    # current_user_id = get_jwt_identity()
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({'msg': 'Necesitas llenar el body'})
    if 'title' not in body:
        return jsonify({'msg': 'Necesitas poner un titulo a la lectura'})
    if 'content' not in body:
        return jsonify({'msg': 'Necesitas agregar contenido'})
    if 'group_id' not in body:
        return jsonify({'msg': 'Necesitas asignarla a un grupo'})
    new_reading = Reading()
    new_reading.title = body['title']
    new_reading.content = body['content']
    new_reading.group_id = body['group_id']
    db.session.add(new_reading)
    db.session.commit()

    return jsonify({'msg': f'lectura agregada por profesor:'})


#editar lectura por el profesor
@app.route('private/readings/create', methods=['POST'])
@jwt_required()
def create_new_reading():
    # current_user_id = get_jwt_identity()
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({'msg': 'Necesitas llenar el body'})
    if 'title' not in body:
        return jsonify({'msg': 'Necesitas poner un titulo a la lectura'})
    if 'content' not in body:
        return jsonify({'msg': 'Necesitas agregar contenido'})
    if 'group_id' not in body:
        return jsonify({'msg': 'Necesitas asignarla a un grupo'})
    new_reading = Reading()
    new_reading.title = body['title']
    new_reading.content = body['content']
    new_reading.group_id = body['group_id']
    db.session.add(new_reading)
    db.session.commit()

    return jsonify({'msg': f'lectura agregada por profesor: '})


#MODIFICAR TAREA 
@app.route('private/readings/update/<int:id>', methods=['PUT'])
# @jwt_required()
def edit_reading(id):
    # current_user_id = get_jwt_identity()
    body = request.get_json(silent=True)
    
    
    reading_to_edit = Reading.query.get(id)
    if reading_to_edit is None:
        return jsonify({'msg': 'Lectura no encontrada'})
    
    if 'title' in body:
        reading_to_edit.title = body['title']
    if 'content' in body:
        reading_to_edit.content = body['content']
    if 'group_id' in body:
        reading_to_edit.group_id = body['group_id']
    
    db.session.commit()
    
    return jsonify({'msg': f'lectura editada por profesor: '})

#ELIMINAR TAREA 
        
@app.route('private/readings/delete/<int:id>', methods=['DELETE'])
# @jwt_required()
def delete_reading(id):
    # current_user_id = get_jwt_identity()
    
    reading_to_delete = Reading.query.get(id)
    if reading_to_delete is None:
        return jsonify({'msg': 'Lectura no encontrada'})
    
    db.session.delete(reading_to_delete)
    db.session.commit()
    
    return jsonify({'msg': f'lectura eliminada por profesor:'})