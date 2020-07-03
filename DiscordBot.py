# coding: utf8

import discord
import asyncio   # check if installed / проверьте, установлен ли модуль
import io
import aiohttp
import random
import asyncpg  # check if installed / проверьте, установлен ли модуль
import os
from time import sleep
from discord.ext import commands
from chests_rewards import usual_reward, gold_reward
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
des = 'GoldenBot for discord.'
rgb_colors = ['ff0000', 'ff4800', 'ffaa00', 'ffe200', 'a5ff00', '51ff00', '00ff55', '00ffb6', '00fffc', '00bdff', '0055ff', '0600ff', '6700ff', '9f00ff', 'f200ff', 'ff0088', 'ff003b']
Client = discord.Client()
bot = commands.Bot(description=des, command_prefix=prefix)

async def db_connection():
    db_user = 'postgres'
    db_pwd = 'Prophesy4'  # 32167 - пароль дома; Prophesy4 - пароль там.
    db_name = 'DiscBot_db'
    global db
    # db_address = reserved variable for database http address
    try:
        print('connecting to database')
        db = await asyncpg.connect(f'postgresql://{db_user}:{db_pwd}@localhost:5000/{db_name}')
        print('connection successful')
    except Exception as e:
        print('could not connect to database:\n', e.args, e.__traceback__)
    try:
        await db.execute('''CREATE TABLE IF NOT EXISTS discord_users (
            Id SERIAL PRIMARY KEY NOT NULL,
            Nickname varchar(255) NOT NULL,
            Join_date TIMESTAMP,
            Activity INT DEFAULT 0,
            Coin INT DEFAULT 0);''')
        print('connection to users base established')
    except Exception as e:
        print(e)
        print(e.__traceback__)
    return db


# считываем базу данных
async def initial_db_read():
    records_in_db = 0
    records_in_db = await db.fetch('SELECT * FROM discord_users')
    print(records_in_db)
    if len(records_in_db) >= 1:
        records_count = len(records_in_db)
        print(records_count, ' пользователей в базе')
        await db.close()
        return records_count
    else:
        await db.close()
        return len(records_in_db)

# функция для изначального заполнения базы данных пользователями сервера
async def initial_db_fill():
# проверить, все ли пользователи занесены в ДБ, если нет - дозаписать недостающих
    users_now = await initial_db_read()
    for guild in bot.guilds:
        if 'golden crown' in guild.name.lower():
            crown = await bot.get_guild(guild.id)
            if users_now < len(crown.members):
                for member in crown.members:
                    await db.execute(f'INSERT INTO discord_users VALUES({member.display_name}, {member.joined_at}, 0, 0) '
                                     f'SELECT {member.display_name}, {member.joined_at} FROM DUAL '
                                     f'WHERE NOT EXISTS (SELECT 1 FROM discord_users WHERE (Nickname={member.display_name}, Join_date={member.joined_at})')
            else:
                pass
    print('Данные пользователей в базе обновлены')

# class User:
#
#     def add(self, user, activity=0, gold=0):  #добавляем юзера как строку в БД
#         """We use separate class "User" for our discord server users -  to simplify the data handling.
#         This function needs you to specify at least user's display name (nick)"""
#
#         self.id = user.id
#         self.username = user.name
#         self.join_date = user.joined_at  # вписать сюда обращение к АПИ для получения даты присоединения к серверу
#         self.activity = activity
#         self.gold = gold
#         db.execute(f'INSERT INTO discord_users VALUES({self.id}, {self.username}, {self.join_date}, 0, 0)')
#
#     def update(self, user, gold):  #обновляем юзверя - ник, если изменился, начисляем деньги и активность.
#         self.gold = gold
#         self.id = user.id # неправильно, надо - передаём ник, по нему ищем юзер_айди в дискорде, далее если его ник != нику в ДБ - перезаписываем
#         db.execute(f'SELECT TOP 1 FROM TABLE discord_users WHERE Id={self.user_id}') #нужно доработать согласно комменту выше
#         record = db.fetchrow()
#         #дописать дальше обновление - идея, передаём ник, по нему ищем юзер_айди в дискорде, далее если какая-то инфа изменилась - перезаписываем
#         #отбой. Эту часть буду делать в рамках функции дискорда. Есть ли тогда смысл делать класс Юзера?
#
#     def delete(self, name):  #если юзера забанили или удалили с сервера, удаляем из ДБ (под вопросом)
#         self.name = name
#         pass
#
#     def show(self, user):
#         self.user_id = user.id #obsolete
#         record = db.fetchrow(f'SELECT TOP 1 FROM TABLE discord_users WHERE Id={self.user_id}')
#         ctx.send(record)

#
# @bot.event()
# async def on_member_remove(member):
#     User.delete(member.display_name)


async def start_rainbowise():
    async for guild in bot.fetch_guilds(limit=150):  # Проверить - нужно ли вообще это условие?
        if 'golden crown' in guild.name.lower():
            crown = bot.get_guild(guild.id)
    try:
        role = discord.utils.find(lambda r:('РАДУЖНЫЙ НИК' in r.name.upper()), crown.roles)
    except Exception as e:
        print('no server "Golden Crown" in my server list')
        print(e.__traceback__)
    while not Client.is_closed():
        for clr in rgb_colors:
            clr = random.choice(rgb_colors)
            try:
                await role.edit(color=discord.Colour(int(clr, 16)))
                await asyncio.sleep(600)
            except Exception as e:
                channel = discord.utils.get(crown.channels, name='system')
                print(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                await channel.send(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                print(e.args, e.__cause__)
                break

@bot.event
async def on_ready():
    await db_connection()
    print('I\'m ready to do your biddings, Master')
    print('initial database fill starting...')  # ON script start - this line and further lines didn't work.
    await initial_db_fill()
    print('initial database fill finished')
    await start_rainbowise()


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


#    for usr in ctx.guild.members:
#


# @bot.command()  # команда вывода списка ID пользователей сервера (игнорируя тех кто оффлайн)
# async def who_online(ctx):

@bot.command(pass_context=True)
async def user(ctx, member: discord.Member, arg=None):
    # кратко - "user" - меню-функция для пользователя/админа - аргументы "add" "del" "show"?? "update"
    # проверить как работает
    if arg==None:
        data = await db.fetchrow(f'SELECT ALL FROM TABLE discord_users WHERE Name={member.display_name})')
        for element in data.split(','):
            ctx.send(element)
    elif arg=='add':
        await db.execute(f'INSERT INTO discord_users VALUES({member.display_name},{member.joined_at}, 0, 0)')
        ctx.send('user added to database')
    pass


@bot.command(pass_context=True)
async def echo(ctx, *args):  # Название функции = название команды, в нашем случае это будет ">echo"
    """ prints your message like a bot said it """
    # тут какая-то проблема, теперь вместо слов в "args" находится объект контекста. Проблема решена?
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


# Ручная команда для радужного ника
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
                await asyncio.sleep(600)
            except Exception as e:
                await ctx.send(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                print(e.args, e.__cause__)
                pass


# ------------- ИГРА СУНДУЧКИ -----------
@bot.command(pass_context=True)
async def chest(ctx):
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
    author = ctx.message.author
    channel = ctx.message.channel
    check_role = discord.utils.get(ctx.message.author.roles, name='АДМИН')
    me = discord.utils.get(ctx.message.author.roles, name='КЛАНОВЫЙ ПРОГРАММИСТ')
    usual_rewards = []
    # with open(os.path.join(os.getcwd(), 'usual-rewards.txt'), mode='r', encoding='utf-8') as file:
    #     for line in file:
    #         usual_rewards.append(str(line))
    #
    # golden_rewards = []
    # with open(os.path.join(os.getcwd(), 'golden-rewards.txt'), mode='r', encoding='utf-8') as file:
    #     for line in file:
    #         golden_rewards.append(str(line))
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
            reward, pic = usual_reward()
            await channel.send(f'```yaml\nСундук со скрипом открывается и... {reward}```')
            async with aiohttp.ClientSession() as session:
                async with session.get(pic) as resp:
                        if resp.status != 200 and 301:
                            return await channel.send('Error! Could not get the file...')
                        data = io.BytesIO(await resp.read())
                        await channel.send(file=discord.File(data, 'reward.png'))
            if 'золотой ключ' in reward.lower():
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
                    reward, pic = gold_reward()
                    await channel.send('```fix\nВы проворачиваете Золотой ключ в замочной скважине ' +
                                       f'и крышка тихонько открывается...\n{reward}```')
                    async with aiohttp.ClientSession() as session:
                        async with session.get(pic) as resp:
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