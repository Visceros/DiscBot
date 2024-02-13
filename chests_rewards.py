import random


def usual_reward():  # Здесь прописано соответствие фраз и картинок Обычных наград.
    usualrewards = {
        '45': {'слот под стража.': 'slot-pod-strazha.png', 'слот под оружие.': 'slot-pod-oruzhie.png', 'слот под Варфрейма!': 'slot-pod-warfreima.png', 'слот под оружие арчвинга!': 'slot-pod-oryzhie-archwing.png', 'слот под усилитель!':'slot-pod-usilitel.png', 'украшение сугатра!': 'aksessuar.png'},
        '35': {'катализатор Орокин. ': 'catalizator.png', 'реактор Орокин.': 'reactor.png', 'адаптер Эксилус для оружия.': 'eksilus-na-orujie.png'},
        '30': {'крепёж на оружие.': 'krepezh.png', 'адаптер мистификатора для ближнего боя': 'adapter-blizhnii-boi.png', 'адаптер мистификатора для основного оружия': 'adapter-osnovnoe.png', 'адаптер мистификатора для вторичного оружия': 'adapter-vtorichnoe.png'},
        '25': {'увеличение шанса выпадения ресурсов.': 'shans-vipadeniya.png', 'умножитель ресурсов.': 'umnojitel-resursov.png', 'умножитель синтеза.': 'umnojitel-sinteza.png','бустер на кредиты.': 'umnojitel-creditov.png', 'кусок брони для варфрейма.': 'kusok-broni.png'},
        '15': {'золотой ключ.': 'golden-key.png'},
        'пустой сундук.': 'empty.png'
    }
    win_lose_roll = random.randint(1,100)
    if win_lose_roll < 80:
        return 'пустой сундук.', usualrewards['пустой сундук.']
    else:
        grade = random.choices(list(usualrewards.keys()), weights=[60,35,30,25,15,0])[0]
        ret = random.choice(list(usualrewards[grade].keys()))
        return ret, usualrewards[grade][ret]


def gold_reward(): # Здесь прописано соответствие фраз и картинок Золотых наград.
    goldlrewards = {
        '50': {'анимация': 'animatsiya.png'},
        '35': {'палитра!': 'palitra.png'},
        '30': {'форма-аура!': 'forma-aura.png'},
        '20': {'сандана!': 'sandana.png'}
    }
    grade = random.choices(list(goldlrewards.keys()), weights=[50, 35, 30, 20])[0]
    ret = random.choice(list(goldlrewards[grade].keys()))
    return ret, goldlrewards[grade][ret]