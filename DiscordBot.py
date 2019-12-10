# coding: utf8

import discord
import asyncio   # check if installed
import io
import aiohttp
import random
import psycopg2  # check if installed
import os
from time import sleep
from discord.utils import get   # just unused statement, cause I use discord.utils.get everywhere (for explicity)
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
# db_pwd = 'Prophesy4'  # 32167 - пароль дома
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
#
# class User:
#     def __init__(self):
#         pass
#
#     def add(self, userId, userName, activity=0, gold=0):  #добавляем юзера как строку в БД
#         """We use separate class "User" for our discord server users -  to simplify the data handling
#         at least 2 *args should be given: 1)user id 2) user name (nick)"""
#         self.id = userId
#         self.username = userName
#         self.join_date =   # вписать сюда обращение к АПИ для получения даты присоединения к серверу
#         self.activity = activity
#         self.gold = gold
#
#     def update(self):  #обновляем юзверя - ник, если изменился, начисляем деньги и активность.
#         pass
#
#     def delete(self, name):  #если юзера забанили или удалили с сервера, удаляем из ДБ (под вопросом)
#         self.name = name
#         pass
#
#     def show(self, name):
#         cursor.execute('')
#         user = cursor.fetchone()


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


@bot.command(pass_context=True)  # Функция для начисления собственно денег
async def money_start(ctx):
    global db
    db['user_names'] = {}
    db['user_currency'] = {}
    await ctx.send('Okay I will give em money')
    while not Client.is_closed():
        onvoice_list = get_userlist(ctx)
        for usr in ctx.guild.members:
            if usr.id in onvoice_list:
                if usr.id not in db['user_names'].keys():
                    await ctx.send('adding to base: {}'.format(usr.id))
                    db['user_names'][usr.id] = str(usr.display_name)
                    db['user_currency'][usr.id] = 1
                    print('айдишники:', list(db['user_names'].keys()), '\n', 'значения:', list(db['user_names'].values()))
                elif usr.id in db['user_names'].keys():
                    db['user_currency'][usr.id] = db['user_currency'][usr.id] + 1
        print('users data:')
        print(db['user_names'])
        print('currency data:')
        print(db['user_currency'])
        sleep(60) # 1 minute
        if ctx.message.content.startswith('_money_stop'):
            await ctx.send('Okay I will stop giving money')
            break
        else:
            pass
    return db['user_names'], db['user_currency']


@bot.command(pass_context=True)
async def mymoney(ctx):
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
    rainbowrolename = 'V.I.P. радужный ник'
    print(f'starting rainbow for {rainbowrolename}')
    role = discord.utils.get(ctx.guild.roles, name=rainbowrolename)
    while not Client.is_closed():
        for clr in rgb_colors:
            clr = random.choice(rgb_colors)
            try:
                await role.edit(color=discord.Colour(int(clr, 16)))
                sleep(600)
            except Exception as e:
                await ctx.send(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{rainbowrolename}" role')
                print(e.args, e.__cause__)
                pass


# ------------- ИГРА СУНДУЧКИ -----------
@bot.command(pass_context=True)
async def chest(ctx):
    usual_rewards = []
    with open(os.path.join(os.getcwd(), 'usual-rewards.txt'), mode='r', encoding='utf-8') as file:
        for line in file:
            usual_rewards.append(str(line))
    golden_rewards = []
    with open(os.path.join(os.getcwd(), 'golden-rewards.txt'), mode='r', encoding='utf-8') as file:
        for line in file:
            golden_rewards.append(str(line))
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
    author = ctx.message.author
    channel = ctx.message.channel
    check_role = discord.utils.get(ctx.message.author.roles, name='АДМИН')
    me = discord.utils.get(ctx.message.author.roles, name='КЛАНОВЫЙ ПРОГРАММИСТ')
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
                if resp.status != 200:
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
            return str(reaction.emoji) in reactions[0:3] and user.bot is not True

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=120, check=checkS)
        except asyncio.TimeoutError:
            await ctx.send('```yaml\nУдача не терпит медлительных. Время вышло! 👎```')
        else:
            random.shuffle(usual_rewards)
            usual_reward = random.choice(usual_rewards)
            await channel.send(f'```yaml\nСундук со скрипом открывается и... {usual_reward}```')
            if 'золотой ключ' in usual_reward.lower():
                await ctx.send('```fix\nОГО! Да у нас счастливчик! Принимайте поздравления и готовьтесь открыть золотой сундук!```')
                # Начало вставки картинки с золотыми сундуками
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                            'https://cdn.discordapp.com/attachments/585041003967414272/647935813962694676/51d6848c09aba40c.png') as resp:
                        if resp.status != 200:
                            return await channel.send('Error! Could not get the file...')
                        data = io.BytesIO(await resp.read())
                        start_message = await channel.send(file=discord.File(data, 'Golden-chests.png'))
                        await session.close()
                # Конец вставки картинки с золотыми сундуками
                for react in reactions[0:3]:
                    await start_message.add_reaction(react)
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=120, check=checkG)
                except asyncio.TimeoutError:
                    return await ctx.send('```fix\nУдача не терпит медлительных. Время вышло! 👎```')
                else:
                    random.shuffle(golden_rewards)
                    golden_reward = random.choice(golden_rewards)
                    await channel.send('```fix\nВы проворачиваете Золотой ключ в замочной скважине ' +
                                       f'и крышка тихонько открывается...\n{golden_reward}```')

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