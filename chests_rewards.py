import random


def usual_reward():  # Здесь прописано соответствие фраз и картинок Обычных наград.
    usualrewards = {
        '45': {'слот под Арчвинг.': 'https://cdn.discordapp.com/attachments/872834857082970133/872837396000030780/slot-pod-archwing.png', 'слот под стража.': 'https://cdn.discordapp.com/attachments/872834857082970133/872837497711890442/slot-pod-strazha.png', 'слот под оружие.': 'https://cdn.discordapp.com/attachments/872834857082970133/872837632445546516/slot-pod-oruzhie.png'},
        '35': {'15 платины.': 'https://cdn.discordapp.com/attachments/872834857082970133/872838163553464390/15-pl.png', '20 платины.': 'https://cdn.discordapp.com/attachments/872834857082970133/872838312044425277/20-pl.png'},
        '30': {'крепёж на оружие.': 'https://cdn.discordapp.com/attachments/872834857082970133/872838507813568652/krepezh.png', 'катализатор Орокин. ': 'https://cdn.discordapp.com/attachments/585041003967414272/686893122155708453/catalizator.png', 'реактор Орокин.': 'https://cdn.discordapp.com/attachments/585041003967414272/686893125041389570/reactor.png', 'адаптер Эксилус для оружия.': 'https://cdn.discordapp.com/attachments/585041003967414272/686892875312529481/eksilus-na-orujie.png', 'слот под Варфрейма!': 'https://cdn.discordapp.com/attachments/585041003967414272/686890018530394117/slot-pod-warfreima.png'},
        '25': {'30 пл.': 'https://cdn.discordapp.com/attachments/872834857082970133/872839309865156628/30-pl.png', 'увеличение шанса выпадения ресурсов.': 'https://cdn.discordapp.com/attachments/585041003967414272/686892637805871116/shans-vipadeniya.png', 'умножитель ресурсов.': 'https://cdn.discordapp.com/attachments/585041003967414272/686891780465098833/umnojitel-resursov.png', 'множитель синтеза.': 'https://cdn.discordapp.com/attachments/585041003967414272/686891782142820372/umnojitel-sinteza.png','бустер на кредиты.': 'https://cdn.discordapp.com/attachments/585041003967414272/686891777932001290/umnojitel-creditov.png'},
        '20': {'кусок брони для варфрейма.': 'https://cdn.discordapp.com/attachments/872834857082970133/872840073614348348/kusok-broni.png'},
        '10': {'золотой ключ.': 'https://cdn.discordapp.com/attachments/872840127318212609/872887186792513536/2f22310639486436.png'},
        'пустой сундук.': 'https://cdn.discordapp.com/attachments/872840157362008065/872855092380983416/1db40890dff1de9f.png'
    }
    win_lose_roll = random.randint(1,100)
    if win_lose_roll < 65:
        return 'пустой сундук.', usualrewards['пустой сундук.']
    else:
        grade = random.choices(list(usualrewards.keys()), weights=[60,35,30,25,20,10,0])[0]
        ret = random.choice(list(usualrewards[grade].keys()))
        return ret, usualrewards[grade][ret]


def gold_reward(): # Здесь прописано соответствие фраз и картинок Золотых наград.
    goldlrewards = {
        '50': {'аксессуар - скин/сугатра!': 'https://cdn.discordapp.com/attachments/872840127318212609/872852153411178606/aksessuar.png', 'шазин.': 'https://cdn.discordapp.com/attachments/872840127318212609/872852316422823986/shazin.png', 'анимация': 'https://cdn.discordapp.com/attachments/872840127318212609/872853289962700840/animatsiya.png'},
        '40': {'50 платины!': 'https://cdn.discordapp.com/attachments/872840127318212609/872853607010164746/50-pl.png'},
        '35': {'палитра!': 'https://cdn.discordapp.com/attachments/585041003967414272/686894646068117514/palitra.png'},
        '30': {'форма-аура!': 'https://cdn.discordapp.com/attachments/872840127318212609/872853883251216464/forma-aura.png'},
        '25': {'броня на Кават/Кубрау или генно-маскирующий набор!': 'https://cdn.discordapp.com/attachments/872840127318212609/872854249258766356/bronya-kavat.png'},
        '20': {'100 платины!': 'https://cdn.discordapp.com/attachments/872840127318212609/872854359438950420/100-pl.png', 'сандана!': 'https://cdn.discordapp.com/attachments/872840127318212609/872854450421792828/sandana.png'}
    }
    grade = random.choices(list(goldlrewards.keys()), weights=[50, 40, 35, 30, 25, 20])[0]
    ret = random.choice(list(goldlrewards[grade].keys()))
    return ret, goldlrewards[grade][ret]