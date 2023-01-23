from flask import render_template, request, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from config import app, database
from database import User, Assignment, save, roles, get_employees, get_department_heads, find_by_id, \
    get_assignments_by_executor_id, get_assignments_for_director, get_assignments_with_director_sign, \
    get_assignments_for_department_head

login_manager = LoginManager(app)
login_manager.login_view = "/login"


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


@login_manager.user_loader
def load_user(user_id):
    return database.session.query(User).get(user_id)


@app.get("/logout")
@login_required
def logout():
    logout_user()
    return show_login_form()


@app.get("/")
@login_required
def index():
    assignments = []
    completed_assignments = []
    if current_user.is_director():
        assignments = get_assignments_for_director()
        completed_assignments = get_assignments_with_director_sign()
    else:
        assignments = get_assignments_by_executor_id(current_user.id)
    if current_user.is_department_head():
        assignments.extend(get_assignments_for_department_head())
    return render_template("index.html", employees=get_employees(), department_heads=get_department_heads(),
                           assignments=assignments, completed_assignments=completed_assignments)


@app.post("/assignment/create")
@login_required
def create_assignment():
    text = request.form.get("text")
    executor_id = request.form.get("executor_id")
    save(Assignment(text=text, executor_id=executor_id))
    return index()


@app.post("/assignment/delegate")
@login_required
def assignment_delegate():
    assignment_id = int(request.form.get("assignment_id"))
    executor_id = request.form.get("executor_id")
    assignment = find_by_id(Assignment, assignment_id)
    assignment.executor_id = executor_id
    assignment.director_sign = None
    assignment.department_head_sign = None
    assignment.employee_sign = None
    assignment.file_name = None
    save(assignment)
    return index()


@app.get("/assignment/<assignment_id>/file/download")
@login_required
def assignment_file_download(assignment_id):
    assignment_id = int(assignment_id)
    assignment = find_by_id(Assignment, assignment_id)
    return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path=assignment.file_name, as_attachment=True)


@app.post("/assignment/file/upload")
@login_required
def assignment_file_upload():
    assignment_id = int(request.form.get("assignment_id"))
    assignment = find_by_id(Assignment, assignment_id)
    file = request.files['file']
    file_name = f"assignment_{assignment.id}_{file.filename}"
    file_path = f"{app.config['UPLOAD_FOLDER']}/{file_name}"
    assignment.file_name = file_name
    file.save(file_path)
    save(assignment)
    return index()


@app.post("/assignment/sign")
@login_required
def sign_assignment():
    assignment_id = int(request.form.get("assignment_id"))
    assignment = find_by_id(Assignment, assignment_id)
    if current_user.is_director():
        assignment.director_sign = current_user.password_hash
    elif current_user.is_department_head():
        assignment.department_head_sign = current_user.password_hash
    else:
        assignment.employee_sign = current_user.password_hash
    save(assignment)
    return index()


@app.post("/assignment/sign/remove")
@login_required
def remove_assignment_sign():
    assignment_id = int(request.form.get("assignment_id"))
    assignment = find_by_id(Assignment, assignment_id)
    if current_user.is_director():
        assignment.director_sign = None
    elif current_user.is_department_head():
        assignment.department_head_sign = None
    else:
        assignment.employee_sign = None
    save(assignment)
    return index()


@app.post("/login")
def login():
    if current_user.is_authenticated:
        return index()
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        user = database.session.query(User).filter(User.username == username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return index()
        else:
            return show_login_form(message="Ошибка авторизации")


@app.post("/registration")
def registration():
    if current_user.is_authenticated:
        return index()
    else:
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        username = request.form.get("username")
        role = request.form.get("role")
        if database.session.query(User).filter(User.username == username).first():
            return show_login_form(message="Пользователь с таким логином уже зарегистрирован")
        else:
            password = request.form.get("password")
            user = User(first_name=first_name, last_name=last_name, username=username, role=role)
            user.set_password(password)
            save(user)
            login_user(user, remember=True)
            return index()


@app.get("/registration")
def show_registration_form(message=""):
    return render_template("registration.html", message=message, roles=roles)


@app.get("/login")
def show_login_form(message=""):
    return render_template("login.html", message=message)


if __name__ == "__main__":
    app.app_context().push()
    database.create_all()
    app.run()
