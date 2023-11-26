from flask import Flask
from models import Post, Tag, Category, db, Budget
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finances.db'
db.init_app(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Создаем примеры категорий
        category1 = Category(name='Медицина')
        category2 = Category(name='Обучение')
        category3 = Category(name='Продукты')
        category4 = Category(name='Зарплата')

        # Добавляем категории в базу
        db.session.add(category1)
        db.session.add(category2)
        db.session.add(category3)
        db.session.add(category4)
        db.session.commit()

        # Создаем примеры тегов
        tag1 = Tag(name='Расходы')
        tag2 = Tag(name='Доходы')

        # Добавляем теги в базу
        db.session.add(tag1)
        db.session.add(tag2)
        db.session.commit()

        # Создаем пример бюджета
        budget = Budget(sum=0.00)
        db.session.add(budget)
        db.session.commit()

        # Тестовые посты
        post1 = Post(title='АСПИРИН',
            content=30,
            date=datetime.utcnow(), category_id=category1.id, budget=budget)
        post2 = Post(title='',
            content=20.5,
            date=datetime.utcnow(), category_id=category2.id, budget=budget)
        post3 = Post(title='',
            content=3,
            date=datetime.utcnow(), category_id=category3.id, budget=budget)

        # Добавляем теги к постам
        post1.tags.append(tag1)
        post2.tags.append(tag2)
        post3.tags.append(tag1)

        # Сохраняем посты в БД
        db.session.add(post1)
        db.session.add(post2)
        db.session.add(post3)
        db.session.commit()
