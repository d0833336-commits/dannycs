import random
import os
from flask import Flask, render_template, request,session, redirect, url_for


base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))

app.secret_key = 'danny_secret_key_777'
user_name = "Danny"
user_weapon = "Калаш в КС!"

# Твой баланс, инвентарь и экономика
user_balance = 5335  # Твой актуальный баланс с последнего скриншота!
last_drop = "Пока ничего не произошло"
can_sell = False
user_inventory = []
roulette_result = ""  # Результат рулетки
upgrade_result = ""  # Результат апгрейда

# Базовые цены (для качества "Испытанное в боях")
weapons_base_prices = {
    "P250 | Песчаная дюна": 5,
    "Glock-18 | Горелка Бунзена": 15,
    "AK-47 | Затерянная земля": 50,
    "M4A4 | Безлюдный космос": 150,
    "AWP | Азимов": 500,
    "★ Нож! ★ Керамбит | Кровавая паутина": 5000
}

quality_multipliers = {
    "Прямо с завода": 2.0,
    "Немного поношенное": 1.3,
    "Испытанное в боях": 1.0,
    "Поношенное": 0.7,
    "Закаленное в боях": 0.4
}

rarity_order = [
    "P250 | Песчаная дюна",
    "Glock-18 | Горелка Бунзена",
    "AK-47 | Затерянная земля",
    "M4A4 | Безлюдный космос",
    "AWP | Азимов",
    "★ Нож! ★ Керамбит | Кровавая паутина"
]


def get_quality_by_float(wear):
    if wear <= 0.07:
        return "Прямо с завода"
    elif wear <= 0.15:
        return "Немного поношенное"
    elif wear <= 0.38:
        return "Испытанное в боях"
    elif wear <= 0.45:
        return "Поношенное"
    else:
        return "Закаленное в боях"


@app.route('/')
def home():
    global user_balance, last_drop, can_sell, user_inventory, roulette_result, upgrade_result
    if 'balance' not in session:
        session['balance'] = 5335  # Твой стартовый баланс с прошлого скриншота!
    if 'inventory' not in session:
        session['inventory'] = []
    return render_template('index.html', balance=session['balance'], drop=last_drop, can_sell=can_sell,
                           inventory=session['inventory'], roulette_result=roulette_result,
                           upgrade_result=upgrade_result)


@app.route('/open_case', methods=['POST'])
def open_case():
    global last_drop, can_sell, roulette_result, upgrade_result
    # Проверяем личный баланс конкретного пользователя
    if 'balance' not in session:
        session['balance'] = 5335
    if 'inventory' not in session:
        session['inventory'] = []

    if session['balance'] >= 30:
        session['balance'] -= 30  # Списываем бабки только у того, кто нажал!
        weapons = list(weapons_base_prices.keys())
        drops = random.choices(weapons, weights=[50, 30, 13, 5, 1.8, 0.2])[0]
        base_name = drops
        wear = round(random.uniform(0.0, 1.0), 4)
        quality = get_quality_by_float(wear)
        final_price = int(weapons_base_prices[base_name] * quality_multipliers[quality])

        last_drop = f"{base_name} ({quality}) [Float: {wear}] - Цена: {final_price} руб."

        # Добавляем пушку строго в личный инвентарь этого игрока
        session['inventory'].append(last_drop)
        session.modified = True  # Говорим Flask, что инвентарь обновился!
        can_sell = True

    return render_template('index.html', balance=session['balance'], drop=last_drop, can_sell=can_sell,
                           inventory=session['inventory'], roulette_result=roulette_result,
                           upgrade_result=upgrade_result)
@app.route('/add_to_inventory', methods=['POST'])
def add_to_inventory():
    global last_drop, can_sell, user_inventory
    if can_sell and "Цена:" in last_drop:
        user_inventory.append(last_drop)
        last_drop = "📥 Предмет успешно добавлен в инвентарь!"
        can_sell = False
    return render_template('index.html', balance=user_balance, drop=last_drop, can_sell=can_sell,
                           inventory=user_inventory, roulette=roulette_result, upgrade=upgrade_result)


@app.route('/sell', methods=['POST'])
def sell_skin():
    global last_drop, can_sell, roulette_result, upgrade_result
    if 'balance' not in session:
        session['balance'] = 5335

    try:
        # Умный бэкэнд сессий: вытаскиваем цену из последнего дропа
        price = int(last_drop.split("Цена: ")[1].split(" руб."))
        session['balance'] += price
    except:
        session['balance'] += 500

    return render_template('index.html', balance=session['balance'], drop=last_drop, can_sell=can_sell,
                           inventory=session.get('inventory', []), roulette_result=roulette_result,
                           upgrade_result=upgrade_result)



@app.route('/sell_from_inventory', methods=['POST'])
def sell_from_inventory():
            global user_balance, user_inventory
            item_index = int(request.form.get('item_index'))
            if 0 <= item_index < len(user_inventory):
                item_text = user_inventory[item_index]
                try:
                    price = int(item_text.split("Цена: ")[1].split(" руб.")[0])
                    user_balance += price
                    user_inventory.pop(item_index)
                except:
                    pass
            return render_template('index.html', balance=user_balance, drop=last_drop, can_sell=can_sell,
                                   inventory=user_inventory, roulette_result=roulette_result,
                                    upgrade_result=upgrade_result)

@app.route('/run_roulette', methods=['POST'])
def run_roulette():
    global user_balance, roulette_result
    bet_color = request.form.get('color')
    bet_amount = 100

    if user_balance >= bet_amount:
        user_balance -= bet_amount
        num = random.randint(1, 100)
        if num <= 6: rolled_color = "green"
        elif num <= 53: rolled_color = "red"
        else: rolled_color = "black"

        if rolled_color == bet_color:
            if bet_color == "green":
                win_money = bet_amount * 14
                user_balance += win_money
                roulette_result = f"🟢 МЕГА-КУШ! Выпало ЗЕЛЁНОЕ! Ты выиграл {win_money} руб.!"
            else:
                win_money = bet_amount * 2
                user_balance += win_money
                roulette_result = f"🎉 ПОБЕДА! Выпало {rolled_color.upper()}! Ты выиграл {win_money} руб.!"
        else:
            roulette_result = f"😢 Проигрыш... Выпало {rolled_color.upper()}. Твоя ставка сгорела."
    return render_template('index.html', balance=user_balance, drop=last_drop, can_sell=can_sell, inventory=user_inventory, roulette=roulette_result, upgrade=upgrade_result)

# --- ЛОГИКА РЕЖИМА АПГРЕЙД ---
@app.route('/run_upgrade', methods=['POST'])
def run_upgrade():
    global user_balance, user_inventory, upgrade_result

    if not user_inventory:
        upgrade_result = "❌ Твой инвентарь пуст! Нечего апгрейдить."
        return render_template('index.html', balance=user_balance, drop=last_drop, can_sell=can_sell, inventory=user_inventory, roulette=roulette_result, upgrade=upgrade_result)

    target_item = request.form.get('target') # Какую пушку хочет игрок
    target_base_price = weapons_base_prices[target_item]

    # Всегда берем самую первую пушку из инвентаря для апгрейда
    user_item_text = user_inventory[0]
    try:
        user_item_price = int(user_item_text.split("Цена: ")[1].split(" руб.")[0])
    except:
        user_item_price = 5

    if user_item_price >= target_base_price:
        upgrade_result = "❌ Выбранная цель должна быть дороже твоего предмета!"
        return render_template('index.html', balance=user_balance, drop=last_drop, can_sell=can_sell, inventory=user_inventory, roulette=roulette_result, upgrade=upgrade_result)

    # Рассчитываем честный шанс (цена твоей пушки / цена цели * 100)
    chance = round((user_item_price / target_base_price) * 100, 2)
    if chance > 80: chance = 80 # Ограничиваем максимальный шанс до 80%# Крутим колесо удачи
    roll = random.uniform(0, 100)
    if roll <= chance:
        # УСПЕХ! Сжигаем дешёвую пушку и выдаём дорогую!
        user_inventory.pop(0)
        wear = round(random.uniform(0.0, 0.1), 4) # Апгрейд даёт шикарный износ!
        quality = get_quality_by_float(wear)
        final_price = int(target_base_price * quality_multipliers[quality])

        new_item_text = f"{target_item} ({quality}) [Float: {wear}] — Цена: {final_price} руб."
        user_inventory.insert(0, new_item_text) # Вставляем на первое место
        upgrade_result = f"🔥 УСПЕШНЫЙ АПГРЕЙД! (Шанс {chance}%) Ты получил {target_item} ({quality})!"
    else:
        # НЕУДАЧА... Дешёвая пушка сгорает
        user_inventory.pop(0)
        upgrade_result = f"💥 Апгрейд взорвался! (Шанс был {chance}%) Твой предмет уничтожен."

    return render_template('index.html', balance=user_balance, drop=last_drop, can_sell=can_sell, inventory=user_inventory, roulette=roulette_result, upgrade=upgrade_result)

@app.route('/get_bonus', methods=['POST'])
def get_bonus():
    global user_balance
    user_balance += 100
    return render_template('index.html', balance=user_balance, drop=last_drop, can_sell=can_sell, inventory=user_inventory, roulette=roulette_result, upgrade=upgrade_result)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    global user_name, user_weapon
    if request.method == 'POST':
        user_name = request.form.get('nickname')
        user_weapon = request.form.get('weapon')
    return render_template('profile.html', name=user_name, weapon=user_weapon,balance = user_balance, inventory=user_inventory)

if __name__ == '__main__':
    port = int(os.environ.get('PORT',500))
    app.run(host='0.0.0.0', port=port)
    # Переменная, чтобы один игрок не вводил промокод бесконечно
    promo_used = 0


    @app.route('/promo')
    def activate_promo():
        global user_balance, promo_used
        code = request.args.get('code')

        if code == 'DANNY777':
            if promo_used == 0:
                user_balance += 1000
                promo_used = 1
                return "PROMO OK! +1000 RUB."
            else:
                return "ALREADY USED!"
        else:
            return "WRONG CODE!"
# Переменная для подкрутки (0 - выключена, 1 - включена)
admin_cheat = 0


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    global user_balance, admin_cheat
    message = ""

    if request.method == 'POST':
        password = request.form.get('password')
        # Проверяем секретный пароль босса
        if password == '7777':
            action = request.form.get('action')
            if action == 'add_money':
                user_balance += 50000
                message = "💰 Успешно начислено 50 000 руб!"
            elif action == 'toggle_cheat':
                admin_cheat = 1 if admin_cheat == 0 else 0
                status = "ВКЛЮЧЕНА" if admin_cheat == 1 else "ВЫКЛЮЧЕНА"
                message = f"🎰 Подкрутка ножей теперь {status}!"
        else:
            message = "❌ Неверный пароль администратора!"

    return render_template('admin.html', balance=user_balance, cheat=admin_cheat, message=message)

@app.route('/sell', methods=['POST'])
def sell_skin():
    # Код продажи: начисляет 1500 рублей за любой скин!
    # В следующих шагах мы свяжем это с твоим инвентарём
    return "Скин успешно продан! +1500 рублей!"