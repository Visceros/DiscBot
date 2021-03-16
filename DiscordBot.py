# coding: utf8

import discord
import asyncio   # check if installed / проверьте, установлен ли модуль
from Cog_utils import Games, Listeners, Utils
import random
import asyncpg  # check if installed / проверьте, установлен ли модуль
import os
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime
import logging

# ------- LOGGER FOR DEBUG PURPOSES
# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)
# ------- LOGGER FOR DEBUG PURPOSES

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
token = os.getenv('bot_key')
if token is None:
    print('Could not receive token. Please check if your .env file has the correct token')
    exit(1)

prefix = '>'
des = 'GoldenBot for Golden Crown discord.'
rgb_colors = ['ff0000', 'ff4800', 'ffaa00', 'ffe200', 'a5ff00', '51ff00', '00ff55', '00ffb6', '00fffc', '00bdff', '0055ff', '0600ff', '6700ff', '9f00ff', 'f200ff', 'ff0088', 'ff003b']
bot = commands.Bot(description=des, command_prefix=prefix)


async def db_connection():
    global db
    db_user = os.getenv('db_user')
    db_pwd = os.getenv('db_pwd')
    db_name = os.getenv('db_name')
    # db_address = os.getenv('db_address')  # reserved variable for database http address
    try:
        print('connecting to database server...')
        db = await asyncpg.connect(host='localhost', port=5000, user=db_user, password=db_pwd, database=db_name)
        print('connection successful!')
    except Exception as e:
        print('Could not connect to database:\n', e.args)
        print(e)
        print('exiting...')
        exit(1)
    try:
        await db.execute('''CREATE TABLE IF NOT EXISTS discord_users (
            Id BIGINT PRIMARY KEY NOT NULL UNIQUE,
            Nickname varchar(255) NOT NULL UNIQUE,
            Join_date Date,
            Gold INT DEFAULT 0,
            Warns INT DEFAULT 0,
            CONSTRAINT users_unique UNIQUE (Id, Nickname));''')
        print('Table of users created or connection established')

        await db.execute('''CREATE TABLE IF NOT EXISTS LogTable (
        user_id BIGINT NOT NULL,
        login timestamp with time zone,
        logoff timestamp with time zone,              
        gold INT DEFAULT 0,
        record_id SERIAL PRIMARY KEY NOT NULL,
        CONSTRAINT users_unique FOREIGN KEY (User_id) REFERENCES discord_users (Id));''')
        print('Log Table online')
    except Exception as e:
        print('Attempt to create tables database failed')
        print(e, e.args, e.__cause__, e.__context__)
    return db


# считываем количество записей в базе данных  - обновлена логика. получаем не только кол-во записей, но и айдишники! ПРОВЕРИТЬ!
async def initial_db_read():
    records_in_db = 0
    records_in_db = await db.fetch('SELECT * FROM discord_users')
    if len(records_in_db) >= 1:
        users_idlist = []
        records_count = len(records_in_db)
        for i in range(1, records_count+1):
            ids = await db.fetchval(f'SELECT id FROM discord_users ORDER BY id LIMIT 1 OFFSET {i-1};')
            users_idlist.append(ids)
        print(records_count, ' пользователей в базе')
        #print(users_idlist)
        return records_count, users_idlist
    else:
        return 0, []


# функция для изначального заполнения базы данных пользователями сервера. Работает раз в сутки
@tasks.loop(hours=24.0)
async def initial_db_fill():
    """проверяет, все ли пользователи занесены в ДБ, если нет - дозаписывает недостающих"""
    users_count, users_ids = await initial_db_read()
    for guild in bot.guilds:
        if 'golden crown' in guild.name.lower():
        #if 'free zone' in guild.name.lower():
            current_members_list = []
            crown = bot.get_guild(guild.id)
            global sys_channel
            sys_channel = discord.utils.get(guild.channels, name='system')
            if not sys_channel:
                try:
                    admin_roles = [role for role in guild.roles if role.permissions.administrator]
                    sys_channel_overwrites = {}
                    for role in admin_roles:
                        sys_channel_overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
                    sys_channel_overwrites[guild.default_role] = discord.PermissionOverwrite(read_messages=False,
                                                                                             send_messages=False,
                                                                                             view_channel=False)
                    sys_channel = await crown.create_text_channel('system', overwrites=sys_channel_overwrites,
                                                                  reason='creating a channel for system messages')
                except discord.Forbidden:
                    print(f'No permissions to create system channel in {guild} server')
                except Exception as ex:
                    print(ex)
            for member in crown.members:
                if not member.bot:
                    current_members_list.append(member.id)
            if users_count < len(current_members_list):
                for member in crown.members:
                    if not member.bot and member.id not in users_ids:
                        await db.execute('INSERT INTO discord_users (id, nickname, join_date, gold) VALUES($1, $2, $3, 0, 0) ON CONFLICT (id) DO NOTHING;', member.id, member.display_name, member.joined_at)
                print('Данные пользователей в базе обновлены')
            else:
                pass
    print('database fill cycle ended')
    test = await db.fetchval('SELECT login from LogTable ORDER BY ID LIMIT 1')
    print(test)


@tasks.loop(minutes=5.0)
async def auto_rainbowise():
    for guild in bot.guilds:  # Проверить - нужно ли вообще это условие?
        if 'golden crown' in guild.name.lower():
            crown = bot.get_guild(guild.id)
            break
        else:
            print('Не найден сервер "Golden Crown"')
        try:
            role = discord.utils.find(lambda r: ('РАДУЖНЫЙ НИК' in r.name.upper()), guild.roles)
        except discord.NotFound:
            sys_channel.send('no role for rainbow nick found. See if you have the role with "радужный ник" in its name')
        except Exception as e:
            print(e)
        clr = random.choice(rgb_colors)
        try:
            await role.edit(color=discord.Colour(int(clr, 16)))
            print(f'changed color for {role}')
        except Exception as e:
            print(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
            await sys_channel.send(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
            print(e.__cause__, e, sep='\n')


@bot.event
async def on_ready():
    await db_connection()
    print('initial database fill starting...')
    initial_db_fill.start()
    auto_rainbowise.start()
    await accounting()
    print('I\'m ready to serve.')
    bot.add_cog(Games(bot))
    bot.add_cog(Listeners(bot, db=db))
#    bot.add_cog(Utils(bot))


# -------------------- Функция ежедневного начисления клановой валюты  --------------------


@tasks.loop(minutes=1)
async def _increment_money(server: discord.Guild):
    try:
        for member in server.members:
            if str(member.status) not in ['offline', 'invisible', 'dnd'] and not member.bot:
                if member.voice is not None and member.voice.channel is not server.afk_channel:
                    gold = await db.fetchval(f'SELECT gold FROM discord_users WHERE id={member.id};')
                    gold = int(gold)+1
                    await db.execute(f'UPDATE discord_users SET gold={gold} WHERE id={member.id};')
    except Exception as ex:
        await sys_channel.send(content=(ex, ex.__traceback__, ex.__cause__, ex.__context__))


async def accounting():
    """Проверяем кто из пользователей в данный момент онлайн и находится в голосовом чате. Начисляем им валюту"""
    try:
        async for guild in bot.fetch_guilds():
            if 'golden crown' in guild.name.lower():
                crown = bot.get_guild(guild.id)
            # if 'free zone' in guild.name.lower():
            #     crown = bot.get_guild(guild.id)
    except Exception as e:
        print(e)
    else:
        if not isinstance(crown, discord.Guild):
            print('Error. No guild named "Golden Crown" found.')
    _increment_money.start(crown)


def subtract_time(time_arg):
    _tmp = time_arg.replace(microsecond=0) - datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0)
    ret = str(abs(_tmp)).replace('days', 'дней')
    return ret


# -------------НАЧАЛО БЛОКА АДМИН-МЕНЮ ПО УПРАВЛЕНИЮ ПОЛЬЗОВАТЕЛЯМИ--------------
@bot.group()
@commands.has_permissions(administrator=True)
async def user(ctx):
    """ "user" - меню-функция для админа - аргументы "add" "del" "show" "update" """
    if ctx.message.author.guild_permissions.administrator:
        if ctx.invoked_subcommand is None:
            await ctx.send('you didn\'t enter any subcommand / вы не указали, что делать с пользователем')
            await ctx.message.delete()
    else:
        user.show(ctx, ctx.message.author)


@user.command()
@commands.has_permissions(administrator=True)
async def add(ctx, member:discord.Member):
    """Adds the user to database / Добавляем пользователя в базу данных (для новых людей, которых ты приглашаешь на сервер)"""
    await ctx.message.delete()
    await db.execute('INSERT INTO discord_users VALUES($1, $2, $3, 0, 0);', member.id, member.display_name, member.joined_at)
    ctx.send('user added to database')


@user.command()
@commands.has_permissions(administrator=True)
async def show(ctx, member: discord.Member):
    """Shows the info about user/ показываем данные пользователя"""
    data = await db.fetchrow(f'SELECT * FROM discord_users WHERE id={member.id};')
    if data is not None:
        achievments = 0
        negative_achievements = 0
        warns = int(data['Warns'])
        for role in member.roles:
            if 'ачивка' in role.name.lower():
                achievments += 1
                if role.color == discord.Colour(int('ff4f4f', 16)):
                    negative_achievements += 1

        seven_days_activity_records = await db.fetch(
            f"SELECT login, logoff from LogTable WHERE login BETWEEN '{datetime.datetime.now() - datetime.timedelta(days=7)}'::timestamptz AND '{datetime.datetime.now()}'::timestamptz AND user_id={member.id} ORDER BY login ASC;")
        thirty_days_activity_records = await db.fetch(
            f"SELECT login, logoff from LogTable WHERE user_id={member.id} AND login BETWEEN '{datetime.datetime.now() - datetime.timedelta(days=30)}'::timestamptz AND '{datetime.datetime.now()}'::timestamptz ORDER BY login ASC;")

        async def count_result_activity(activity_records_list, warns:int):
            activity = datetime.datetime(1,1,1, hour=0, minute=0, second=0)
            for item in activity_records_list:
                if item[1] is None:
                    activity = activity+(datetime.datetime.now(tz=datetime.timezone.utc) - item[0])
                else:
                    activity = (activity + (item[1] - item[0]))
            result_activity = activity - datetime.datetime(1,1,1)
            if warns > 0:
                result_activity = result_activity - datetime.timedelta(minutes=(10*warns))
            result_activity = result_activity - datetime.timedelta(microseconds=result_activity.microseconds)
            return result_activity

        part_1 = f"Никнейм: {member.mention}\nБанковский счёт: `{data['gold']}` :coin:"
        part_2 = f"\nВсего ачивок: `{achievments}`\nНегативных: `{negative_achievements}`"
        part_3 = f"\nАктивность за 7 дней: `{await count_result_activity(seven_days_activity_records, warns)}`\nАктивность за 30 дней: `{await count_result_activity(thirty_days_activity_records, warns)}`"
        part_4 = f"\nДата присоединения к серверу: `{data['join_date'].date()}`\nID пользователя: `{member.id}`"
        embed = discord.Embed(color='#efff00')
        #embed.add_field(name='', value=f"17*{data['symbol']}")
        embed.add_field(name='Пользователь:', value=part_1, inline=False)
        embed.add_field(name='Ачивки:', value=part_2, inline=False)
        embed.add_field(name='Активность:', value=part_3, inline=False)
        embed.add_field(name='Прочее:', value=part_4, inline=False)
        await ctx.send(embed=embed)
    else:
        ctx.send('Sorry I have no data about you / Извините, у меня нет данных о вас.')
    await ctx.message.delete()


# ----------------------------------------------------------------------------------------- Протестировать команду ниже.
# @commands.has_permissions(administrator=True)
@user.command()
async def give(ctx, member: discord.Member, gold):
    """This command used to give someone your coins / Эта команда позволяет передать кому-то вашу валюту"""
    author = ctx.message.author
    await ctx.message.delete()
    gold = abs(gold)
    if 'administrator' in ctx.message.author.guild_permissions:
        """Give user some gold / Даём пользователю деньги"""
        gold_was = await db.fetchval(f'SELECT gold FROM discord_users WHERE id={member.id};')
        newgold = int(gold_was) + int(gold)
        await db.execute(f'UPDATE discord_users SET gold={newgold} WHERE id={member.id};')
    else:
        user_gold = await db.fetchval(f'SELECT gold FROM discord_users WHERE id={author.id};')
        if int(gold) > int(user_gold):
            ctx.channel.send('У вас нет столько денег.')
            return
        else:
            newgold = int(user_gold) - int(gold)
            await db.execute(f'UPDATE discord_users SET gold={newgold} WHERE id={author.id};')
            target_gold = await db.fetchval(f'SELECT gold FROM discord_users WHERE id={member.id};')
            newtargetgold = int(target_gold) + int(gold)
            await db.execute(f'UPDATE discord_users SET gold={newtargetgold} WHERE id={member.id};')


@user.command()
@commands.has_permissions(administrator=True)
async def de(ctx, member: discord.Member, gold):
    """This command takes the coins from selected user / Этой командой забираем у пользователя валюту."""
    await ctx.message.delete()
    gold_was = await db.fetchval(f'SELECT gold FROM discord_users WHERE id={member.id};')
    newgold = int(gold_was) - int(gold)
    if newgold < 0:
        newgold = 0
    await db.execute(f'UPDATE discord_users SET gold={newgold} WHERE id={member.id};')


@user.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, member: discord.Member):
    """Use this to clear the data about user to default and 0 values / Сбросить данные пользователя в базе"""
    await ctx.message.delete()
    await db.execute(f'DELETE FROM discord_users WHERE id={member.id};')
    await db.execute(f'INSERT INTO discord_users VALUES($1, $2, $3, 0, 0);', member.id, member.display_name, member.joined_at)

# -------------КОНЕЦ БЛОКА АДМИН-МЕНЮ ПО УПРАВЛЕНИЮ ПОЛЬЗОВАТЕЛЯМИ--------------

@bot.command(pass_context=True)
async def echo(ctx, msg: str):
    """ prints your message like a bot said it / Бот пишет ваше сообщение так, будто это он сказал."""
    message = ctx.message
    await message.delete()
    await ctx.send(msg)


@bot.command(pass_context=True)
async def me(ctx):
    """Command to see your profile / Этой командой можно увидеть ваш профиль"""
    usr = ctx.message.author
    await show(ctx, usr)


# Ручная команда для радужного ника
@bot.command(pass_context=True)
async def rainbowise(ctx):
    await ctx.message.delete()
    name = discord.utils.find(lambda r:('РАДУЖНЫЙ НИК' in r.name.upper()), ctx.guild.roles)
    role = discord.utils.get(ctx.guild.roles, name=str(name))
    await ctx.send(f'starting rainbow for {role}')
    while True:
        for clr in rgb_colors:
            clr = random.choice(rgb_colors)
            try:
                await role.edit(color=discord.Colour(int(clr, 16)))
                await asyncio.sleep(300)
            except Exception as e:
                await ctx.send(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                print(e.args, e.__cause__)
                pass

@bot.command()
async def poll(ctx, polltime):
    start_time = datetime.datetime.now().replace(microsecond=0)
    msg = ctx.message.reference
    await ctx.message.delete()
    msg = ctx.send(f'Стартовал опрос:\n\n{msg}')
    await msg.add_reaction('👍')
    await msg.add_reaction('👎')
    end_time = start_time + datetime.timedelta(hours=polltime)
    if datetime.datetime.now() > end_time:
        for reaction in msg.reactions:
            if reaction == '👍':
                yes = reaction.count
            elif reaction == '👎':
                no = reaction.count
        await msg.reply(content='Опрос завершён, большинство проголосовало "За"')

bot.run(token, reconnect=True)
