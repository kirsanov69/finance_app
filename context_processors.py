from models import Budget

def inject_budget():
    budget = Budget.query.order_by(Budget.id.desc()).first()  # Получаем текущий бюджет
    return dict(budget=budget)
