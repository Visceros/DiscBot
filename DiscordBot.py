# coding: utf8

import discord
import asyncio  # check if installed / проверьте, установлен ли модуль
from Cog_utils import Games, Listeners, Utils
import random
import asyncpg  # check if installed / проверьте, установлен ли модуль
import os
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime, time
from operator import itemgetter
from db_connector import db_connection
import logging

ds_logger = logging.getLogger('discord')
ds_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
ds_logger.addHandler(handler)

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
intents.guild_messages = True
intents.voice_states = True
intents.reactions = True
des = 'GoldenBot for Golden Crown discord.'
rgb_colors = ['ff0000', 'ff4800', 'ffaa00', 'ffe200', 'a5ff00', '51ff00', '00ff55', '00ffb6', '00fffc', '00bdff',
              '0055ff', '0600ff', '6700ff', '9f00ff', 'f200ff', 'ff0088', 'ff003b']
bot = commands.Bot(description=des, command_prefix=prefix, intents=intents)


# считываем количество записей в базе данных - получаем не только кол-во записей, но и айдишники.
async def initial_db_read():
    global pool
    async with pool.acquire() as db:
        records_in_db = 0
        records_in_db = await db.fetch('SELECT * FROM discord_users;')
        if len(records_in_db) >= 1:
            users_idlist = []
            records_count = len(records_in_db)
            for i in range(len(records_in_db)):
                ids = records_in_db[i][0]
                users_idlist.append(ids)
            print(records_count, ' пользователей в базе')
            await pool.release(db)
            return records_count, users_idlist
        else:
            return 0, []


# функция для изначального заполнения базы данных пользователями сервера. Работает раз в сутки
@tasks.loop(hours=24.0)
async def initial_db_fill():
    """проверяет, все ли пользователи занесены в ДБ, если нет - дозаписывает недостающих"""
    async with pool.acquire() as db:
        users_count, users_ids = await initial_db_read()
        print('Database reading done.')
        for guild in bot.guilds:
            if 'crown' in guild.name.lower() and 'golden' in guild.name.lower():
                current_members_list = []
                crown = guild
                for member in crown.members:
                    if not member.bot:
                        current_members_list.append(member.id)
                if users_count < len(current_members_list):
                    print('There are new users to add to database')
                    try:
                        for member in crown.members:
                            if not member.bot and member.id not in users_ids:
                                await db.execute(
                                    'INSERT INTO discord_users (id, nickname, join_date) VALUES($1, $2, $3) ON CONFLICT (id) DO NOTHING;',
                                    member.id, member.display_name, member.joined_at)
                    except Exception as e:
                        print('Got error while trying to add missing users to database', e)
                    print('Данные пользователей в базе обновлены')
            else:
                print('Golden Crown guild not found')
        print('database fill cycle ended')


@tasks.loop(minutes=5.0)
async def auto_rainbowise():
    for guild in bot.guilds:
        if 'golden crown' in guild.name.lower():
            crown = bot.get_guild(guild.id)
        try:
            role = discord.utils.find(lambda r: ('РАДУЖНЫЙ НИК' in r.name.upper()), guild.roles)
        except discord.NotFound:
            sys_channel.send('no role for rainbow nick found. See if you have the role with "радужный ник" in its name')
        except Exception as e:
            print(e)
        clr = random.choice(rgb_colors)
        try:
            await role.edit(color=discord.Colour(int(clr, 16)))
        except Exception as e:
            print(
                f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
            await sys_channel.send(
                f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
            await sys_channel.send(f'{e.__cause__}\n{e}')
            print(e.__cause__, e, sep='\n')


# функция сброса варнов у всех юзеров на 0 каждое первое число месяца (дописать очистку данных в LogTable старше 3 мес)
@tasks.loop(hours=24)
async def db_auto_clear():
    if datetime.datetime.now().day == 1:
        async with pool.acquire() as db:
            await db.execute('UPDATE discord_users SET warns=0;')

@bot.event
async def on_ready():
    global pool
    global sys_channel
    pool = await db_connection()
    print('initial database fill starting...')
    try:
        initial_db_fill.start()
    except RuntimeError:
        initial_db_fill.restart()
    try:
        auto_rainbowise.start()
    except RuntimeError:
        auto_rainbowise.restart()
    try:
        db_auto_clear.start()
    except RuntimeError:
        db_auto_clear.restart()
    await accounting()
    print('I\'m ready to serve.')
    bot.add_cog(Games(bot, connection=pool))
    bot.add_cog(Listeners(bot, connection=pool))
#    bot.add_cog(Utils(bot, connection = pool))




# -------------------- Функция ежедневного начисления клановой валюты  --------------------
@tasks.loop(minutes=1)
async def _increment_money(server: discord.Guild):
    async with pool.acquire() as db:
        channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice']
        for member in server.members:
            if str(member.status) not in ['offline', 'idle'] and not member.bot and member.voice is not None:
                if any(
                        item in member.voice.channel.name.lower() for item in channel_groups_to_account_contain) and not (member.voice.self_mute or member.voice.mute):
                    try:
                        gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
                        if gold is not None:
                            gold = int(gold) + 1
                            await db.execute(f'UPDATE discord_users SET gold=$1 WHERE id=$2;', gold, member.id)
                    except Exception as ex:
                        await sys_channel.send(f'Got error trying to give money to user {member}, his gold is {gold}')
                        await sys_channel.send(content=ex)


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
        _increment_money.start(crown)


def subtract_time(time_arg):
    _tmp = time_arg.replace(microsecond=0) - datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0)
    ret = str(abs(_tmp)).replace('days', 'дней')
    return ret

@bot.command()
async def shutdown(ctx):
    async with pool.acquire() as db:
        sys_channel = discord.utils.find(lambda r: (r.name.lower()=='system'), ctx.guild.channels)
        for member in ctx.guild.members:
            if member.voice is not None:
                gold = await db.fetchval(f'SELECT gold from discord_users WHERE id=$1;', member.id)
                await db.execute(
                    f"UPDATE LogTable SET logoff=NOW()::timestamptz(0), gold=$1 WHERE user_id=$2 AND logoff IS NULL;", int(gold), member.id)
            else:
                pass
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
            await ctx.send('You didn\'t specify any subcommand / Вы не указали, что делать с пользователем')
            await ctx.message.delete()
    else:
        await user.show(ctx, ctx.message.author)


@user.command()
@commands.has_permissions(administrator=True)
async def add(ctx, member: discord.Member):
    """Adds the user to database / Добавляем пользователя в базу данных (для новых людей, которых приглашаешь на сервер)"""
    await ctx.message.delete()
    async with pool.acquire() as db:
        try:
            await db.execute('INSERT INTO discord_users (id, nickname, join_date, gold, warns) VALUES($1, $2, $3);',
                             member.id, member.display_name, member.joined_at)
            await ctx.send('user added to database')
        except asyncpg.exceptions.UniqueViolationError:
            await ctx.send('user is already added')

@user.command()
@commands.has_permissions(administrator=True)
async def delete(ctx, member: discord.Member):
    """Удаляем человека из базы бота. Введите команду и через пробел - ник, айди, или дискорд-тег участника."""
    await ctx.message.delete()
    async with pool.acquire() as db:
        await db.execute('DELETE FROM discord_users WHERE id=$1;', member.id)
        await db.execute('DELETE FROM LogTable WHERE user_id=$1;', member.id)


async def count_result_activity(activity_records_list, warns: int):
    activity = datetime.datetime(1, 1, 1, hour=0, minute=0, second=0)
    for item in activity_records_list:
        if item[1] is None:
            activity = activity + (datetime.datetime.now(tz=datetime.timezone.utc) - item[0])
        else:
            activity = (activity + (item[1] - item[0]))
    result_activity = activity - datetime.datetime(1, 1, 1)
    if warns >= 3:
        result_activity = result_activity - datetime.timedelta(minutes=(3 * warns))
    result_activity = result_activity - datetime.timedelta(microseconds=result_activity.microseconds)
    result_hours = int(result_activity.total_seconds()) / 3600
    return round(result_hours, 0)


@user.command()
@commands.has_permissions(administrator=True)
async def show(ctx, member: discord.Member):
    """Shows the info about user/ показываем данные пользователя"""
    global pool
    async with pool.acquire() as db:
        data = await db.fetchrow(f'SELECT * FROM discord_users WHERE id=$1;', member.id)
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
            t_7days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
            t_30days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
            try:
                seven_days_activity_records = await db.fetch(
                    "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login ASC;", t_7days_ago, datetime.datetime.now(), member.id)
                thirty_days_activity_records = await db.fetch(
                    "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login ASC;", t_30days_ago, datetime.datetime.now(), member.id)
                # db_messages = await db.fetch(
                #     "SELECT messages from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login ASC;",t_30days_ago, datetime.datetime.now(), member.id)
                # messages = 0
                # for msg_count in range(len(db_messages)):    ПЕРЕПИСАТЬ
                #     messages += int(msg_count)
            except asyncpg.InterfaceError:
                pool = await db_connection()


            part_1 = f"Никнейм: {member.mention}\nБанковский счёт: `{data['gold']}` :coin:"
            part_2 = f"\nПоложительных ачивок: `{positive_achievements}`\nНегативных ачивок: `{negative_achievements}`"
            part_3 = f"\nАктивность за 7 дней: `{await count_result_activity(seven_days_activity_records, warns)}` час(ов)\nАктивность за 30 дней: `{await count_result_activity(thirty_days_activity_records, warns)}` час(ов)"
            part_4 = f"\nДата присоединения к серверу: `{data['join_date']}`\nID пользователя: `{member.id}`"
            embed = discord.Embed(color=discord.Colour(int('efff00', 16)))
            # embed.add_field(name='', value=f"16*{data['symbol']}")
            embed.add_field(name='Пользователь:', value=part_1, inline=False)
            embed.add_field(name='Ачивки:', value=part_2, inline=False)
            embed.add_field(name='Активность:', value=part_3, inline=False)
            embed.add_field(name='Прочее:', value=part_4, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send('Не найдена информация по вашему профилю.\n'
                           'Функция "Профиль", "Валюта" и "Ачивки" доступна только игрокам с активностью в голосовых каналах.')


@user.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, member: discord.Member):
    """Use this to clear the data about user to default and 0 values / Сбросить данные пользователя в базе"""
    await ctx.message.delete()
    async with pool.acquire() as db:
        await db.execute('DELETE FROM discord_users WHERE id=$1;', member.id)
        await db.execute('INSERT INTO discord_users (id, nickname, join_date, gold, warns) VALUES($1, $2, $3);',
                         member.id, member.display_name, member.joined_at)
        await db.execute('DELETE FROM LogTable WHERE user_id=$1;', member.id)


# -------------КОНЕЦ БЛОКА АДМИН-МЕНЮ ПО УПРАВЛЕНИЮ ПОЛЬЗОВАТЕЛЯМИ--------------

@bot.command()
async def gmoney(ctx, member: discord.Member, gold):
    """This command used to give someone your coins / Эта команда позволяет передать кому-то вашу валюту"""
    author = ctx.message.author
    await ctx.message.delete()
    gold = abs(int(gold))
    async with pool.acquire() as db:
        if ctx.message.author.guild_permissions.administrator:
            gold_was = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
            newgold = int(gold_was) + gold
            await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, member.id)
            await ctx.send(f'Пользователю {member.display_name} начислено +{gold} :coin:.')
        else:
            user_gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', author.id)
            if gold > int(user_gold):
                await ctx.channel.send('У вас нет столько денег.')
                return
            else:
                newgold = int(user_gold) - gold
                await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, author.id)
                target_gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
                newtargetgold = int(target_gold) + gold
                await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newtargetgold, member.id)
                await ctx.send(
                    f'Пользователь {ctx.message.author.display_name} передал пользователю {member.display_name} {gold} валюты.')


@commands.has_permissions(administrator=True)
@bot.command()
async def mmoney(ctx, member: discord.Member, gold):
    """This command takes the coins from selected user / Этой командой забираем у пользователя валюту."""
    await ctx.message.delete()
    async with pool.acquire() as db:
        gold_was = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
        newgold = int(gold_was) - int(gold)
        if newgold < 0:
            newgold = 0
        await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, member.id)
        await ctx.send('У Пользователя {member.mention} было отнято {gold} :coin:.')


@bot.command()
@commands.has_permissions(administrator=True)
async def echo(ctx, msg: str):
    """ prints your message like a bot said it / Бот пишет ваше сообщение так, будто это он сказал."""
    #message = ctx.message.content.split(' ')[1:]
    await ctx.message.delete()
    #await ctx.send(msg)
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
    #await ctx.message.delete()
    users_count, users_ids = await initial_db_read()
    checkrole = discord.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), ctx.guild.roles)
    t_30days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    async with pool.acquire() as db:
        for member in ctx.guild.members:
            if member.id in users_ids and checkrole in member.roles and not (member.id == member.guild.owner_id):
                gold = await db.fetchval("SELECT gold from discord_users WHERE id=$1;", member.id)
                if int(gold) > 0:
                    warns = await db.fetchval("SELECT warns from discord_users WHERE id=$1;", member.id)
                    thirty_days_activity_records = await db.fetch(
                        "SELECT login, logoff from LogTable WHERE user_id=$1 AND login BETWEEN $2::timestamptz AND $3::timestamptz ORDER BY login DESC;", member.id, t_30days_ago, datetime.datetime.now())
                    activity = await count_result_activity(thirty_days_activity_records, warns)
                    result_list.append((member.mention, activity))
    res = sorted(result_list, key=itemgetter(1), reverse=True)
    count = len(res) if count > len(res) else count
    output = "".join(f"{i + 1}: {res[i][0]}, актив: {res[i][1]} часа(ов);\n" for i in range(count))
    embed = discord.Embed(color=discord.Colour(int('efff00', 16)))
    embed.add_field(name='Топ активности', value=output)
    await ctx.send(embed=embed)


@bot.command()
async def antitop(ctx, count: int = 10):
    result_list = []
    await ctx.message.delete()
    async with pool.acquire() as db:
        users_count, users_ids = await initial_db_read()
        checkrole = discord.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), ctx.guild.roles)
        for member in ctx.guild.members:
            if member.id in users_ids and checkrole in member.roles and not (member.id == member.guild.owner_id):
                gold = await db.fetchval("SELECT gold from discord_users WHERE id=$1;", member.id)
                if int(gold) > 0:
                    t_30days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    warns = await db.fetchval("SELECT warns from discord_users WHERE id=$1;", member.id)
                    thirty_days_activity_records = await db.fetch(
                        "SELECT login, logoff from LogTable WHERE user_id=$1 AND login BETWEEN $2::timestamptz AND $3::timestamptz ORDER BY login DESC;", member.id, t_30days_ago, datetime.datetime.now())
                    activity = await count_result_activity(thirty_days_activity_records, warns)
                    time_in_clan = datetime.datetime.now() - member.joined_at
                    if time_in_clan.days//14 > 0:
                        if time_in_clan.days//7 <= 4:
                            if activity/(time_in_clan.days//7) < 10:
                                result_list.append((member.mention, activity, time_in_clan.days//7))
                        elif time_in_clan.days//7 < 4 and activity < 40:
                            result_list.append((member.mention, activity, '4+'))
    res = sorted(result_list, key=itemgetter(1), reverse=False)
    count = len(res) if count > len(res) else count
    # if len(res) > 10:
    #     data = {}
    #     buttons = ['⬅️','1️⃣','➡️']
    #     #page = str((count+10)//10)+'️⃣'
    #     for i in range(len(res)):
    #         data[str(i+1)] = f'{res[i][0]}, актив: {res[i][1]} часа(ов), В клане: {res[i][2]} нед.;\n'
    #     count = 0
    #     for i in range(count+1,count+11):
    #         output = "".join(f"{str(i+1)}: {data[str(i+1)]})")
    #     embed = discord.Embed(color=discord.Colour(int('efff00', 16)))
    #     embed.add_field(name='АнтиТоп активности', value=output)
    #     page_message = await ctx.send(embed=embed)
    #     for button in buttons:
    #         await page_message.add_reaction(button)
    #
    #     def checks(reaction, user):
    #         return reaction in page_message.reactions and user.bot is not True
    #
    #     reaction, user = await bot.wait_for('reaction_add', check=checks)
    #     if str(reaction) == buttons[0]:
    #         count = count-10
    #         count = 0 if count < 0 else count
    #     elif str(reaction) == buttons[2]:
    #         count = count + 10
    #         count = len(res)-10 if count+10 > len(res) else count
    #         for i in range(count + 1, count + 11):
    #             output = "".join(f"{str(i + 1)}: {data[str(i + 1)]})")
    #     embed = discord.Embed(color=discord.Colour(int('efff00', 16)))
    #     embed.add_field(name='АнтиТоп активности', value=output)
    #     page_message.edit(embed=embed)
    #     page = str((count + 10) // 10) G+ '️⃣'
    #     page_message.reaction
    #     pass
    # else:
    output = "".join(f"{i + 1}: {res[i][0]}, актив: {res[i][1]} часа(ов), В клане: {res[i][2]} нед.;\n" for i in range(count))
    embed = discord.Embed(color=discord.Colour(int('efff00', 16)))
    embed.add_field(name='АнтиТоп активности', value=output)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def salary(ctx, amount: int = 1000):
    await ctx.message.delete()
    salary_roles_ids = {651377975106732034, 449837752687656960}
    async with pool.acquire() as db:
        for id in salary_roles_ids:
            role = discord.utils.find(lambda r: (r.id == id), ctx.guild.roles)
            for member in role.members:
                gold_was = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
                newgold = int(gold_was) + amount
                await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, member.id)
                await ctx.send(f'Модератору {member.display_name} выдана зарплата: {amount} :coin:')


@bot.command()
async def warn(ctx, member: discord.Member, count=1):
    if member is not None:
        eligible_roles_ids = {651377975106732034, 449837752687656960}
        moderation_channel = bot.get_channel(773010375775485982)
        chat_channel = bot.get_channel(442565510178013184)
        await ctx.message.delete()
        for role in ctx.author.roles:
            if role.id in eligible_roles_ids or ctx.message.author.guild_permissions.administrator is True:
                async with pool.acquire() as db:
                    user_warns = await db.fetchval('SELECT warns FROM discord_users WHERE id=$1', member.id)
                    user_warns+=count
                    await db.execute('UPDATE discord_users SET warns=$1 WHERE id=$2', user_warns, member.id)
                await moderation_channel.send(f'Модератор {ctx.author.mention} ловит игрока {member.mention} на накрутке и отнимает у него время актива ({3*count} минут(ы).')
                return await chat_channel.send(f'Модератор {ctx.author.mention} ловит игрока {member.mention} на накрутке и отнимает у него время актива.')


bot.run(token, reconnect=True)
