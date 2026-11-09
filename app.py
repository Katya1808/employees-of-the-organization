import os
import random
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from database import db, Employee, Department
from sqlalchemy.orm import joinedload
from faker import Faker

load_dotenv()
fake = Faker('ru_RU')

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)

LEVELS = [
    ("Генеральный директор", 1200000, 1),
    ("Менеджер", 300000, 4),
    ("Тимлид", 200000, 15),
    ("Старший разработчик", 150000, 30),
    ("Разработчик", 80000, 100)
]

with app.app_context():
    db.drop_all()
    db.create_all()

    development = Department(name="Разработка")
    hr = Department(name="Рекрутинг")
    db.session.add_all([development, hr])
    db.session.commit()

    ceo = Employee(fullname="Иван Иванович Иванов", position="Генеральный директор", salary=1200000,
                   department=development, manager_id=None)
    db.session.add(ceo)
    db.session.commit()

    db.session.add(Employee(fullname="Мария Алексеевна Петрова", position="Старший разработчик", salary=150000,
                            department=development, manager_id=ceo.id))
    db.session.add(
        Employee(fullname="Петр Сергеевич Иванов", position="Разработчик", salary=80000, department=development,
                 manager_id=ceo.id))
    db.session.add(Employee(fullname="Тамара Евгеньевна Сидорова", position="Менеджер", salary=300000, department=hr,
                            manager_id=ceo.id))
    db.session.commit()

    total_created = 4
    for position, salary, count in LEVELS[1:]:
        for i in range(count):
            new_employee = Employee(
                fullname=fake.name(),
                position=position,
                salary=salary,
                department=development,
                manager_id=ceo.id
            )
            db.session.add(new_employee)
            total_created += 1

    db.session.commit()
    print(f"✅ База данных успешно заполнена! Всего создано сотрудников: {total_created}")


@app.route("/")
def all_employees():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    search_query = request.args.get('search', '').strip()

    allowed_columns = ['id', 'fullname', 'position', 'salary', 'added']
    if sort_by not in allowed_columns: sort_by = 'id'
    if order not in ['asc', 'desc']: order = 'asc'

    sort_column = getattr(Employee, sort_by).desc() if order == 'desc' else getattr(Employee, sort_by).asc()

    query = Employee.query.options(joinedload(Employee.department), joinedload(Employee.manager))
    if search_query:
        query = query.filter(Employee.fullname.ilike(f'%{search_query}%'))

    pagination = query.order_by(sort_column).paginate(page=page, per_page=50, error_out=False)

    # НОВОЕ: Получаем список всех сотрудников (только id и fullname) для выпадающего списка
    # Это легкий запрос, который не нагрузит память даже при 50 000 записей
    all_employees_list = Employee.query.with_entities(Employee.id, Employee.fullname).all()

    return render_template(
        "all_employees.html",
        pagination=pagination,
        current_sort=sort_by,
        current_order=order,
        search_query=search_query,
        all_employees_list=all_employees_list  # <-- Передаем список в шаблон
    )


# НОВОЕ: Маршрут для обновления начальника
@app.route("/update_manager/<int:employee_id>", methods=["POST"])
def update_manager(employee_id):
    new_manager_id = request.form.get("new_manager_id")

    # Если выбрано "Без начальника", сохраняем NULL (None)
    if new_manager_id == "None" or new_manager_id == "":
        new_manager_id = None
    else:
        new_manager_id = int(new_manager_id)

    # Находим сотрудника и обновляем его начальника
    employee = Employee.query.get_or_404(employee_id)
    employee.manager_id = new_manager_id
    db.session.commit()

    # Возвращаем пользователя на ту же страницу, откуда он пришел (сохраняя поиск и сортировку)
    return redirect(request.referrer or url_for("all_employees"))


@app.route("/department/<int:department_id>")
def employee_by_department(department_id):
    department = Department.query.get_or_404(department_id)
    page = request.args.get('page', 1, type=int)
    pagination = Employee.query.filter_by(department_id=department.id).paginate(page=page, per_page=50, error_out=False)
    return render_template("employee_by_department.html", department_name=department.name, pagination=pagination)



if __name__ == '__main__':
    app.run(debug=True)