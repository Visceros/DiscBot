# coding: utf8

import discord
import asyncio   # check if installed
import io
import aiohttp
import random
import psycopg2  # check if installed
import os
from time import sleep
from discord.ext import commands
import logging

# ------- LOGGER FOR DEBUG PURPOSES
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
# ------- LOGGER FOR DEBUG PURPOSES

token = 'NTAzNTQ5MDA1ODMwMDI5MzEy.Du8B4w.jXHBly_o8-E1EJDYsgYMOmxVAhs'
prefix = '>'
des = 'A discord bot for doing some automatic things that I am to lazy to do myself.'
rgb_colors = ['ff0000', 'ff4800', 'ffaa00', 'ffe200', 'a5ff00', '51ff00', '00ff55', '00ffb6', '00fffc', '00bdff', '0055ff', '0600ff', '6700ff', '9f00ff', 'f200ff', 'ff0088', 'ff003b']
Client = discord.Client()
bot = commands.Bot(description=des, command_prefix=prefix)

# db_user = 'postgres'
# db_pwd = '32167'  # 32167 - пароль дома
# db = psycopg2.connect(
#     dbname='DiscBot_db',
#     user=db_user,
#     password=db_pwd,
#     host='',
#     port='5432'
# )
# cursor = db.cursor()
# cursor.execute('SELECT EXISTS(SELECT * FROM DiscBot_db.tables WHERE table_name=discord_users)')
# if cursor.fetchone()[0] is True:
#     pass
# else:
#     try:
#         cursor.execute('''CREATE TABLE discord_users
#             Id INT PRIMARY KEY NOT NULL,
#             Name TEXT NOT NULL,
#             Join_date TIMESTAMP
#             Activity INT DEFAULT 0,
#             Gold INT DEFAULT 0);''')
#     except Exception as e:
#         print(e)
#         print(e.__traceback__)


class User:
    def __init__(self):
        self.id = None
        self.username = None
        self.join_date = None
        self.activity = None
        self.gold = None

    def add(self, user, activity=0, gold=0):  #добавляем юзера как строку в БД
        """We use separate class "User" for our discord server users -  to simplify the data handling
        at least 2 *args should be given: 1)user id 2) user name (nick)"""
        self.id = user.id
        self.username = user.name
        self.join_date = user.joined_at  # вписать сюда обращение к АПИ для получения даты присоединения к серверу
        self.activity = activity
        self.gold = gold
        cursor.execute('INSERT ')

    def update(self, user, gold):  #обновляем юзверя - ник, если изменился, начисляем деньги и активность.
        self.gold = gold
        self.id = user.id #вероятно неправильно, надо - передаём ник, по нему ищем юзер_айди в дискорде, далее если его ник != нику в ДБ - перезаписываем
        cursor.execute(f'SELECT TOP 1 FROM TABLE discord_users WHERE Id={self.user_id}') #нужно доработать согласно комменту выше
        record = cursor.fetchone()
        #дописать дальше обновление - идея, передаём ник, по нему ищем юзер_айди в дискорде, далее если какая-то инфа изменилась - перезаписываем

    # def delete(self, name):  #если юзера забанили или удалили с сервера, удаляем из ДБ (под вопросом)
    #     self.name = name
    #     pass

    def show(self, user):
        self.user_id = user.id
        cursor.execute(f'SELECT TOP 1 FROM TABLE discord_users WHERE Id={self.user_id}')
        record = cursor.fetchone()



@bot.event
async def on_ready():
    print('I\'m ready to do your biddings, Master')
#
#
# @bot.event()
# async def on_member_remove(member):
#     User.delete(member.display_name)


# Проверяем кто из пользователей в данный момент онлайн и находится в голосовом чате
def get_userlist(ctx):
    online_users = []
    for usr in ctx.guild.members:
        if str(usr.status) not in(['offline', 'invisible', 'dnd']):
            if usr.voice is not None and str(usr.channel.name) is not 'AFK':
                online_users.append(usr.id)
#    ctx.send(online_users)
    return online_users


# @bot.command(pass_context=True)  # Функция для начисления собственно денег - переписать под PostgreSQL <<--------
# async def money(ctx, arg):
#     """Uses: money on - to enable | money off - to disable"""
#     server_id = ctx.message.server # Важно - определяем айдишник сервера, он будет использоваться в разных командах.
#     global server_id
#     global db
#     await ctx.send(f'Money function is {arg}')
#     while arg.lower()=='on':
#         onvoice_list = get_userlist(ctx)
#         for usr in ctx.guild.members:
#             if usr.id in onvoice_list:
#                 if usr.id not in db['user_names'].keys():
#                     await ctx.send('adding to base: {}'.format(usr.id))
#                     db['user_names'][usr.id] = str(usr.display_name)
#                     db['user_currency'][usr.id] = 1
#                     print('айдишники:', list(db['user_names'].keys()), '\n', 'значения:', list(db['user_names'].values()))
#                 elif usr.id in db['user_names'].keys():
#                     db['user_currency'][usr.id] = db['user_currency'][usr.id] + 1
#         print('users data:')
#         print(db['user_names'])
#         print('currency data:')
#         print(db['user_currency'])
#         sleep(60)  # 1 minute

# функция для изначального заполнения базы данных пользователями сервера
def initial_db_read():
    cursor.execute('SELECT * FROM TABLE discord_users')
    records_count = len(cursor.fetchall())
    return records_count


def initial_db_fill():
# проверить, все ли пользователи занесены в ДБ, если нет - решить - дозаписать недостающих или перезаписать полностью
    cursor.execute('')
#    for usr in ctx.guild.members:
#        User.add(usr)


# @bot.command()  # команда вывода списка ID пользователей сервера (игнорируя тех кто оффлайн)
# async def who_online(ctx):


@bot.command(pass_context=True)
async def echo(ctx, *args):  # Название функции = название команды, в нашем случае это будет ">echo"
    """ prints your message like a bot said it """
    # тут какая-то проблема, теперь вместо слов в "args" находится объект контекста
    out = ''
    for word in ctx.message.content.split():
        out += word
        out += ' '
    await ctx.send(out)


@bot.command(pass_context=True)
async def mymoney(ctx):     #------- Тоже переписать под PostgreSQL
    me = ctx.message.author
    if me.id in list(db['user_currency'].keys()):
        await ctx.send('your money amount now is: ', db['user_currency'][me.id])
    else:
        await ctx.send('sorry you have no money')


@bot.command(pass_context=True)
async def showall(ctx):
    await ctx.send(list(db['user_currency'].keys()))


# Функция ежедневного начисления клановой валюты
# def daily(ctx):
#     if me.id in list(db['user_currency'].keys()):


# Команда для радужного ника
@bot.command(pass_context=True)
async def rainbowise(ctx):
    name = discord.utils.find(lambda r:('РАДУЖНЫЙ НИК' in r.name.upper()), ctx.guild.roles)
    role = discord.utils.get(ctx.guild.roles, name=str(name))
    await ctx.send(f'starting rainbow for {role}')
    while not Client.is_closed():
        for clr in rgb_colors:
            clr = random.choice(rgb_colors)
            try:
                await role.edit(color=discord.Colour(int(clr, 16)))
                sleep(600)
            except Exception as e:
                await ctx.send(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                print(e.args, e.__cause__)
                pass

def chests_getrewards():  # Здесь прописано соответствие фраз и картинок.
    rewardslist = {
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
        # Далее золотые награды
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
    return rewardslist

# ------------- ИГРА СУНДУЧКИ -----------
@bot.command(pass_context=True)
async def chest(ctx):
    rewardslist = chests_getrewards()
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
    author = ctx.message.author
    channel = ctx.message.channel
    check_role = discord.utils.get(ctx.message.author.roles, name='АДМИН')
    me = discord.utils.get(ctx.message.author.roles, name='КЛАНОВЫЙ ПРОГРАММИСТ')
    usual_rewards = []

    with open(os.path.join(os.getcwd(), 'usual-rewards.txt'), mode='r', encoding='utf-8') as file:
        for line in file:
            usual_rewards.append(str(line))

    golden_rewards = []
    with open(os.path.join(os.getcwd(), 'golden-rewards.txt'), mode='r', encoding='utf-8') as file:
        for line in file:
            golden_rewards.append(str(line))
    # Check if it's the right channel to write to and if user have relevant role
    if 'сундучки' in channel.name.lower() or 'казино' in channel.name.lower():
        pass
    else:
         return await ctx.send('```Error! Извините, эта команда работает только в специальном канале.```')
    isClanMate = False
    if [check_role in author.roles] or [me in author.roles]:
        isClanMate = True
    if not isClanMate:
        return await ctx.send(f'```Error! Извините, доступ имеют только члены клана с ролью "{check_role}"```')
    else:
        # IF all correct we head further
        await ctx.send('```yaml\nРешили испытать удачу и выиграть главный приз? Отлично! \n' +
                                       'Выберите, какой из шести простых сундуков открываем? Нажмите на цифру от 1 до 6```')
        # Начало вставки картинки с простыми сундуками
        async with aiohttp.ClientSession() as session:
            async with session.get('https://cdn.discordapp.com/attachments/585041003967414272/647943159762124824/Untitled_-_6.png') as resp:
                if resp.status != 200 and 301:
                    return await channel.send('Error! Could not get the file...')
                data = io.BytesIO(await resp.read())
                start_message = await channel.send(file=discord.File(data, 'Normal-chests.png'))
                await session.close()
        # Конец вставки картинки с простыми сундуками
        for react in reactions:
            await start_message.add_reaction(react)

        def checkS(reaction, user):
            return str(reaction.emoji) in reactions and user.bot is not True

        def checkG(reaction, user):
            return str(reaction.emoji) in reactions[0:2] and user.bot is not True

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=180, check=checkS)
        except asyncio.TimeoutError:
            await ctx.send('```yaml\nУдача не терпит медлительных. Время вышло! 👎```')
        else:
            random.shuffle(usual_rewards)
            usual_reward = random.choice(usual_rewards).rstrip()
            await channel.send(f'```yaml\nСундук со скрипом открывается и... {usual_reward}```')
            if usual_reward in rewardslist.keys():
                async with aiohttp.ClientSession() as session:
                    async with session.get(rewardslist[usual_reward]) as resp:
                        if resp.status != 200 and 301:
                            return await channel.send('Error! Could not get the file...')
                        data = io.BytesIO(await resp.read())
                        await channel.send(file=discord.File(data, 'reward.png'))
            if 'золотой ключ' in usual_reward.lower():
                await ctx.send('```fix\nОГО! Да у нас счастливчик! Принимайте поздравления и готовьтесь открыть золотой сундук!```')
                # Начало вставки картинки с золотыми сундуками
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                            'https://cdn.discordapp.com/attachments/585041003967414272/647935813962694676/51d6848c09aba40c.png') as resp:
                        if resp.status != 200 and 301:
                            return await channel.send('Error! Could not get the file...')
                        data = io.BytesIO(await resp.read())
                        start_message = await channel.send(file=discord.File(data, 'Golden-chests.png'))
                        await session.close()
                # Конец вставки картинки с золотыми сундуками
                for react in reactions[0:3]:
                    await start_message.add_reaction(react)
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=180, check=checkG)
                except asyncio.TimeoutError:
                    return await ctx.send('```fix\nУдача не терпит медлительных. Время вышло! 👎```')
                else:
                    random.shuffle(golden_rewards)
                    golden_reward = random.choice(golden_rewards)
                    await channel.send('```fix\nВы проворачиваете Золотой ключ в замочной скважине ' +
                                       f'и крышка тихонько открывается...\n{golden_reward}```')
                    if golden_reward in rewardslist.keys():
                        async with aiohttp.ClientSession() as session:
                            async with session.get(rewardslist[golden_reward]) as resp:
                                if resp.status != 200 and 301:
                                    return await channel.send('Error! Could not get the file...')
                                data = io.BytesIO(await resp.read())
                                await channel.send(file=discord.File(data, 'gold-reward.png'))


@bot.command(pass_context=True)
async def casino(ctx):
    prize = 0

    def makenums():
        nums = ""
        for _ in range(3):
            nums += str(random.randint(0,9))
        return nums

    ed_msg = await ctx.send(makenums())
    # rules ---> ctx.send('```fix\n каковы правила? ```')
    for i in range(3,9):
        ed = makenums()
        await ed_msg.edit(content=ed, suppress=False)
        sleep(0.2)
    await ctx.send('fin')


bot.run(token)
User = User()
