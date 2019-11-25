# coding: utf8

import discord
import asyncio   # check if installed
import random
import psycopg2  # check if installed
import os
from time import sleep
from discord.utils import get   # just unused statement, cause I use discord.utils.get everywhere (for explicity)
from discord.ext import commands

token = 'NTAzNTQ5MDA1ODMwMDI5MzEy.Du8B4w.jXHBly_o8-E1EJDYsgYMOmxVAhs'
prefix = '>'
des = 'A discord bot for doing some automatic things that I am to lazy to do myself.'
rgb_colors = ['ff0000', 'ff4800', 'ffaa00', 'ffe200', 'a5ff00', '51ff00', '00ff55', '00ffb6', '00fffc', '00bdff', '0055ff', '0600ff', '6700ff', '9f00ff', 'f200ff', 'ff0088', 'ff003b']
Client = discord.Client()
bot = commands.Bot(description=des, command_prefix=prefix)

db_user = 'postgres'
db_pwd = '32167'
# db = psycopg2.connect(
#     dbname='DiscBot_db',
#     user=db_user,
#     password=db_pwd,
#     host='',
#     port='5432'
# )
# cursor = db.cursor()
# cursor.execute('SELECT EXISTS(SELECT * FROM DiscBot+db.tables WHERE table_name=discord_users)')
# if cursor.fetchone()[0] is True:
#     pass
# else:
#     try:
#         cursor.execute('''CREATE TABLE discord_users
#             ID INT PRIMARY KEY NOT NULL,
#             NAME TEXT NOT NULL,
#             ACTIVITY INT,
#             GOLD INT);''')
#     except Exception as e:
#         print(e)
#         print(e.__traceback__)

class User:
    def __init__(self, user_id, user_name, activity=0, gold=0):
        """We use separate class "User" for discord users to simplify the data handling
        at least 2 *args should be given: 1)user id 2) user name (nick)"""
        self.id = user_id
        self.username = user_name
        self.join_date = join_date
        self.activity = activity
        self.gold = gold

    def db_add(self):  #добавляем юзера как строку в БД
        pass

    def db_update(self):  #обновляем юзверя - ник, если изменился, начисляем деньги и активность.
        pass

    def db_del(self):  #если юзера забанили или удалили с сервера, удаляем из ДБ (под вопросом)
        pass


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
    for word in ctx.message.split():
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
async def checkme(ctx):
    me = ctx.message.author
    if me.id in list(db['user_currency'].keys()):
        await ctx.send('your money amount now is: ',db['user_currency'][me.id])
    else:
        await ctx.send('sorry you have no money')


@bot.command(pass_context=True)
async def showall(ctx):
    await ctx.send(list(db['user_currency'].keys()))


@bot.event
async def on_ready():
    print('I\'m ready to do your biddings, Master')


# Команда для запуска функции ежедневного начисления клановой валюты
# @bot.command()
# async def daily(ctx):
#     me = ctx.message.author
#     bonus_money = random.randint(50,150)
#     if me.id in list(db['user_currency'].keys()):


# Команда для радужного ника
@bot.command(pass_context=True)
async def rainbowise(ctx):
    rainbowrolename = 'V.I.P. радужный ник'
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
    reactions_silverchests = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
    reactions_goldchests = ['1️⃣', '2️⃣', '3️⃣']
    author = ctx.message.author
    channel = ctx.message.channel
    check_role = discord.utils.get(ctx.message.author.roles, name='Сокланы')
    # Check if it's the right channel to write to and if user have relevant role
    # if 'сундучки' in channel.name.lower():
    #     pass
    # else:
    #      await ctx.send('```Error! Извините, эта команда работает только в специальном канале.```')
    isClanMate = False
    if check_role in author.roles:
        isClanMate = True
    if not isClanMate:
        await ctx.send(f'```Error! Извините, доступ имеют только члены клана с ролью "{check_role}"```')
    else:
        # IF all correct we head further
        start_message = await ctx.send('```yaml\nРешили испытать удачу и выиграть главный приз? Отлично! \n' +
                                       'Выберите, какой из шести простых сундуков открываем? Нажмите на цифру от 1 до 6```')
        # showBasicChests = await ctx.send()  # картинка с простыми сундуками
        for react in reactions_silverchests:
            await start_message.add_reaction(react)

        def check(reaction, user):
            return user == author and str(reaction.emoji) in reactions_silverchests

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=120, check=check)
        except asyncio.TimeoutError:
            await ctx.send('```yaml\nУдача не терпит медлительных. Время вышло! 👎```')
        else:
            # await reaction.remove(author)
            random.shuffle(usual_rewards)
            usual_reward = random.choice(usual_rewards)
            await channel.send(f'```yaml\nСундук со скрипом открывается и... {usual_reward}```')
            if 'золотой ключ' in usual_reward.lower():
                #Вы проворачиваете Золотой ключ в замочной скважине и крышка тихонько открывается.
                pass

bot.run(token)
