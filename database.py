from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Integer, nullable=False)
    added = db.Column(db.DateTime, nullable=False, default=func.now())
    department_id = db.Column(db.Integer, db.ForeignKey("department.id", ondelete="SET NULL"), nullable=True)
    department = relationship("Department", back_populates="employees")
    manager_id = db.Column(db.Integer, db.ForeignKey("employee.id", ondelete="SET NULL"), nullable=True)
    manager = relationship("Employee", remote_side=[id], backref="subordinates")

    def __repr__(self):
        return f"Employee(fullname={self.fullname!r})"

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    employees = relationship("Employee", back_populates="department", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Department(name={self.name!r})"


