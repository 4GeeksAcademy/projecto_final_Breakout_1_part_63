from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    role = mapped_column(SQLEnum('ADMIN', 'TEACHER', 'STUDENT', name='role_enum'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    students_groups: Mapped[list["Students_Group"]] = relationship(back_populates='user')
    groups_admin: Mapped[list["Group"]] = relationship(back_populates='admin', foreign_keys="Group.admin_id")
    groups_teacher: Mapped[list["Group"]] = relationship(back_populates='teacher', foreign_keys="Group.teacher_id")
    todos: Mapped[list["Todo"]] = relationship(back_populates='teacher')
    readings: Mapped[list["Reading"]] = relationship(back_populates='teacher')
    statuses: Mapped[list["Status"]] = relationship(back_populates='teacher')

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "is_active": self.is_active
        }


class Students_Group(db.Model):
    __tablename__ = 'student_group'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    user: Mapped["User"] = relationship(back_populates='students_groups')
    group_id: Mapped[int] = mapped_column(ForeignKey('group.id'), nullable=False)
    group: Mapped["Group"] = relationship(back_populates='students')
    todos: Mapped[list["Todo"]] = relationship(back_populates='student')
    submissions: Mapped[list["Submission"]] = relationship(back_populates='student')
    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "group_id": self.group_id
        }

class Group(db.Model):
    __tablename__ = 'group'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255))
    admin_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    admin: Mapped["User"] = relationship(back_populates='groups_admin', foreign_keys="Group.admin_id")
    teacher_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    teacher: Mapped["User"] = relationship(back_populates='groups_teacher', foreign_keys="Group.teacher_id")
    students: Mapped[list["Students_Group"]] = relationship(back_populates='group')
    todos: Mapped[list["Todo"]] = relationship(back_populates='group')
    readings: Mapped[list["Reading"]] = relationship(back_populates='group')
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "admin_id": self.admin_id,
            "teacher_id": self.teacher_id
        }


class Todo(db.Model):
    __tablename__ = 'todo'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255))
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    teacher: Mapped["User"] = relationship(back_populates='todos')
    group_id: Mapped[int] = mapped_column(ForeignKey('group.id'), nullable=False)
    group: Mapped["Group"] = relationship(back_populates='todos')
    student_id: Mapped[int] = mapped_column(ForeignKey('student_group.id'))
    student: Mapped["Students_Group"] = relationship(back_populates='todos')
    submissions: Mapped[list["Submission"]] = relationship(back_populates='todo')
    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat(),
            "teacher_id": self.teacher_id,
            "group_id": self.group_id,
            "student_id": self.student_id
        }


class Submission(db.Model):
    __tablename__ = 'submission'
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    response_url: Mapped[str] = mapped_column(String(300))
    todo_id: Mapped[int] = mapped_column(ForeignKey('todo.id'), nullable=False)
    todo: Mapped["Todo"] = relationship(back_populates='submissions')
    student_id: Mapped[int] = mapped_column(ForeignKey('student_group.id'), nullable=False)
    student: Mapped["Students_Group"] = relationship(back_populates='submissions')
    statuses: Mapped[list["Status"]] = relationship(back_populates='submission')
    def serialize(self):
        return {
            "id": self.id,
            "description": self.description,
            "response_url": self.response_url,
            "todo_id": self.todo_id,
            "student_id": self.student_id
        }


class Status(db.Model):
    __tablename__ = 'status'
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey('submission.id'), nullable=False)
    submission: Mapped["Submission"] = relationship(back_populates='statuses')
    state = mapped_column(SQLEnum('PENDING', 'APPROVED', 'REJECTED', name='status_enum'), nullable=False, default='PENDING')
    feedback: Mapped[str] = mapped_column(String(255))
    teacher_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    teacher: Mapped["User"] = relationship(back_populates='statuses')
    def serialize(self):
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "state": self.state,
            "feedback": self.feedback,
            "teacher_id": self.teacher_id
        }


class Reading(db.Model):
    __tablename__ = 'reading'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    teacher: Mapped["User"] = relationship(back_populates='readings')
    group_id: Mapped[int] = mapped_column(ForeignKey('group.id'), nullable=False)
    group: Mapped["Group"] = relationship(back_populates='readings')

    def __repr__(self):
        return f'Lectura: {self.title}'

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "La asigno el profesor": self.teacher,
            "Grupo asignado": self.group
        }
    

