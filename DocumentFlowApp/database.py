import datetime

from flask_login import UserMixin
from sqlalchemy import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from config import database

DIRECTOR_ROLE = "Директор"
DEPARTMENT_HEAD_ROLE = "Глава отдела"
EMPLOYEE_ROLE = "Специалист отдела"

roles = [DIRECTOR_ROLE, DEPARTMENT_HEAD_ROLE, EMPLOYEE_ROLE]


class User(database.Model, UserMixin):
    __tablename__ = "user"
    id = Column(Integer(), primary_key=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    assignments = relationship("Assignment", backref="executor")

    def is_director(self):
        return self.role == DIRECTOR_ROLE

    def is_department_head(self):
        return self.role == DEPARTMENT_HEAD_ROLE

    def is_employee(self):
        return self.role == EMPLOYEE_ROLE

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if check_password_hash(self.password_hash, password):
            return true
        return false


class Assignment(database.Model):
    __tablename__ = "assignment"
    id = Column(Integer(), primary_key=True)
    text = Column(Text, nullable=False)
    create_date = (Column(Date(), nullable=True, default=datetime.datetime.now().date()))
    executor_id = Column(Integer(), ForeignKey("user.id"), nullable=False)
    director_sign = Column(Text, nullable=True)
    department_head_sign = Column(Text, nullable=True)
    employee_sign = Column(Text, nullable=True)
    file_name = Column(String, nullable=True)


def save(obj):
    try:
        database.session.add(obj)
        database.session.commit()
    except SQLAlchemyError as e:
        print(e)
        database.session.rollback()


def get_employees():
    return database.session.query(User).filter(User.role == EMPLOYEE_ROLE).all()


def get_department_heads():
    return database.session.query(User).filter(User.role == DEPARTMENT_HEAD_ROLE).all()


def get_assignments_with_director_sign():
    return [i for i in database.session.query(Assignment).all() if i.director_sign]


def get_assignments_for_director():
    return [i for i in database.session.query(Assignment).all() if i.department_head_sign and i.director_sign is None]


def get_assignments_for_department_head():
    return [i for i in database.session.query(Assignment).all() if i.employee_sign and i.director_sign is None]


def get_assignments_by_executor_id(executor_id):
    return [i for i in database.session.query(Assignment).filter(Assignment.executor_id == executor_id).all() if
            i.director_sign is None]


def get_all(obj_class):
    return database.session.query(obj_class).all()


def find_by_id(obj_class, obj_id):
    return database.session.query(obj_class).filter(obj_class.id == obj_id).first()
