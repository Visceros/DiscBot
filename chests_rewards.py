import random


def usual_reward():  # Здесь прописано соответствие фраз и картинок Обычных наград.
    usualrewards = {
        '45': {'слот под Арчвинг.': 'slot-pod-archwing.png', 'слот под стража.': 'slot-pod-strazha.png', 'слот под оружие.': 'slot-pod-oruzhie.png'},
        '35': {'15 платины.': '15-pl.png', '20 платины.': '20-pl.png'},
        '30': {'крепёж на оружие.': 'krepezh.png', 'катализатор Орокин. ': 'catalizator.png', 'реактор Орокин.': 'reactor.png', 'адаптер Эксилус для оружия.': 'eksilus-na-orujie.png', 'слот под Варфрейма!': 'slot-pod-warfreima.png'},
        '25': {'30 пл.': '30-pl.png', 'увеличение шанса выпадения ресурсов.': 'shans-vipadeniya.png', 'умножитель ресурсов.': 'umnojitel-resursov.png', 'множитель синтеза.': 'umnojitel-sinteza.png','бустер на кредиты.': 'umnojitel-creditov.png'},
        '20': {'кусок брони для варфрейма.': 'kusok-broni.png'},
        '10': {'золотой ключ.': 'golden-key.png'},
        'пустой сундук.': 'empty.png'
    }
    win_lose_roll = random.randint(1,100)
    if win_lose_roll < 80:
        return 'пустой сундук.', usualrewards['пустой сундук.']
    else:
        grade = random.choices(list(usualrewards.keys()), weights=[60,35,30,25,20,10,0])[0]
        ret = random.choice(list(usualrewards[grade].keys()))
        return ret, usualrewards[grade][ret]


def gold_reward(): # Здесь прописано соответствие фраз и картинок Золотых наград.
    goldlrewards = {
        '50': {'аксессуар - скин/сугатра!': 'aksessuar.png', 'шазин.': 'shazin.png', 'анимация': 'animatsiya.png'},
        '40': {'50 платины!': '50-pl.png'},
        '35': {'палитра!': 'palitra.png'},
        '30': {'форма-аура!': 'forma-aura.png'},
        '25': {'броня на Кават/Кубрау или генно-маскирующий набор!': 'bronya-kavat.png'},
        '20': {'100 платины!': '100-pl.png', 'сандана!': 'sandana.png'}
    }
    grade = random.choices(list(goldlrewards.keys()), weights=[50, 40, 35, 30, 25, 20])[0]
    ret = random.choice(list(goldlrewards[grade].keys()))
    return ret, goldlrewards[grade][ret]