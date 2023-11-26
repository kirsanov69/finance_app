from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
db = SQLAlchemy()

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    posts = db.relationship('Post', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sum = db.Column(db.Integer)
    post = db.relationship('Post', back_populates='budget')

    @staticmethod
    def get_current_budget_from_database():
    # Получаем текущий бюджет из базы данных
        current_budget = Budget.query.order_by(Budget.id.desc()).first()

    # Если бюджет не найден, создаем новый с начальным значением
        if current_budget is None:
            current_budget = Budget(sum=0.00)  # Замените на ваше начальное значение
            db.session.add(current_budget)
            db.session.commit()

        return current_budget

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    posts = db.relationship('Post', secondary='post_tag', backref='tags', lazy=True)

    def __repr__(self):
        return f'<Tag {self.name}>'

post_tag = db.Table('post_tag',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)



class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    content = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    budget = db.relationship('Budget', back_populates='post')



    def repr(self):
        return f'<Post {self.title}>'

    @classmethod
    def newest_first(cls):
        return cls.query.order_by(cls.date.desc())

class NewCategoryForm(FlaskForm):
    name = StringField('Название категории')
    submit = SubmitField('Добавить категорию')
