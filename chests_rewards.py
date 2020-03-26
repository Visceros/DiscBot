import random

def usual_reward():  # Здесь прописано соответствие фраз и картинок Обычных наград.
    usualrewards = {
        'Ты выиграл 15 платины! А ведь, в соседнем сундуке лежал намного больший приз.': 'https://cdn.discordapp.com/attachments/585041003967414272/686865238158606352/15-pl.png',
        'Ты выиграл 20 платины. С каждым участием шанс на получение главного приза становится больше.': 'https://cdn.discordapp.com/attachments/585041003967414272/686865241983811594/20-pl.png',
        'Ты выиграл 30 платины. Участвуй чаще, чтобы увеличить шанс на получение главного приза!': 'https://cdn.discordapp.com/attachments/585041003967414272/686865242617020452/30-pl.png',
        'Ты выиграл 40 платины. Прекрасный выигрыш!': 'https://cdn.discordapp.com/attachments/585041003967414272/686865244483878912/40-pl.png',
        'Ого, что это тут?! Слот под оружие!': 'https://cdn.discordapp.com/attachments/585041003967414272/686890014256267264/slot-pod-oruzhie.png',
        'Вот это да, - Слот под Варфрейма!': 'https://cdn.discordapp.com/attachments/585041003967414272/686890018530394117/slot-pod-warfreima.png',
        'Космос зовёт, так получи под Арчвинг слот!': 'https://cdn.discordapp.com/attachments/585041003967414272/686890012343795744/slot-pod-archwing.png',
        'Отличному игроку, отличный - Слот под Стража!': 'https://cdn.discordapp.com/attachments/585041003967414272/686890017024376842/slot-pod-strazha.png',
        'Смотри, это же кусок брони! Ты можешь получить любой кусок в виде наплечников, наголенников и нагрудника на выбор.': 'https://cdn.discordapp.com/attachments/585041003967414272/686890718194827284/kusok-broni.png',
        'Вау! Это же бустер на кредиты! Это твой шанс собрать пати и поднять кредитов на Индексе!': 'https://cdn.discordapp.com/attachments/585041003967414272/686891777932001290/umnojitel-creditov.png',
        'Ух ты! Это же бустер на синтез! Настало время идти качаться!': 'https://cdn.discordapp.com/attachments/585041003967414272/686891782142820372/umnojitel-sinteza.png',
        'Ого! Это же бустер на ресурсы! Пора фармить ресурсы, Куву и отголоски!': 'https://cdn.discordapp.com/attachments/585041003967414272/686891780465098833/umnojitel-resursov.png',
        'Супер! Это увеличение шанса выпадения ресурсов! Пора идти на выживание! И возьми ребят из клана!': 'https://cdn.discordapp.com/attachments/585041003967414272/686892637805871116/shans-vipadeniya.png',
        'Тебе выпадает Адаптер Эксилус для Варфрейма.': 'https://cdn.discordapp.com/attachments/585041003967414272/686892860707962990/eksilus.png',
        'Тебе выпадает Адаптер Эксилус для оружия.': 'https://cdn.discordapp.com/attachments/585041003967414272/686892875312529481/eksilus-na-orujie.png',
        'Реактор Орокин озаряет все своим светом.': 'https://cdn.discordapp.com/attachments/585041003967414272/686893125041389570/reactor.png',
        'Катализатор Орокин озаряет все своим светом.': 'https://cdn.discordapp.com/attachments/585041003967414272/686893122155708453/catalizator.png',
        'Волшебное сияние дарит вам крепеж на ваше оружие ближнего боя.': 'https://cdn.discordapp.com/attachments/585041003967414272/686893331103744022/krepezh.png',
    }
    ret = random.choice(list(usualrewards.keys()))
    return ret, usualrewards[ret]

def gold_reward(): # Здесь прописано соответствие фраз и картинок Золотых наград.
    goldlrewards = {
        'И в сундуке вы находите 50 платины! Поздравляю! Но выбрав соседний сундук, вы могли получить аж 1,500 платины.': 'https://cdn.discordapp.com/attachments/585041003967414272/686894139371028521/50-pl.png',
        'И в сундуке вы находите 100 платины! Отличный выигрыш.': 'https://cdn.discordapp.com/attachments/585041003967414272/686894156857344023/100-pl.png',
        'И из сундука вываливается древняя броня на питомца. Теперь ваше животное будет в тепле!': 'https://cdn.discordapp.com/attachments/585041003967414272/686894390803038266/bronya-kavat.png',
        'И комнату наполняют чарующие звуки Шазина.': 'https://cdn.discordapp.com/attachments/585041003967414272/686894583363141647/shazin.png',
        'И радуга вырывается на свободу, заливая комнату ярким свечением. Из света появляется Палитра!': 'https://cdn.discordapp.com/attachments/585041003967414272/686894646068117514/palitra.png',
        'И вам в руки попадает красивая Сандана.': 'https://cdn.discordapp.com/attachments/585041003967414272/686894622244732933/sandana.png',
        'И из сгустков кинетической энергии появляется Анимация на варфрейма.': 'https://cdn.discordapp.com/attachments/585041003967414272/686894952013496340/animatsiya.png',
        'И сотканная из множества форм, появляется Форма-аура.': 'https://cdn.discordapp.com/attachments/585041003967414272/686894662124044328/forma-aura.png',
        'И на свет появляется аксессуар на Оружие!': 'https://cdn.discordapp.com/attachments/585041003967414272/686895370160308254/aksessuar.png'
    }
    ret = random.choice(list(goldlrewards.keys()))
    return ret, goldlrewards[ret]