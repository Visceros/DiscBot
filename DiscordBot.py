# coding: utf8

import discord
import asyncio   # check if installed / проверьте, установлен ли модуль
import io
import aiohttp
import random
import asyncpg  # check if installed / проверьте, установлен ли модуль
import os
from time import sleep
from discord.ext import commands, tasks
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
        print('connecting to database server')
        db = await asyncpg.connect(f'postgresql://{db_user}:{db_pwd}@localhost:5000/{db_name}')
        print('connection successful')
    except Exception as e:
        print('could not connect to database:\n', e.args, e.__traceback__)
    try:
        await db.execute('''CREATE TABLE IF NOT EXISTS discord_users (
            Id BIGINT PRIMARY KEY NOT NULL UNIQUE,
            Nickname varchar(255) NOT NULL UNIQUE,
            Join_date timestamptz,
            Activity INT DEFAULT 0,
            Gold INT DEFAULT 0,
            CONSTRAINT users_unique UNIQUE (Id, Nickname));''')
        print('connection to users base established')
    except Exception as e:
        print(e.args, e.__cause__, e.__context__)
    return db


# считываем количество записей в базе данных  - обновлена логика. получаем не только кол-во записей, но и айдишники! ПРОВЕРИТЬ!
async def initial_db_read():
    records_in_db = 0
    records_in_db = await db.fetch('SELECT * FROM discord_users')
    # print('records in db are:\n', records_in_db)   # debug print
    if len(records_in_db) >= 1:
        users_idlist = []
        records_count = len(records_in_db)
        for i in range(1, records_count+1):
            id = await db.fetchval(f'SELECT Id FROM discord_users ORDER BY Id LIMIT 1 OFFSET {i-1};')
            users_idlist.append(id)
        print(records_count, ' пользователей в базе')
        print(users_idlist)
        return records_count, users_idlist
    else:
        return 0, []


# функция для изначального заполнения базы данных пользователями сервера. Работает раз в сутки
@tasks.loop(hours=24.0)
async def initial_db_fill():
    """проверяет, все ли пользователи занесены в ДБ, если нет - дозаписывает недостающих"""
    users_count, users_ids = await initial_db_read()
    for guild in bot.guilds:
        #if 'golden crown' in guild.name.lower():
        if 'free zone' in guild.name.lower():
            current_members_list = []
            crown = bot.get_guild(guild.id)
            for member in crown.members:
                if not member.bot:
                    current_members_list.append(member.id)
            if users_count < len(current_members_list):
                for member in crown.members:
                    if not member.bot and member.id not in users_ids:
                        await db.execute('INSERT INTO discord_users (id, nickname, join_date, activity, gold) VALUES($1, $2, $3, 0, 0) ON CONFLICT (Id) DO NOTHING;', member.id, member.display_name, member.joined_at)
                print('Данные пользователей в базе обновлены')
                #break
            else:
                pass
    print('database fill cycle ended')


@tasks.loop(minutes=5.0)
async def auto_rainbowise():
    print(2)
    async for guild in bot.fetch_guilds(limit=150):  # Проверить - нужно ли вообще это условие?
        if 'golden crown' in guild.name.lower():
            crown = bot.get_guild(guild.id)
            print('Гильдия "Golden Crown" найдена в списке')
        else:
            print('Не найден сервер "Golden Crown"')
            return False
    try:
        role = await discord.utils.find(lambda r: ('РАДУЖНЫЙ НИК' in r.name.upper()), crown.roles)
    except Exception as e:
        print(f'something gone wrong when changing {role} role color')
        print(e.__traceback__)
    while not Client.is_closed():
        for color in rgb_colors:
            clr = random.choice(rgb_colors)
            try:
                await role.edit(color=discord.Colour(int(clr, 16)))
            except Exception as e:
                channel = discord.utils.get(crown.channels, name='system')
                print(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                await channel.send(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                print(e.__cause__, e, sep='\n')
                break


@bot.event
async def on_ready():
    await db_connection()
    print('initial database fill starting...')
    initial_db_fill.start()
    print('initial database fill finished')
    auto_rainbowise.start()
    print('I\'m ready to serve.')


# -------------------- Функция ежедневного начисления клановой валюты  --------------------
async def daily():
    """Проверяем кто из пользователей в данный момент онлайн и находится в голосовом чате. Начисляем им валюту"""
    async for guild in await bot.fetch_guilds(limit=150):  # Проверить - нужно ли вообще это условие?
        # if 'golden crown' in guild.name.lower():
        #     crown = bot.get_guild(guild.id)
        if 'free zone' in guild.name.lower():
            crown = await bot.get_guild(guild.id)
        else:
            print('Error. No guild named "Golden Crown" found.')
    while True:
        async for member in crown.members:
            if str(member.status) not in (['offline', 'invisible', 'dnd']):
                if member.voice is not None and str(member.channel.name) is not 'AFK':
                    gold = await db.fetchval(f'SELECT Gold FROM TABLE discord_users WHERE Id={member.id};')
                    gold = int(gold)+1
                    await db.execute(f'UPDATE discord_users SET Gold={gold} WHERE Id={member.id};')
        await asyncio.sleep(60)  # 1 minute


# проверка на наличие админ-прав у того, кто запускает команды управления пользователями
async def is_admin(ctx):
    if ctx.message.author.has_permissions(administrator=True):
        ctx.send(ctx.message.author.has_permissions(administrator=True))
        return ctx.message.author.has_permissions(administrator=True)
    else:
        return ctx.send('you don\'t have the rights to perform this command')


# -------------НАЧАЛО БЛОКА АДМИН-МЕНЮ ПО УПРАВЛЕНИЮ ПОЛЬЗОВАТЕЛЯМИ--------------
@bot.group()
async def user(ctx):
    # кратко - "user" - меню-функция для пользователя/админа - аргументы "add" "del" "show"?? "update"
    # проверить как работает            <<<<<-----------------------------------------------------------работаю сейчас
    if ctx.invoked_subcommand is None:
        await ctx.send('you didn\'t enter any subcommand / вы не указали, что делать с пользователем')


@user.command()
@commands.check(is_admin)
async def add(ctx, member:discord.member):
    """Adds the user to database / Добавляем пользователя в базу данных (для новых людей, которых ты приглашаешь на сервер)"""
    await db.execute('INSERT INTO discord_users VALUES($1, $2, $3, 0, 0);', member.id, member.display_name, member.joined_at)
    ctx.send('user added to database')


@user.command()
@commands.check(is_admin)
async def show(ctx, member: discord.member):
    """Shows the info about user/ показываем данные пользователя"""
    data = await db.fetchrow(f'SELECT ALL FROM TABLE discord_users WHERE Id={member.id};')
    for element in data.split(','):
        ctx.send(element+' ')


@user.command()
@commands.check(is_admin)
async def give(member: discord.member, gold):
    """Give user some gold / Даём пользователю деньги"""
    gold_was = await db.fetchval(f'SELECT Gold FROM TABLE discord_users WHERE Id={member.id};')
    newgold = int(gold_was) + gold
    await db.execute(f'UPDATE discord_users SET gold={newgold} WHERE Id={member.id};')


@user.command()
@commands.check(is_admin)
async def clear(member: discord.member):
    """Use this to clear the data about user to default and 0 values"""
    await db.execute(f'DELETE FROM TABLE discord_users WHERE Id={member.id};')
    await db.execute(f'INSERT INTO discord_users VALUES($1, $2, $3, 0, 0);', member.id, member.display_name, member.joined_at)


@bot.command(pass_context=True)
async def echo(ctx, *, msg:str):  # Название функции = название команды, в нашем случае это будет ">echo"
    """ prints your message like a bot said it """
    message = ctx.message
    await message.delete()
    await ctx.send(msg)


@bot.command(pass_context=True)
async def me(ctx):
    usr = ctx.message.author
    me_data = await db.fetchval(f'SELECT Gold FROM discord_users WHERE Id={usr.id};')
    if me_data is not None:
        await ctx.send('your amount of Gold now is: ', me_data)
    else:
        await ctx.send('sorry you have no money, or I do not know you')


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
                await asyncio.sleep(300)
            except Exception as e:
                await ctx.send(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                print(e.args, e.__cause__)
                pass


bot.run(token, reconnect=True)
