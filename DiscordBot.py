# coding: utf8

import discord
import asyncio  # check if installed / проверьте, установлен ли модуль
from Cog_utils import Games, Listeners, Utils
import random
import asyncpg  # check if installed / проверьте, установлен ли модуль
import os
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime
from operator import itemgetter
from db_connector import db_connection
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

prefix = '!'
intents = discord.Intents.default()
intents.members = True
intents.presences = True
des = 'GoldenBot for Golden Crown discord.'
rgb_colors = ['ff0000', 'ff4800', 'ffaa00', 'ffe200', 'a5ff00', '51ff00', '00ff55', '00ffb6', '00fffc', '00bdff',
              '0055ff', '0600ff', '6700ff', '9f00ff', 'f200ff', 'ff0088', 'ff003b']
bot = commands.Bot(description=des, command_prefix=prefix, intents=intents)


# считываем количество записей в базе данных  - обновлена логика. получаем не только кол-во записей, но и айдишники! ПРОВЕРИТЬ!
async def initial_db_read():
    global pool
    db = await pool.acquire()
    records_in_db = 0
    records_in_db = await db.fetch('SELECT * FROM discord_users;')
    if len(records_in_db) >= 1:
        users_idlist = []
        records_count = len(records_in_db)
        for i in range(1, records_count + 1):
            ids = await db.fetchval(f'SELECT id FROM discord_users ORDER BY id LIMIT 1 OFFSET {i - 1};')
            users_idlist.append(ids)
        print(records_count, ' пользователей в базе')
        await pool.release(db)
        return records_count, users_idlist
    else:
        await pool.release(db)
        return 0, []


# функция для изначального заполнения базы данных пользователями сервера. Работает раз в сутки
@tasks.loop(hours=24.0)
async def initial_db_fill():
    """проверяет, все ли пользователи занесены в ДБ, если нет - дозаписывает недостающих"""
    db = await pool.acquire()
    users_count, users_ids = await initial_db_read()
    for guild in bot.guilds:
        # if 'free zone' in guild.name.lower():
        if 'golden crown' in guild.name.lower():
            current_members_list = []
            crown = bot.get_guild(guild.id)
            global sys_channel
            for member in crown.members:
                if not member.bot:
                    current_members_list.append(member.id)
            if users_count < len(current_members_list):
                try:
                    for member in crown.members:
                        if not member.bot and member.id not in users_ids:
                            await db.execute(
                                'INSERT INTO discord_users (id, nickname, join_date, gold, warns) VALUES($1, $2, $3, 0, 0) ON CONFLICT (id) DO NOTHING;',
                                member.id, member.display_name, member.joined_at)
                finally:
                    await pool.release(db)
                print('Данные пользователей в базе обновлены')
        sys_channel = discord.utils.get(guild.channels, name='system')
        if not sys_channel:
            print('creating system channel')
            try:
                admin_roles = [role for role in guild.roles if role.permissions.administrator]
                sys_channel_overwrites = {}
                for role in admin_roles:
                    sys_channel_overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
                sys_channel_overwrites[guild.default_role] = discord.PermissionOverwrite(read_messages=False,
                                                                                         send_messages=False,
                                                                                         view_channel=False)
                sys_channel = await guild.create_text_channel('system', overwrites=sys_channel_overwrites,
                                                              reason='creating a channel for system messages')
            except discord.Forbidden:
                print(f'No permissions to create system channel in {guild} server')
            except Exception as ex:
                print('Couldn\'t create #system channel, something is wrong:\n')
                print(ex)
        else:
            print('system channel found')
            pass
    print('database fill cycle ended')
    await pool.release(db)


@tasks.loop(minutes=5.0)
async def auto_rainbowise():
    for guild in bot.guilds:  # Проверить - нужно ли вообще это условие?
        if 'golden crown' in guild.name.lower():
            crown = bot.get_guild(guild.id)
        else:
            print('Не найден сервер "Golden Crown"')
        try:
            role = discord.utils.find(lambda r: ('РАДУЖНЫЙ НИК' in r.name.upper()), guild.roles)
            print(role)
        except discord.NotFound:
            sys_channel.send('no role for rainbow nick found. See if you have the role with "радужный ник" in its name')
        except Exception as e:
            print(e)
        clr = random.choice(rgb_colors)
        try:
            await role.edit(color=discord.Colour(int(clr, 16)))
            print(f'changed color for {role}')
        except Exception as e:
            print(
                f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
            await sys_channel.send(
                f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
            await sys_channel.send(f'{e.__cause__}\n{e}')
            print(e.__cause__, e, sep='\n')


@bot.event
async def on_ready():
    global pool
    pool = await db_connection()
    await asyncio.sleep(2)
    print('initial database fill starting...')
    try:
        initial_db_fill.start()
    except RuntimeError:
        initial_db_fill.restart()
    await asyncio.sleep(1)
    try:
        auto_rainbowise.start()
    except RuntimeError:
        auto_rainbowise.restart()
    await asyncio.sleep(1)
    await accounting()
    print('I\'m ready to serve.')
    bot.add_cog(Games(bot, connection=pool))
    bot.add_cog(Listeners(bot, sys_channel=sys_channel, connection=pool))
#    bot.add_cog(Utils(bot, connection = pool))


# -------------------- Функция ежедневного начисления клановой валюты  --------------------
@tasks.loop(minutes=1)
async def _increment_money(server: discord.Guild):
    db = await pool.acquire()
    channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice']
    try:
        for member in server.members:
            if any(item in member.voice.channel.name.lower() for item in
                   channel_groups_to_account_contain):
                if str(member.status) not in ['offline', 'invisible', 'dnd'] and not member.bot and member.voice is not None:
                    gold = await db.fetchval(f'SELECT Gold FROM discord_users WHERE id={member.id};')
                    gold = int(gold) + 1
                    await db.execute(f'UPDATE discord_users SET gold={gold} WHERE id={member.id};')
    except Exception as ex:
        await sys_channel.send(f'Got error trying to give money to user {member}, his gold is {gold}')
        await sys_channel.send(content=(ex, ex.__cause__, ex.__context__))
    finally:
        await pool.release(db)


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


async def shutdown(ctx):
    db = await pool.acquire()
    for member in ctx.guild.members:
        if member.voice is not None:
            gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id}')
            await db.execute(
                f"UPDATE LogTable SET logoff='{datetime.datetime.now().replace(microsecond=0)}'::timestamptz, gold={gold} WHERE user_id={member.id} AND logoff IS NULL;")
    await asyncio.sleep(5)
    await sys_channel.send('Shutdown complete')
    exit(1)



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
        await user.show(ctx, ctx.message.author)


@user.command()
@commands.has_permissions(administrator=True)
async def add(ctx, member: discord.Member):
    """Adds the user to database / Добавляем пользователя в базу данных (для новых людей, которых приглашаешь на сервер)"""
    await ctx.message.delete()
    db = await pool.acquire()
    try:
        await db.execute('INSERT INTO discord_users (id, nickname, join_date, gold, warns) VALUES($1, $2, $3);',
                         member.id, member.display_name, member.joined_at)
        await ctx.send('user added to database')
    except asyncpg.exceptions.UniqueViolationError:
        await ctx.send('user is already added')
    finally:
        await pool.release(db)

@user.command()
@commands.has_permissions(administrator=True)
async def delete(ctx, member: discord.Member):
    """Удаляем человека из базы бота. Введите команду и через пробел - ник, айди, или дискорд-тег участника."""
    await ctx.message.delete()
    db = await pool.acquire()
    await db.execute(f'DELETE FROM discord_users WHERE id={member.id};')
    await db.execute(f'DELETE FROM LogTable WHERE user_id={member.id};')
    await pool.release(db)


async def count_result_activity(activity_records_list, warns: int):
    activity = datetime.datetime(1, 1, 1, hour=0, minute=0, second=0)
    for item in activity_records_list:
        if item[1] is None:
            activity = activity + (datetime.datetime.now(tz=datetime.timezone.utc) - item[0])
        else:
            activity = (activity + (item[1] - item[0]))
    result_activity = activity - datetime.datetime(1, 1, 1)
    if warns > 0:
        result_activity = result_activity - datetime.timedelta(minutes=(10 * warns))
    result_activity = result_activity - datetime.timedelta(microseconds=result_activity.microseconds)
    # result_hours = result_activity.days*24+result_activity.hour
    result_hours = int(result_activity.total_seconds()) / 3600
    return round(result_hours, 1)


@user.command()
@commands.has_permissions(administrator=True)
async def show(ctx, member: discord.Member):
    """Shows the info about user/ показываем данные пользователя"""
    db = await pool.acquire()
    data = await db.fetchrow(f'SELECT * FROM discord_users WHERE id={member.id};')
    if data is not None:
        achievments = 0
        negative_achievements = 0
        warns = int(data['warns'])
        for role in member.roles:
            if 'ачивка' in role.name.lower():
                achievments += 1
                if role.color == discord.Colour(int('ff4f4f', 16)):
                    negative_achievements += 1
        positive_achievements = achievments - negative_achievements
        try:
            seven_days_activity_records = await db.fetch(
                f"SELECT login, logoff from LogTable WHERE login BETWEEN '{datetime.datetime.now() - datetime.timedelta(days=7)}'::timestamptz AND '{datetime.datetime.now()}'::timestamptz AND user_id={member.id} ORDER BY login ASC;")
            thirty_days_activity_records = await db.fetch(
                f"SELECT login, logoff from LogTable WHERE user_id={member.id} AND login BETWEEN '{datetime.datetime.now() - datetime.timedelta(days=30)}'::timestamptz AND '{datetime.datetime.now()}'::timestamptz ORDER BY login ASC;")
        finally:
            await pool.release(db)

        part_1 = f"Никнейм: {member.mention}\nБанковский счёт: `{data['gold']}` :coin:"
        part_2 = f"\nПоложительных ачивок: `{positive_achievements}`\nНегативных: `{negative_achievements}`"
        part_3 = f"\nАктивность за 7 дней: `{await count_result_activity(seven_days_activity_records, warns)}` час(ов)\nАктивность за 30 дней: `{await count_result_activity(thirty_days_activity_records, warns)}` час(ов)"
        part_4 = f"\nДата присоединения к серверу: `{data['join_date']}`\nID пользователя: `{member.id}`"
        embed = discord.Embed(color=discord.Colour(int('efff00', 16)))
        # embed.add_field(name='', value=f"17*{data['symbol']}")
        embed.add_field(name='Пользователь:', value=part_1, inline=False)
        embed.add_field(name='Ачивки:', value=part_2, inline=False)
        embed.add_field(name='Активность:', value=part_3, inline=False)
        embed.add_field(name='Прочее:', value=part_4, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send('Не найдена информация по вашему профилю.\n'
                       'Функция "Профиль", "Валюта" и "Ачивки" доступна только игрокам с активностью в голосовых каналах.')


@bot.command()
async def gmoney(ctx, member: discord.Member, gold):
    """This command used to give someone your coins / Эта команда позволяет передать кому-то вашу валюту"""
    author = ctx.message.author
    await ctx.message.delete()
    db = await pool.acquire()
    gold = abs(int(gold))
    try:

        if ctx.message.author.guild_permissions.administrator:
            gold_was = await db.fetchval(f'SELECT gold FROM discord_users WHERE id={member.id};')
            newgold = int(gold_was) + gold
            await db.execute(f'UPDATE discord_users SET gold={newgold} WHERE id={member.id};')
            await ctx.send(f'Пользователю {member.display_name} начислено +{gold} :coin:.')
        else:
            user_gold = await db.fetchval(f'SELECT gold FROM discord_users WHERE id={author.id};')
            if gold > int(user_gold):
                await ctx.channel.send('У вас нет столько денег.')
                return
            else:
                newgold = int(user_gold) - gold
                await db.execute(f'UPDATE discord_users SET gold={newgold} WHERE id={author.id};')
                target_gold = await db.fetchval(f'SELECT gold FROM discord_users WHERE id={member.id};')
                newtargetgold = int(target_gold) + gold
                await db.execute(f'UPDATE discord_users SET gold={newtargetgold} WHERE id={member.id};')
                await ctx.send(
                    f'Пользователь {ctx.message.author.display_name} передал пользователю {member.display_name} {gold} валюты.')
    finally:
        await pool.release(db)


@commands.has_permissions(administrator=True)
@bot.command()
async def mmoney(ctx, member: discord.Member, gold):
    """This command takes the coins from selected user / Этой командой забираем у пользователя валюту."""
    await ctx.message.delete()
    db = await pool.acquire()
    gold_was = await db.fetchval(f'SELECT gold FROM discord_users WHERE id={member.id};')
    newgold = int(gold_was) - int(gold)
    if newgold < 0:
        newgold = 0
    await db.execute(f'UPDATE discord_users SET gold={newgold} WHERE id={member.id};')
    await ctx.send(f'У Пользователя {member.mention} было отнято {gold} :coin:.')
    await pool.release(db)


@user.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, member: discord.Member):
    """Use this to clear the data about user to default and 0 values / Сбросить данные пользователя в базе"""
    await ctx.message.delete()
    db = await pool.acquire()
    await db.execute(f'DELETE FROM discord_users WHERE id={member.id};')
    await db.execute(f'INSERT INTO discord_users (id, nickname, join_date, gold, warns) VALUES($1, $2, $3);',
                     member.id, member.display_name, member.joined_at)
    await db.execute(f'DELETE FROM LogTable WHERE user_id={member.id};')
    await pool.release(db)


# -------------КОНЕЦ БЛОКА АДМИН-МЕНЮ ПО УПРАВЛЕНИЮ ПОЛЬЗОВАТЕЛЯМИ--------------


@bot.command()
async def echo(ctx, msg: str):
    """ prints your message like a bot said it / Бот пишет ваше сообщение так, будто это он сказал."""
    message = ctx.message
    await message.delete()
    await ctx.send(msg)


@bot.command()
async def me(ctx):
    """Command to see your profile / Этой командой можно увидеть ваш профиль"""
    usr = ctx.message.author
    await show(ctx, usr)


@bot.command()
async def u(ctx, member: discord.Member):
    await show(ctx, member)
    await ctx.message.delete()


@bot.command()
@commands.has_permissions(administrator=True)
async def danet(ctx, polltime=60):
    """resends the replied message and adds 👍 and 👎 emoji reactions to it - making it look like a poll
    and after provided number of minutes counts the result and sends a message about it mentioning you
    """
    start_time = datetime.datetime.now().replace(microsecond=0)
    msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    await ctx.message.delete()
    poll_msg = await ctx.send(f'Стартовал опрос:\n\n{msg.content}')
    await poll_msg.add_reaction('👍')
    await poll_msg.add_reaction('👎')
    end_time = start_time + datetime.timedelta(minutes=polltime)
    while True:
        if datetime.datetime.now() > end_time:
            break
        else:
            await asyncio.sleep(5)
    poll_msg = await ctx.channel.fetch_message(poll_msg.id)
    for reaction in poll_msg.reactions:
        if str(reaction.emoji) == '👍':
            yes = reaction.count
        elif str(reaction.emoji) == '👎':
            no = reaction.count
        elif not yes or not no or yes == 0 or no == 0:
            await sys_channel.send(
                f'{ctx.message.author.mention} Опрос на сообщении {poll_msg.content} выполнен с ошибками, отсутствует один из обязательных эмодзи - 👍 или 👎')
        else:
            pass
    if yes > no:
        await poll_msg.reply(content=f'{ctx.message.author.mention} опрос завершён, большинство проголосовало "За"')
        await sys_channel.send(content=f'{ctx.message.author.mention} опрос завершён, большинство проголосовало "За"')
    elif no > yes:
        await poll_msg.reply(content=f'{ctx.message.author.mention} опрос завершён, большинство проголосовало "Против"')
        await sys_channel.send(
            content=f'{ctx.message.author.mention} опрос завершён, большинство проголосовало "Против"')
    elif yes == no:
        await poll_msg.reply(
            content=f'{ctx.message.author.mention} участники голосования не смогли определиться с выбором')
        await sys_channel.send(
            content=f'{ctx.message.author.mention} участники голосования не смогли определиться с выбором')


@bot.command()
async def poll(ctx, options: int, time=60):
    if options > 9:
        await ctx.send(
            content=f"{ctx.message.author.mention}, количество вариантов в голосовании должно быть не больше 9!")
        return
    await ctx.message.delete()
    messages = await ctx.channel.history(limit=2).flatten()
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    message = await ctx.channel.fetch_message(messages[0].id)
    for num in range(options):
        await message.add_reaction(reactions[num])
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(minutes=time)
    while True:
        if datetime.datetime.now() > end_time:
            break
        else:
            await asyncio.sleep(20)
    message = await ctx.channel.fetch_message(messages[0].id)
    reactions_count_list = []
    for reaction in message.reactions:
        reactions_count_list.append((str(reaction.emoji), reaction.count))
    sort_reactions = sorted(reactions_count_list, key=itemgetter(1), reverse=True)
    await ctx.channel.send(
        content=f"{ctx.message.author.mention}, опрос завершён:\n ```{message.content}```\n Победил вариант № {sort_reactions[0][0]}")


@bot.command()
async def top(ctx, count: int = 10):
    result_list = []
    await ctx.message.delete()
    db = await pool.acquire()
    users_count, users_ids = await initial_db_read()
    checkrole = discord.utils.find(lambda r: ('СОКЛАН' in r.name.upper()), ctx.guild.roles)
    for member in ctx.guild.members:
        if member.id in users_ids and checkrole in member.roles:
            gold = await db.fetchval(f"SELECT gold from discord_users WHERE id={member.id};")
            if int(gold) > 0:
                warns = await db.fetchval(f"SELECT warns from discord_users WHERE id={member.id};")
                thirty_days_activity_records = await db.fetch(
                    f"SELECT login, logoff from LogTable WHERE user_id={member.id} AND login BETWEEN '{datetime.datetime.now() - datetime.timedelta(days=30)}'::timestamptz AND '{datetime.datetime.now()}'::timestamptz ORDER BY login ASC;")
                activity = await count_result_activity(thirty_days_activity_records, warns)
                result_list.append((member.mention, activity))
    res = sorted(result_list, key=itemgetter(1), reverse=True)
    count = len(res) if count > len(res) else count
    output = ""
    for i in range(count):
        output += f"{i + 1}: {res[i][0]}, актив: {res[i][1]} часа(ов);\n"
    embed = discord.Embed(color=discord.Colour(int('efff00', 16)))
    embed.add_field(name='Топ активности', value=output)
    await ctx.channel.send(embed=embed)
    await pool.release(db)


bot.run(token, reconnect=True)
