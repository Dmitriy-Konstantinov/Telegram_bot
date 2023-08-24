import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler
from datetime import datetime, timedelta
import json


TOKEN_BOT = '6631587700:AAGdFmZbiN0QzpjejG-sOuz0xv5WsaJvylU'


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def save_data():
    with open('budget_data.json', 'w') as file:
        data_to_save = {
            "categories": {category_name: {"amount": category.amount, "exp_by_dates": {
                date.strftime("%d-%m-%Y"): value for date, value in category.exp_by_dates.items()
            }} for category_name, category in categories.items()},
            "income": {category_name: {date.strftime("%d-%m-%Y"): value for date, value in category_data.items()
                                       } for category_name, category_data in income.items()}
        }
        json.dump(data_to_save, file)


def load_data():
    try:
        with open('budget_data.json', 'r') as file:
            data = json.load(file)
            for category_name, category_data in data["categories"].items():
                category = categories.get(category_name)
                if category:
                    category.amount = category_data["amount"]
                    category.exp_by_dates = {datetime.strptime(date_str, "%d-%m-%Y"): value
                                             for date_str, value in category_data["exp_by_dates"].items()}
            income.update(data["income"])
    except FileNotFoundError:
        pass


class Category:
    def __init__(self, name: str, amount: int):
        self.name = name
        self.amount = amount
        self.exp_by_dates = {}


food = Category('Еда', 0)
transport = Category('Транспорт', 0)
clothes = Category('Одежда', 0)
entertainment = Category('Развлечения', 0)

categories = {food.name: food,
              transport.name: transport,
              clothes.name: clothes,
              entertainment.name: entertainment
              }

income = {}


async def start(update: Update, context: CallbackContext) -> None:
    logging.info('Command "start" was triggered')
    await update.message.reply_text(
        'Добро пожаловать в ваш личный бюджет.\n'
        'Список команд: \n'
        'Показать список доступных команд: /help\n'
        'Показать доступные категории затрат: /categories_list\n'
        'Добавить расходы: /add_expenses\n'
        'Добавить доходы: /add_income\n'
        'Посмотреть статистику расходов за день/неделю/месяц/год: /statistics_expenses\n'
        'Посмотреть статистику доходов за день/неделю/месяц/год: /statistics_income\n'
        'Удалить расходы: /delete_expenses\n'
        'Удалить доходы: /delete_income\n'
    )


async def categories_list(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    await update.message.reply_text(food.name)
    await update.message.reply_text(transport.name)
    await update.message.reply_text(clothes.name)
    await update.message.reply_text(entertainment.name)


async def add_expenses(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    message_parts = " ".join(context.args).split()

    try:
        date = datetime.strptime(message_parts[2], "%d-%m-%Y")
        categories[message_parts[0]].amount += int(message_parts[1])
        categories[message_parts[0]].exp_by_dates.setdefault(date, int(message_parts[1]))
        await update.message.reply_text(f'Расходы в размере {message_parts[1]} грн. были добавлены в категорию '
                                        f'{message_parts[0]}.')
        save_data()
    except (KeyError, IndexError, ValueError):
        await update.message.reply_text('Введите сообщение в формате: {Категория расходов} {сумма} {дд-мм-гггг}')


async def statistics_expenses(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    message_parts = " ".join(context.args).split()
    total = 0
    if len(message_parts) > 0:
        category = categories[message_parts[0]]
    else:
        pass

    if len(message_parts) > 1:
        period = message_parts[1]
        today = datetime.now()
        start_date = datetime

        if period == 'день':
            start_date = today - timedelta(days=1)
        elif period == 'неделя':
            start_date = today - timedelta(days=7)
        elif period == 'месяц':
            start_date = today - timedelta(days=30)
        elif period == 'год':
            start_date = today - timedelta(days=365)
        else:
            await update.message.reply_text('Некорректный период')

        for date, value in category.exp_by_dates.items():
            if start_date <= date <= today:
                total += value

        await update.message.reply_text(str(total))

    elif len(message_parts) == 1:
        await update.message.reply_text(str(category.amount))

    elif len(message_parts) == 0:
        await update.message.reply_text(f'{food.name}: {food.amount} грн.')
        await update.message.reply_text(f'{transport.name}: {transport.amount} грн.')
        await update.message.reply_text(f'{clothes.name}: {clothes.amount} грн.')
        await update.message.reply_text(f'{entertainment.name}: {entertainment.amount} грн.')


async def delete_expenses(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_message = " ".join(context.args)

    try:
        category = categories[user_message]
        category.exp_by_dates = {}
        category.amount = 0
        await update.message.reply_text(f'Категория {user_message} была очищена.')
        save_data()
    except (KeyError, ValueError):
        await update.message.reply_text('Укажите название категории затрат.')


async def add_income(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    message_parts = " ".join(context.args).split()

    try:
        category = message_parts[0]
        profit = int(message_parts[1])
        date = datetime.strptime(message_parts[2], "%d-%m-%Y")

        if category not in income:
            income[category] = {}

        if date in income[category]:
            income[category][date] += profit
        else:
            income[category][date] = profit

        await update.message.reply_text(f'Доходы в размере {profit} грн. были добавлены в категорию '
                                        f'{category}.')
        save_data()
    except (KeyError, IndexError, ValueError):
        await update.message.reply_text('Введите сообщение в формате: {Категория доходов} {сумма} {дд-мм-гггг}')


async def statistics_income(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    message_parts = " ".join(context.args).split()
    total = 0
    if len(message_parts) > 0:
        category = income[message_parts[0]]
    else:
        pass

    if len(message_parts) > 1:
        period = message_parts[1]
        today = datetime.now()
        start_date = datetime

        if period == 'день':
            start_date = today - timedelta(days=1)
        elif period == 'неделя':
            start_date = today - timedelta(days=7)
        elif period == 'месяц':
            start_date = today - timedelta(days=30)
        elif period == 'год':
            start_date = today - timedelta(days=365)
        else:
            await update.message.reply_text('Некорректный период')

        for date, value in category.items():
            if start_date <= date <= today:
                total += value

        await update.message.reply_text(str(total))

    elif len(message_parts) == 1:
        for date, value in category.items():
            total += value

        await update.message.reply_text(str(total))

    elif len(message_parts) == 0:
        for key, value in income.items():
            total = sum(value.values())
            await update.message.reply_text(f'{key}: {total} грн.')


async def delete_income(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_message = " ".join(context.args)
    if user_message in income:
        income[user_message] = {}
        await update.message.reply_text(f'Категория {user_message} была очищена.')
        save_data()
    else:
        await update.message.reply_text('Укажите название категории доходов.')


def run():
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    logging.info('Application build successfully.')

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', start))
    app.add_handler(CommandHandler('categories_list', categories_list))
    app.add_handler(CommandHandler('add_expenses', add_expenses))
    app.add_handler(CommandHandler('add_income', add_income))
    app.add_handler(CommandHandler('statistics_expenses', statistics_expenses))
    app.add_handler(CommandHandler('statistics_income', statistics_income))
    app.add_handler(CommandHandler('delete_expenses', delete_expenses))
    app.add_handler(CommandHandler('delete_income', delete_income))

    app.run_polling()


if __name__ == '__main__':
    load_data()
    run()
