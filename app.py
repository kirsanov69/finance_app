from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import session
from models import db, Category, Tag, Post, Budget, NewCategoryForm
from context_processors import inject_budget
from sqlalchemy import func, cast, Float, case
from sqlalchemy import extract
from flask_babel import Babel
from flask_babel import gettext as _
import datetime
from datetime import timedelta
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt


app = Flask(__name__)

app.config['LANGUAGES'] = ['en', 'es', 'ru']  # Список поддерживаемых языков

babel = Babel(app)

app.context_processor(inject_budget) #Импортируем функцию, чтобы бюджет по умолчанию был везде определен

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finances.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
db.init_app(app)


@app.route('/')
def index():
    posts = Post.newest_first().all()
    budget = Budget.query.first()
    return render_template('index.html', posts=posts, budget=budget)

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@app.route('/category/<int:category_id>')
def category(category_id):
    category = Category.query.get_or_404(category_id)

    # Вычисляем сумму бюджетов для выбранной категории
    total_budget_category = (
        db.session.query(func.sum(Post.content))
        .filter(Post.category_id == category_id)
        .scalar() or 0
    )
    posts = Post.query.filter_by(category_id=category_id).order_by(Post.date.desc()).all()

    return render_template('category.html', category=category, posts=posts, total_budget_category=total_budget_category)

@app.route('/tag/<int:tag_id>')
def tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    posts = Post.query.filter(Post.tags.any(id=tag_id)).order_by(Post.date.desc()).all()

    # Вычисляем сумму бюджетов по тегу в зависимости от типа тега
    total_budget_tag = (
        db.session.query(func.sum(Post.content))
        .join(Post.tags)
        .filter(Tag.id == tag_id)
        .group_by(Tag.id)
        .scalar() or 0
    )
    return render_template('tag.html', tag=tag, posts=posts, total_budget_tag = total_budget_tag)

@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    budget = Budget.query.order_by(Budget.id.desc()).first()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category_id = request.form['category']
        tag_ids = [int(tag_id) for tag_id in request.form.getlist('tags')]
         # Рассчитываем новую сумму бюджета после расхода
        expense_amount = float(request.form['content'])
         # Проверяем, есть ли тег "Расходы" в выбранных тегах
        if 'Расходы' in [tag.name for tag in Tag.query.filter(Tag.id.in_(tag_ids)).all()]:
            new_budget_sum = budget.sum - expense_amount  # Уменьшаем бюджет только если есть тег "Расходы"

        if 'Доходы' in [tag.name for tag in Tag.query.filter(Tag.id.in_(tag_ids)).all()]:
            new_budget_sum = budget.sum + expense_amount  # Увеичиваем бюджет только если есть тег "Доходы"

        # Обновляем значение суммы в текущем бюджете
        budget.sum = new_budget_sum
        post = Post(title=title, content=content, category_id=category_id, budget=budget)
        for tag_id in tag_ids:
            tag = Tag.query.get(tag_id)
            post.tags.append(tag)
        db.session.add(post)
        db.session.commit()
        flash('Запись создана!', 'success')
        return redirect(url_for('index'))
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('new_post.html', categories=categories, tags=tags, budget=budget)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        post.category_id = request.form['category']
        tag_ids = [int(tag_id) for tag_id in request.form.getlist('tags')]
        post.tags = []
        for tag_id in tag_ids:
            tag = Tag.query.get(tag_id)
            post.tags.append(tag)
        db.session.commit()
        flash('Запись обновлена!', 'success')
        return redirect(url_for('index'))
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('edit_post.html', post=post, categories=categories, tags=tags)

@app.route('/delete_post/<int:post_id>', methods=['GET', 'POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Запись удалена!', 'success')
    return redirect(url_for('index'))

@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    form = NewCategoryForm()

    if form.validate_on_submit():
        # Добавляем новую категорию в базу данных
        new_category = Category(name=form.name.data)
        db.session.add(new_category)
        db.session.commit()

        flash('Категория успешно добавлена!', 'success')
        return redirect(url_for('index'))  # Можно перенаправить на другую страницу

    return render_template('add_category.html', form=form)

@app.route('/delete_category/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Категория удалена!', 'success')
    return jsonify({'message': 'Категория удалена успешно'})

@app.route('/categories')
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@app.route('/calendar', methods=['GET', 'POST'])
def actions_by_month():
    if request.method == 'POST':
        # Получите выбранный месяц из формы
        selected_month = int(request.form.get('selected_month'))
        actions = Post.query.filter(extract('month', Post.date)==selected_month).all()

         # Группировка и агрегация по тегам (расходы и доходы)
        expenses = (
            db.session.query(func.sum(Post.content).label('total_expenses'))
            .join(Post.tags)
            .filter(Tag.name == 'Расходы', extract('month', Post.date) == selected_month)
            .scalar() or 0
        )

        incomes = (
            db.session.query(func.sum(Post.content).label('total_incomes'))
            .join(Post.tags)
            .filter(Tag.name == 'Доходы', extract('month', Post.date) == selected_month)
            .scalar() or 0
        )
         # Получаем данные по расходам
        expenses_data = (
            db.session.query(Category.name, func.sum(Post.content).label('total_expenses'))
            .join(Post.category)
            .join(Post.tags)
            .filter(Tag.name == 'Расходы', extract('month', Post.date) == selected_month)
            .group_by(Category.name)
            .all()
        )

        # Получаем данные по доходам
        incomes_data = (
            db.session.query(func.sum(Post.content).label('total_incomes'))
            .join(Post.tags)
            .filter(Tag.name == 'Доходы', extract('month', Post.date) == selected_month)
            .scalar() or 0
        )

        # Строим круговую диаграмму для расходов
        if expenses_data:
            plt.figure(figsize=(8, 8))
            labels_expenses = [item[0] for item in expenses_data]
            values_expenses = [item[1] for item in expenses_data]
            plt.pie(values_expenses, labels=labels_expenses, autopct='%1.1f%%', startangle=140)
            plt.title('Расходы по категориям')
            plt.axis('equal')  # Равные оси для сохранения формы круга
            img_path_expenses = 'static/images/expenses_pie_chart.png'
            plt.savefig(f'./{img_path_expenses}')
            plt.close()  # Закрываем график
        else:
            img_path_expenses = None

        # Строим круговую диаграмму для доходов
        plt.figure(figsize=(8, 8))
        labels_incomes = ['Доходы']
        values_incomes = [incomes_data]
        plt.pie(values_incomes, labels=labels_incomes, autopct='%1.1f%%', startangle=140)
        plt.title('Доходы')
        plt.axis('equal')  # Равные оси для сохранения формы круга
        img_path_incomes = 'static/images/incomes_pie_chart.png'
        plt.savefig(f'./{img_path_incomes}')
        plt.close()  # Закрываем график

        return render_template('actions_by_month.html', actions=actions, expenses=expenses, incomes=incomes, img_path_expenses=img_path_expenses, img_path_incomes=img_path_incomes)

    # Если метод запроса GET, просто отображаем форму выбора месяца
    return render_template('select_month.html')

@app.route('/set_locale/<locale>')
def set_locale(locale):
    session['locale'] = locale
    return redirect(request.referrer)

def get_locale():
    return session.get('locale', 'ru')  # По умолчанию 'ru', если язык не выбран

babel.init_app(app, locale_selector=get_locale)



@app.route('/diagram')
def all_categories_pie_chart():
    with app.app_context():
        # Получаем все категории
        categories = Category.query.all()

        # Вычисляем сумму бюджетов для каждой категории
        total_budgets = []
        labels = []
        for category in categories:
            if Tag.name == "Доходы":
                continue
            total_budget = (
                db.session.query(func.sum(Post.content))
                .filter(Post.category_id == category.id)
                .scalar() or 0
            )
            total_budgets.append(total_budget)
            labels.append(category.name)

        # Строим круговую диаграмму
        plt.figure(figsize=(8, 8))
        plt.pie(total_budgets, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.title('Расходы по категориям')
        plt.axis('equal')  # Равные оси для сохранения формы круга

        # Сохраняем диаграмму во временный файл
        img_path = 'static/images/all_categories_pie_chart.png'  # Путь к файлу, который будет доступен через статический URL
        plt.savefig(f'./{img_path}')
        plt.close()  # Закрываем график

        return render_template('diagram.html', img_path=img_path)

if __name__ == '__main__':
    app.run(debug=True)
