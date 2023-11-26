from models import Post, db
from sqlalchemy import func
import json


# Пример запроса для получения сумм за каждый день
def get_sums_for_calendar():
    # Ваш запрос для получения данных о суммах за каждый день
    # Пример: SELECT date, SUM(amount) FROM transactions GROUP BY date;
    sums = db.session.query(Post.date, func.sum(Post.content)).group_by(Post.date).all()
    return sums

def prepare_data_for_calendar(sums):
    events = []



    for date, amount in sums:
        formatted_date = date.strftime('%Y-%m-%d')
        event = {
            'title': f'Сумма: {amount}',
            'start': formatted_date,
            'end': formatted_date,
        }
        events.append(event)

    return json.dumps(events)

