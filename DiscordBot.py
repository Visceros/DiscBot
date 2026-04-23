# coding: utf8
import json
import io
import ast
import logging
import csv
import disnake
import asyncio  # check if installed / проверьте, установлен ли модуль
import random
import asyncpg  # check if installed / проверьте, установлен ли модуль
import os
import datetime
from disnake.ext import commands, tasks
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from operator import itemgetter
from db_connector import db_connection
from Cog_utils import Listeners, Games, Player, Shop
from buttons import Giveaway, RenameModal, StickyNoteModal


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
token = os.getenv('BOT_KEY')
if token is None:
    print('Could not receive token. Please check if your .env file has the correct token')
    exit(1)

tz = datetime.timezone(datetime.timedelta(hours=3))
intents = disnake.Intents.all()
rgb_colors = ['ff0000', 'ff4800', 'ffaa00', 'ffe200', 'a5ff00', '51ff00', '00ff55', '00ffb6', '00fffc', '00bdff',
              '0055ff', '0600ff', '6700ff', '9f00ff', 'f200ff', 'ff0088', 'ff003b']
command_sync_flags = commands.CommandSyncFlags(sync_commands_debug=True, sync_on_cog_actions=True)
bot = commands.InteractionBot(intents=intents, command_sync_flags=command_sync_flags)
sys_channel = None

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
    # checks if all the users added to the database. If not - adds them
    async with pool.acquire() as db:
        users_count, users_ids = await initial_db_read()
        print('Database reading done.')
        _crown = False
        for guild in bot.guilds:
            if 'golden' in guild.name.lower() and 'crown' in guild.name.lower():
                _crown = True
                current_members_list = []
                crown = bot.get_guild(guild.id)
                sys_channel = disnake.utils.find(lambda r: (r.name.lower() == 'system'), guild.channels)
                if sys_channel is None:
                    sys_channel = await guild.create_text_channel('system', position=len(guild.channels), overwrites={guild.default_role: disnake.PermissionOverwrite(view_channel=False)})
                for member in crown.members:
                    if not member.bot:
                        current_members_list.append(member.id)
                if users_count < len(current_members_list):
                    print('There are new users to add to database')
                    try:
                        for member in crown.members:
                            if not member.bot and member.id not in users_ids:
                                if not member.display_name == '[Ранг] Nickname (ВашеИмя) GC':
                                    await db.execute(
                                        'INSERT INTO discord_users (id, nickname, join_date) VALUES($1, $2, $3) ON CONFLICT (id) DO NOTHING;',
                                        member.id, member.display_name, member.joined_at)
                    except Exception as e:
                        print('Got error while trying to add missing users to database', e)
                    print('Данные пользователей в базе обновлены')
        if _crown is False:
            print('Golden Crown guild not found')
        print('database fill cycle ended')


@tasks.loop(minutes=5.0)
async def auto_rainbowise():
    for guild in bot.guilds:
        global sys_channel
        try:
            sys_channel = disnake.utils.find(lambda r: ('SYSTEM' in r.name.upper()), guild.channels)
            role = disnake.utils.find(lambda r: ('РАДУЖНЫЙ НИК' in r.name.upper()), guild.roles)
            clr = random.choice(rgb_colors)
            if role is not None:
                await role.edit(color=disnake.Colour(int(clr, 16)))
        except disnake.NotFound:
            await sys_channel.send('no role for rainbow nick found. See if you have the role with "радужный ник" in its name')
        except Exception as e:
            print(
                f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
            await sys_channel.send(
                f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
            await sys_channel.send(f'{e.__cause__}\n{e}')
            print(e.__cause__, e, sep='\n')


# функция сброса варнов у всех юзеров на 0 каждое первое число месяца (дописать очистку данных в LogTable старше 3 мес)
@tasks.loop(hours=24)
async def monthly_task():

    # События в первый день месяца
    if datetime.datetime.now(tz=tz).day == 1:
        async with pool.acquire() as db:
            guild = bot.get_guild(198134036890255361)
            for user in guild.members:
                t_30days_ago = datetime.datetime.now(tz=tz) - datetime.timedelta(days=30)
                data = await db.fetchrow(f'SELECT * FROM discord_users WHERE id=$1;', user.id)
                if data is not None and data['warns'] is not None:
                    warns = int(data['warns'])
                    thirty_days_activity_records = await db.fetch(
                        "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login DESC;", t_30days_ago, datetime.datetime.now(), user.id)
                    minutes = await count_result_activity(thirty_days_activity_records, warns)
                    time_in_clan = datetime.datetime.now(tz=tz) - user.joined_at
                    if minutes == 0 and time_in_clan.days//7 >= 8:
                        await db.execute('DELETE FROM LogTable CASCADE WHERE user_id=$1;', user.id)
                        await db.execute('DELETE FROM discord_users CASCADE WHERE id=$1;', user.id)
                        # Убрана проверка на роль СОКЛАНЫ
                        # checkrole = disnake.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), guild.roles)
                        # if checkrole in user.roles:
                        #     await user.remove_roles(checkrole)
                else:
                    await db.execute('DELETE FROM LogTable CASCADE WHERE user_id=$1;', user.id)
                    await db.execute('DELETE FROM discord_users CASCADE WHERE id=$1;', user.id)



    # События во второй день месяца
    if datetime.datetime.now(tz=tz).day == 2:

        # обновление ТОПов клана
        guild = bot.get_guild(198134036890255361)
        result_list = []
        top_in_clan_rId = 422480212840939562
        top_in_clan_r = disnake.utils.find(lambda r: (r.id == top_in_clan_rId), guild.roles)
        check_role = disnake.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), guild.roles)
        t_30days_ago = datetime.datetime.now(tz=tz) - datetime.timedelta(days=30)
        async with pool.acquire() as db:
            for member in guild.members:
                if top_in_clan_r in member.roles:
                    await member.remove_roles(top_in_clan_r)
                if check_role in member.roles and not (member.id == guild.owner_id):
                    warns = await db.fetchval("SELECT warns from discord_users WHERE id=$1;", member.id)
                    thirty_days_activity_records = await db.fetch(
                        "SELECT login, logoff from LogTable WHERE user_id=$1 AND login BETWEEN $2::timestamptz AND $3::timestamptz ORDER BY login DESC;",
                        member.id, t_30days_ago, datetime.datetime.now(tz=tz))
                    activity = await count_result_activity(thirty_days_activity_records, warns)
                    result_list.append((member, activity))
            res = sorted(result_list, key=itemgetter(1), reverse=True)
            count = 3
            for record in res:
                usr = record[0] #Берём пользователя с самой высокой активностью
                await usr.add_roles(top_in_clan_r) # и даём ему роль топ клана
                count-=1 # и так 3 раза, ибо count = 3.
                if count == 0:
                    break

        # снятие варнов на 2 день месяца
        async with pool.acquire() as db:
            await db.execute('UPDATE discord_users SET warns=0;')

        # снятие ачивки "накрутчик" на 2 день месяца
        for user in bot.get_guild(198134036890255361).members:
            for role in user.roles:
                if role.name.lower() == 'накрутчик': await user.remove_roles(role)

        # раздача зарплаты верховному совету на 2 день месяца
        for guild in bot.guilds:
            amount = 1000  # количество заработной платы
            salary_roles_ids = {651377975106732034, 449837752687656960, 1489831507433488586} # ID ролей, которым начисляется зарплата
            async with pool.acquire() as db:
                for id in salary_roles_ids:
                    role = disnake.utils.find(lambda r: (r.id == id), guild.roles)
                    if role is not None:
                        for member in role.members:
                            gold_was = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
                            newgold = int(gold_was) + amount
                            await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, member.id)


@tasks.loop(hours=24)
async def daily_task():
    while not (datetime.datetime.now(tz=tz).hour == 0 and datetime.datetime.now(tz=tz).minute == 0):
        await asyncio.sleep(10)
    else:
        global sys_channel
        # Проверяем не истёк ли срок каких-либо покупок из списка в Логе покупок
        async with pool.acquire() as db:
            records_list = await db.fetch("SELECT * FROM ShopLog WHERE date_trunc('day', expiry_date)=CURRENT_DATE")
            for record in records_list:
                if record['expiry_date'].date() == datetime.date.today(): # если срок действия покупки 30 дней вышел
                    product = await db.fetchrow('SELECT * FROM Shop WHERE product_id=$1', record['product_id'])

                    # Получаем сущность пользователя и сервера
                    for server in bot.guilds:
                        for member in server.members:
                            if member.id == record['buyer_id']:
                                user = member
                                guild = server
                                break

                    # Если это роль - снимаем роль
                    if product['product_type'] == 'role':
                        role = disnake.utils.find(lambda r: (r.name.lower() == record['item_name'].lower()), guild.roles)
                        if role is not None and role in user.roles:
                            try:
                                await user.remove_roles(role)
                                print('Снимаю', role.name, 'у', user.display_name)
                            except:
                                await sys_channel.send(f'Ошибка при снятии купленной роли {product["name"]} с пользователя {user.display_name}, id {user.id}. Не удалось найти соответствующую роль на сервере.')

                    #Если это скин профиля - меняем скин на дефолтный (если только не был куплен другой)
                    elif product['product_type'] == 'profile_skin':
                        current_profile_skin = await db.fetchval('SELECT profile_pic from discord_users WHERE id=$1', user.id)
                        json_data = json.loads(product['json_data'])
                        if current_profile_skin == json_data['image_name']:  #Если фон профиля не сменился
                            try:
                                await db.execute('UPDATE discord_users SET profile_pic=$1, profile_text_color=$2 WHERE id=$3', 'default_profile_pic.png', '(255,207,102,255)', user.id)
                                print('Вернул стандартный фон профиля пользователяю', user.display_name)
                            except Exception as e:
                                await sys_channel.send(f'{guild.owner.mention} Произошла ошибка при возвращении стандартного фона профиля для пользователя {user.mention}:')
                                await sys_channel.send(str(e))


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
        monthly_task.start()
    except RuntimeError:
        monthly_task.restart()
    daily_task.start()
    await accounting()
    print('I\'m ready to serve.')
    bot.add_cog(Games(bot, connection=pool))
    bot.add_cog(Listeners(bot, connection=pool))
    bot.add_cog(Shop(bot, connection=pool))
    bot.add_cog(Player(bot))




# -------------------- Функция ежедневного начисления клановой валюты  --------------------
@tasks.loop(minutes=1)
async def _increment_money(server: disnake.Guild):
    """
    Give money to users

    Parameters
    ----------
    server: a discord Server
    """
    async with pool.acquire() as db:
        #channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice'] # Count voice activity for money only in specific channels
        for member in server.members:
            if not member.bot:
                if str(member.status) not in ['offline'] and member.voice is not None:
                    #if any(item in member.voice.channel.name.lower() for item in channel_groups_to_account_contain) and not (member.voice.self_mute or member.voice.mute): # Give money only in specific channels
                    if not (member.voice.self_mute or member.voice.mute):
                        try:
                            gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
                            if gold is not None:
                                gold = int(gold) + 1
                                await db.execute(f'UPDATE discord_users SET gold=$1 WHERE id=$2;', gold, member.id)
                            else:
                                gold = 1
                                await db.execute(f'UPDATE discord_users SET gold=$1 WHERE id=$2;', gold, member.id)
                        except Exception as e:
                            await sys_channel.send(f'Got error trying to give money to user {member}, his gold is {gold}')
                            await sys_channel.send(content=e.__str__())

                chat_history:list = await member.history(after=datetime.datetime.now(tz=tz)-datetime.timedelta(minutes=1)).flatten()
                try:
                    m = chat_history[0]
                    print(m.author, f'sent {len(chat_history)} messages in', m.channel)
                    await sys_channel.send(f'{m.author} sent {len(chat_history)} messages in {m.channel}')
                except IndexError:
                    pass
                except disnake.HTTPException:
                    print(e.__str__())
                    # try:
                    #     gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
                    #     if gold is not None:
                    #         gold = int(gold) + 1
                    #         await db.execute(f'UPDATE discord_users SET gold=$1 WHERE id=$2;', gold, member.id)
                    #     else:
                    #         gold = 1
                    #         await db.execute(f'UPDATE discord_users SET gold=$1 WHERE id=$2;', gold, member.id)
                    # except Exception as e:
                    #     await sys_channel.send(f'Got error trying to give money to user {member}, his gold is {gold}')
                    #     await sys_channel.send(content=e.__str__())

# Проверяем кто из пользователей в данный момент онлайн и находится в голосовом чате. Начисляем им валюту
async def accounting():
    crown = None
    try:
        async for guild in bot.fetch_guilds():
            if 'golden' in guild.name.lower() and 'crown' in guild.name.lower():
                crown = bot.get_guild(guild.id)
    except Exception as e:
        print(e)
    else:
        _increment_money.start(crown)

# -------------------- Конец функции ежедневного начисления клановой валюты --------------------

def subtract_time(time_arg):
    """
    deals with timezones

    Parameters
    ----------
    time_arg: time to subtract from
    """
    _tmp = time_arg.replace(microsecond=0) - datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0)
    ret = str(abs(_tmp)).replace('days', 'дней')
    return ret


@bot.slash_command(dm_permission=True)
async def shutdown(inter:disnake.ApplicationCommandInteraction):
    """
    shuts the bot down

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction object
    """
    async with pool.acquire() as db:
        sys_channel = disnake.utils.find(lambda r: (r.name.lower()=='system'), inter.guild.channels)
        for member in inter.guild.members:
            if member.voice is not None:
                gold = await db.fetchval(f'SELECT gold from discord_users WHERE id=$1;', member.id)
                await db.execute(
                    f"UPDATE LogTable SET logoff=NOW()::timestamptz(0), gold=$1 WHERE user_id=$2 AND logoff IS NULL;", int(gold), member.id)
                # await member.move_to(None)
        # clan_role = disnake.utils.find(lambda r: 'соклан' in r.name.lower(), inter.guild.roles)
        # chat_channel = disnake.utils.find(lambda r: ('чат-сервера' in r.name.lower()), inter.guild.channels)
        # await chat_channel.send(f'{clan_role.mention} вы были автоматически отключены от голосовых каналов в связи с перезапуском бота, чтобы у вас корректно учитывалась активность. Просим переподключиться, спасибо.')
        await asyncio.sleep(2)
        await sys_channel.send('Shutdown complete')
        exit(1)


@bot.slash_command()
async def set_rename(inter:disnake.ApplicationCommandInteraction):
    channel = inter.channel
    history_messages = await channel.history(limit=1).flatten()
    the_msg = history_messages[0]
    btn_rename = disnake.ui.Button(label='Переименоваться', custom_id='rename', style=disnake.ButtonStyle.primary)
    await the_msg.edit(components=btn_rename)


@bot.slash_command(dm_permission=False)
async def gchelp(inter:disnake.ApplicationCommandInteraction, helptype:str=None):
    """
    A standard help command

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    helptype: пустой, "mod" или "admin"
    """
    embed = disnake.Embed(color=disnake.Colour(int('efff00', 16)))
    basic_help = """    !me - посмотреть свой профиль\n
!top - посмотреть топ пользователей по активности\n
!antitop - посмотреть анти-топ пользователей по активности\n
!gmoney <имя_пользователя> <количество> или <id пользователя> <количество> - отдать кому-то свои деньги\n
!poll <кол-во опций> <длительность в минутах> - возможность сделать из сообщения опрос. Команда пишется, "ответом" на сообщение к которому хотите прикрепить опрос.
Сообщение, на которое вы отвечаете, дублируется и к нему в виде реакций назначаются опции для голосования (до 9 опций)\n
!chest - игра в сундучки (только в канале "сундучки")\n
!slots <ставка> - игра казино, где можно выиграть клановую валюту, или проиграть (только в канале казино) мин ставка = 50.\n
Посмотреть информацию для модератора - /gchelp mod | для админа - /gchelp admin."""

    mod_help = basic_help + """
    !warn <пользователь> <кол-во>- выдать кому-то предупреждение и снять 3 минуты активности. Аргументом <пользователь> может 
    являться айди юзера, его имя, или упоминание. Можно выдать несколько предупреждений поставив после пользователя пробел и число.\n
    !u <пользователь> - посмотреть профиль любого пользователя.\n"""

    admin_help = """!me - посмотреть свой профиль
!u <пользователь> - посмотреть профиль любого пользователя.
!top - посмотреть топ пользователей по активности
!antitop - посмотреть анти-топ пользователей по активности
!gmoney <имя_пользователя> <количество> или <id_пользователя> <количество> - отдать кому-то свои деньги
!mmoney <имя_пользователя> <количество> или <id_пользователя> <количество> - отнять у кого-то валюту.
!salary - раздать зарплату совету/исполнителям
!warn <пользователь> <кол-во>- выдать кому-то предупреждение и снять 3 минуты активности. Используется ID юзера, имя или упоминание. Количество предупреждений задаётся числом после пробела.
!poll <кол-во опций> <длительность в минутах> - возможность сделать из сообщения опрос. Команда пишется, "ответом" на сообщение к которому хотите прикрепить опрос.
!danet - работает как и !poll, только вместо реакций с вариантами, используются реакции 👍 и 👎 как "да" или "нет".
!user [add|delete|clear] <пользователь>- команда для управления пользователями в базе данных:
add - Добавляет пользователя в базу данных
delete - Удаляет пользователя из базы данных
clear - Сбрасывает статистику пользователя, как будто он только что присоединился к клану.
!echo <сообщение> или <"сообщение из нескольких слов"> - отправить сообщение, как будто его сказал бот.
!chest - игра в сундучки (только в канале "сундучки")
!slots <ставка> - игра казино, где можно выиграть клановую валюту, или проиграть (только в канале казино) мин ставка = 50.
!fortuna - колесо фортуны с 26 секторами.
!bingo <число> - бот составит число из указанного количества цифр, исходно - 3 цифры.
!buy <название> - купить товар, указав его номер или название
!shop add <тип> <название> <цена> <длительность> - добавить товар (только администраторы) - укажите тип товара, название,  
его цену и длительность (если продаётся время использования)
!shop delete <название> или <ID>- удалить товар из магазина (только администраторы)"""
    if helptype==None:
        embed.add_field(name='Справка пользователя', value=basic_help)
        await inter.send(embed=embed)
    elif helptype=="mod":
        await inter.send(mod_help, ephemeral=True)
    elif helptype=="admin":
        if inter.author.guild_permissions.administrator:
            await inter.send(admin_help, ephemeral=True)
        else:
            await inter.send(f'{inter.author.mention}. Этот раздел доступен только администраторам.')


# -------------НАЧАЛО БЛОКА АДМИН-МЕНЮ ПО УПРАВЛЕНИЮ ПОЛЬЗОВАТЕЛЯМИ--------------
@bot.slash_command()
@commands.has_permissions(administrator=True)
async def user(inter:disnake.ApplicationCommandInteraction):
    """
    User grouping command

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    """
    pass


@user.sub_command()
@commands.has_permissions(administrator=True)
async def add(inter, member: disnake.Member):
    """
    Adds the user to database | Добавляем пользователя в базу данных

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    member: Участник дискорд сервера
    """
    await inter.response.defer(ephemeral=True)
    async with pool.acquire() as db:
        try:
            await db.execute('INSERT INTO discord_users (id, nickname, join_date, gold, warns) VALUES($1, $2, $3);',
                             member.id, member.display_name, member.joined_at)
            await inter.edit_original_response('user added to database')
        except asyncpg.exceptions.UniqueViolationError:
            await inter.edit_original_response('user is already added')


@user.sub_command()
@commands.has_permissions(administrator=True)
async def delete(inter:disnake.ApplicationCommandInteraction, member: disnake.Member):
    """
    Delete the person from the bot database.

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    member: Участник дискорд сервера
    """
    async with pool.acquire() as db:
        await db.execute('DELETE FROM discord_users WHERE id=$1;', member.id)
        await db.execute('DELETE FROM LogTable WHERE user_id=$1;', member.id)


async def count_result_activity(activity_records_list, warns: int):
    """
    Counts the time of activeness in voice chats of a Member

    Parameters
    ----------
    activity_records_list: Набор записей из базы данных
    warns: Количество предупреждений юзера. Получается автоматически
    """
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
    result_minutes = int(result_activity.total_seconds() //60)

    # Теперь возвращает количество минут для более корректной сортировки в top и antitop
    return result_minutes


@user.sub_command()
@commands.has_permissions(administrator=True)
async def show(inter:disnake.ApplicationCommandInteraction, member: disnake.Member):
    """
    Shows the info about user | показываем данные пользователя

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    member: Чей профиль показать
    """
    global pool
    await inter.response.defer()
    async with pool.acquire() as db:
        data = await db.fetchrow(f'SELECT * FROM discord_users WHERE id=$1;', member.id)
        if data is not None:
            achievments = 0
            negative_achievements = 0
            warns = int(data['warns'])
            reputation = 0
            for role in member.roles:
                if 'ачивка' in role.name.lower():
                    achievments += 1
                    if role.color == disnake.Colour(int('ff4f4f', 16)):
                        negative_achievements += 1
                        reputation -= 5
                    elif role.color == disnake.Colour(int('920a0a', 16)):
                        negative_achievements += 1
                        reputation -= 10
                    elif role.color == disnake.Colour(int('873fff', 16)):
                        reputation += 10
                    else:
                        reputation += 2
            positive_achievements = achievments - negative_achievements
            t_7days_ago = datetime.datetime.now(tz=tz) - datetime.timedelta(days=7)
            t_30days_ago = datetime.datetime.now(tz=tz) - datetime.timedelta(days=30)

            try:
                seven_days_activity_records = await db.fetch(
                    "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login DESC;", t_7days_ago, datetime.datetime.now(tz=tz), member.id)
                thirty_days_activity_records = await db.fetch(
                    "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login DESC;", t_30days_ago, datetime.datetime.now(tz=tz), member.id)
            except asyncpg.InterfaceError:
                pool = await db_connection()

                # профиль картинкой
            activity7d = await count_result_activity(seven_days_activity_records, warns)
            activity30d = await count_result_activity(thirty_days_activity_records, warns)
            part_1 = f"ПОЛЬЗОВАТЕЛЬ:\nНикнейм: {member.display_name}\nБанковский счёт: {data['gold']} золота"
            part_2 = f"\nРЕПУТАЦИЯ:\nОчки престижа: {reputation}\nПозитивных ачивок: {positive_achievements}\nНегативных ачивок: {negative_achievements}"
            part_3 = f"\nАКТИВНОСТЬ:\nАктивность за 7 дней: {activity7d//60} ч. {activity7d%60} мин.\nАктивность за 30 дней: {activity30d//60} ч. {activity30d%60} мин."
            part_4 = f"\nПрочее:\nНа сервере с: {data['join_date']}"
            path = os.path.join('images', 'profile', data['profile_pic'])
            background = Image.open(path).convert('RGBA')
            background_img = background.copy()
            draw = ImageDraw.Draw(background_img)

            profile_text = part_1+'\n'+part_2+'\n'+part_3+'\n'+part_4   # текст профиля
            profile_font = ImageFont.truetype('Fonts/arialbd.ttf', encoding='UTF-8', size=22) # Шрифт текста профиля
            text_color = ast.literal_eval(data['profile_text_color'])
            #background_width, background_height = background_img.size
            #left, top, right, bottom = profile_font.getbbox(profile_text)
            #textbox = draw.multiline_textbbox((20,20),text=profile_text, font=profile_font)
            draw.text((50, 50), text=profile_text, fill=text_color, font=profile_font) # вписываем текст
            buffer = io.BytesIO()
            background_img.save(buffer, format='PNG')  # сохраняем в буфер обмена
            buffer.seek(0)
            await inter.edit_original_response(file=disnake.File(buffer, 'profile.png'))
            buffer.close()

        else:
            await inter.edit_original_response('Не найдена информация по вашему профилю.\n'
                           'Функция "Профиль", "Валюта" и "Репутация" доступна только игрокам с активностью в голосовых каналах.')


@user.sub_command()
@commands.has_permissions(administrator=True)
async def clear(inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
    """
    Reset user info to default values | Сбросить данные пользователя в базе

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction
    member: Участник дискорд сервера (ID, имя, упоминание)
    """
    await inter.response.defer(ephemeral=True)
    async with pool.acquire() as db:
        await db.execute('DELETE CASCADE FROM discord_users WHERE id=$1;', member.id)
        await db.execute('INSERT INTO discord_users (id, nickname, join_date, gold, warns) VALUES($1, $2, $3);',
                         member.id, member.display_name, member.joined_at)
    await inter.edit_original_response('Удаление участника из базы выполнено.')


# -------------КОНЕЦ БЛОКА АДМИН-МЕНЮ ПО УПРАВЛЕНИЮ ПОЛЬЗОВАТЕЛЯМИ--------------

@bot.slash_command(dm_permission=False)
async def gmoney(inter:disnake.ApplicationCommandInteraction, member: disnake.Member, gold:int):
    """
    Передать кому-то валюту | Give someone your coins

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction
    member: Участник сервера (айди, имя или упоминание)
    gold: Сколько денег дать
    """
    author = inter.author
    gold = abs(int(gold))
    await inter.response.defer()
    sys_channel = disnake.utils.find(lambda c: c.name.lower() == 'system', inter.guild.channels)
    async with pool.acquire() as db:
        if inter.author.guild_permissions.administrator:
            gold_was = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
            newgold = int(gold_was) + gold
            await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, member.id)
            await inter.edit_original_response(f'Пользователю {member.display_name} начислено +{gold} :coin:.')
        else:
            user_gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', author.id)
            if gold > int(user_gold):
                await inter.edit_original_response('У вас нет столько денег.')
                return
            else:
                newgold = int(user_gold) - gold
                await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, author.id)
                target_gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
                newtargetgold = int(target_gold) + gold
                await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newtargetgold, member.id)
                await inter.edit_original_response(f'Пользователь {inter.author.display_name} передал пользователю {member.display_name} {gold} валюты.')
                await sys_channel.send(
                    f'Пользователь {inter.author.display_name} передал пользователю {member.display_name} {gold} валюты.')


@commands.has_permissions(administrator=True)
@bot.slash_command(dm_permission=False)
async def mmoney(inter:disnake.ApplicationCommandInteraction, member: disnake.Member, gold:int):
    """
    Забираем у пользователя валюту | Take the money from a selected user.

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction
    member: Участник сервера (айди, имя или упоминание)
    gold: Сколько денег забрать
    """
    async with pool.acquire() as db:
        gold_was = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
        newgold = int(gold_was) - int(gold)
        if newgold < 0:
            newgold = 0
        await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, member.id)
        await inter.send(f'У Пользователя {member.mention} было отнято {gold} :coin:.', ephemeral=True)


@bot.slash_command(dm_permission=False)
@commands.has_permissions(administrator=True)
async def echo(inter:disnake.ApplicationCommandInteraction, text:str):
    """prints your message like a bot said it | Бот отправит сообщение от своего имени.

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction
    text: output message text
    """
    ch = inter.channel
    sys_channel = disnake.utils.find(lambda r: ('SYSTEM' in r.name.upper()), inter.guild.channels)
    await ch.send(text)
    await inter.send('👌', ephemeral=True)
    msg = str(inter.author.display_name) + ' using /echo sent: ' + text
    await sys_channel.send(msg)



@bot.slash_command(dm_permission=False)
async def me(inter:disnake.ApplicationCommandInteraction):
    """
    Command to see your profile generated by bot

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction
    """

    # При присоединении к голосовому каналу Если человека нет в базе данных - добавляем его и назначем роль
    global pool
    member = inter.author
    async with pool.acquire() as db:
        try:
            gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id}')
            roles_list = [role for role in member.guild.roles if role.id in (
            1486644163704262716, 653683016912338955, 742056254721228817, 688066382348419200, 742057453562101870,
            654005044815069186, 651377953271185409)]
            if not any(role in roles_list for role in member.roles):
                try:
                    for role_to_add in roles_list:
                        await member.add_roles(role_to_add)
                except Exception as e:
                    print(f'Возникла ошибка при назначении ролей профиля:/n{e.__str__()}')
            if type(gold) == 'NoneType' or gold is None:
                try:
                    await db.execute(
                        'INSERT INTO discord_users (id, nickname, join_date) VALUES($1, $2, $3);',
                        member.id, member.display_name, member.joined_at)
                    await sys_channel.send(f'Юзер добавлен в базу данных: {member.display_name}')
                except asyncpg.exceptions.UniqueViolationError:
                    await sys_channel.send(
                        f'Пользователь {member.display_name}, id: {member.id} уже есть в базе данных')
        except asyncpg.connection.exceptions.ConnectionRejectionError or asyncpg.connection.exceptions.ConnectionFailureError as err:
            print('Got error:', err, err.__traceback__)
            pool = await db_connection()
            await me(member)

    if "профиль" in inter.channel.name or "system" in inter.channel.name:
        await show(inter, member)
    else:
        await inter.send('Команда доступна только в специальном канале / Command is accessible only in predefined channel.', ephemeral=True)


# просмотр урезанного профиля пользователей для модерации
@bot.slash_command(dm_permission=False)
async def u(inter, member: disnake.Member):
    """
    shortened user profile show for moderators

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    member: Участник дискорд сервера (ID, имя, упоминание)
    """
    eligible_roles_ids = {651377975106732034, 449837752687656960}
    if any(role.id in eligible_roles_ids for role in inter.author.roles) or inter.author.guild_permissions.administrator is True:
        global pool
        await inter.response.defer()
        async with pool.acquire() as db:
            data = await db.fetchrow(f'SELECT * FROM discord_users WHERE id=$1;', member.id)
            if data is not None:
                warns = int(data['warns'])
                t_7days_ago = datetime.datetime.now(tz=tz) - datetime.timedelta(days=7)
                t_30days_ago = datetime.datetime.now(tz=tz) - datetime.timedelta(days=30)

                try:
                    seven_days_activity_records = await db.fetch(
                        "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login ASC;",
                        t_7days_ago, datetime.datetime.now(tz=tz), member.id)
                    thirty_days_activity_records = await db.fetch(
                        "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login ASC;",
                        t_30days_ago, datetime.datetime.now(tz=tz), member.id)
                except asyncpg.InterfaceError:
                    pool = await db_connection()
                time_in_clan = datetime.datetime.now(tz=tz) - member.joined_at
                reputation = 0
                for role in member.roles:
                    if 'ачивка' in role.name.lower():
                        if role.color == disnake.Colour(int('ff4f4f', 16)):
                            reputation -= 5
                        elif role.color == disnake.Colour(int('920a0a', 16)):
                            reputation -= 10
                        elif role.color == disnake.Colour(int('873fff', 16)):
                            reputation += 10
                        else:
                            reputation += 2

                part_1 = f"Никнейм: {member.mention}\n Банковский счёт: `{data['gold']}` :coin:\n Репутация: {reputation}"
                part_2 = f"`{time_in_clan.days//7} недель`"
                activity7d = await count_result_activity(seven_days_activity_records, warns)
                activity30d = await count_result_activity(thirty_days_activity_records, warns)
                part_3 = f"\nАктивность за 7 дней: {activity7d//60} ч. {activity7d%60} мин.\nАктивность за 30 дней: {activity30d//60} ч. {activity30d%60} мин.\nID: {member.id}"
                embed = disnake.Embed(color=disnake.Colour(int('efff00', 16)))
                embed.add_field(name=f"Пользователь:", value=part_1, inline=False)
                embed.add_field(name=f"Состоит в клане", value=part_2, inline=False)
                embed.add_field(name=f"Активность:", value=part_3, inline=False)
                await inter.send(embed=embed)
            else:
                await inter.edit_original_response(
                    'В базе пользователей не найдена информация по этому профилю. Чтобы информация появилась требуется активность в голосовых каналах')
    else:
        await inter.send('Вы не являетесь модератором или администратором.')


@bot.message_command(dm_permission=False, name='Лайк-дизлайк')
@commands.has_permissions(administrator=True)
async def likedis(inter:disnake.ApplicationCommandInteraction, msg:disnake.Message, polltime:int=60):
    """Отправляет сообщение и добавляет под него,👍 и 👎 чтобы провести голосование.

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    msg: Сообщение
    polltime: длительность в Минутах.
    """
    start_time = datetime.datetime.now(tz=tz).replace(microsecond=0)
    await inter.response.defer(ephemeral=True)
    await msg.add_reaction('👍')
    await msg.add_reaction('👎')
    end_time = start_time + datetime.timedelta(minutes=polltime)
    await inter.edit_original_response('done')
    await asyncio.sleep(60*polltime)
    msg = await inter.channel.fetch_message(msg.id)
    for reaction in msg.reactions:
        if str(reaction.emoji) == '👍':
            yes = reaction.count
        elif str(reaction.emoji) == '👎':
            no = reaction.count
        elif not yes or not no or yes == 0 or no == 0:
            await sys_channel.send(
                f'Опрос от {inter.author.display_name}, начатый в {start_time} выполнен с ошибками, отсутствует один из обязательных эмодзи - 👍 или 👎')
        else:
            pass
    if yes > no:
        await inter.channel.send(content=f'{inter.author.mention} опрос завершён, большинство проголосовало "За"')
        await sys_channel.send(content=f'Опрос от {inter.author.display_name}, начатый в {start_time} завершён, большинство проголосовало "За"')
    elif no > yes:
        await inter.channel.send(content=f'{inter.author.mention} опрос завершён, большинство проголосовало "Против"')
        await sys_channel.send(
            content=f'Опрос от {inter.author.display_name}, начатый в {start_time} завершён, большинство проголосовало "Против"')
    elif yes == no:
        await inter.channel.send(
            content=f'{inter.author.mention} участники голосования не смогли определиться с выбором')
        await sys_channel.send(
            content=f'Участники голосования от {inter.author.display_name}, начатого в {start_time} не смогли определиться с выбором')


@bot.slash_command(dm_permission=False)
async def poll(inter, options: int, time=60, arg=None):
    """
    Создаёт опрос / Makes a poll

    Parameters
    ----------
    inter: Context autofilled
    options: Количество вариантов
    time: Сколько минут длится опрос
    arg: напишите help, если хотите получить инструкцию по команде
    """
    await inter.response.defer(ephemeral=True)
    if arg=='help':
        return await inter.edit_original_response(
            '''Как использовать: команда пишется, сразу после сообщения, из которого хотите сделать \
            опрос (в нём заранее пропишите для людей опции голосования). Это сообщение, дублируется\
             и к нему назначаются реакции для голосования (до 9). Длительность по умолчанию - час.''')
    if options > 9:
        return await inter.edit_original_response(
            content=f"{inter.message.author.mention}, количество вариантов в голосовании должно быть не больше 9!")

    messages = await inter.channel.history(limit=2).flatten()
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    message = await inter.channel.fetch_message(messages[0].id)
    for num in range(options):
        await message.add_reaction(reactions[num])
    start_time = datetime.datetime.now(tz=tz)
    await inter.delete_original_response()
    await asyncio.sleep(60*time)
    message = await inter.channel.fetch_message(messages[0].id)
    reactions_count_list = []
    for reaction in message.reactions:
        reactions_count_list.append((str(reaction.emoji), reaction.count))
    sort_reactions = sorted(reactions_count_list, key=itemgetter(1), reverse=True)
    await inter.channel.send(
        content=f"{inter.message.author.mention}, опрос, стартовавший {start_time} завершён:\n ```{message.content}```\n Победил вариант № {sort_reactions[0][0]}")


@bot.slash_command(dm_permission=False)
async def top(inter, count: int = 10):
    """
    Displays top active players.

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    count: сколько позиций показать, по умолчанию = 10
    """

    await inter.response.defer(ephemeral=True)
    result_list = []
    users_count, users_ids = await initial_db_read()
    # checkrole = disnake.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), inter.guild.roles) # Clanmates only role
    t_30days_ago = datetime.datetime.now(tz=tz) - datetime.timedelta(days=30)
    async with pool.acquire() as db:
        async with inter.channel.typing():
            for member in inter.guild.members:
                if member.id in users_ids and not (member.id == member.guild.owner_id): # all people, not only Clanmates
                #if member.id in users_ids and checkrole in member.roles and not (member.id == member.guild.owner_id): #with Clanmates only clause
                    gold = await db.fetchval("SELECT gold from discord_users WHERE id=$1;", member.id)
                    if int(gold) > 0:
                        warns = await db.fetchval("SELECT warns from discord_users WHERE id=$1;", member.id)
                        thirty_days_activity_records = await db.fetch(
                            "SELECT login, logoff from LogTable WHERE user_id=$1 AND login BETWEEN $2::timestamptz AND $3::timestamptz ORDER BY login DESC;", member.id, t_30days_ago, datetime.datetime.now(tz=tz))
                        activity = await count_result_activity(thirty_days_activity_records, warns)
                        result_list.append((member.mention, activity))
    res = sorted(result_list, key=itemgetter(1), reverse=True)
    count = len(res) if count > len(res) else count
    output = "".join(f"{i + 1}: {res[i][0]}, актив: {res[i][1]//60} ч. {res[i][1] % 60} мин.;\n" for i in range(count))
    while len(output) > 1024:
        count -=1
        output = "".join(f"{i + 1}: {res[i][0]}, актив: {res[i][1]//60} ч. {res[i][1] % 60} мин.\n" for i in range(count))
    embed = disnake.Embed(color=disnake.Colour(int('efff00', 16)))
    embed.add_field(name='Топ активности', value=output)
    await inter.delete_original_response()
    await inter.send(embed=embed)


@bot.slash_command(dm_permission=False)
async def antitop(inter, count: int = 15):
    """
    Displays Least active players.

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    count: сколько позиций показывать, по умолчанию - 15
    """

    await inter.response.defer(ephemeral=True)
    result_list = []
    async with pool.acquire() as db:
        users_count, users_ids = await initial_db_read()
        #checkrole = disnake.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), inter.guild.roles)
        async with inter.channel.typing(): # анимация долгих вычислений в виде печатания
            for member in inter.guild.members:
                if member.id in users_ids and not (member.id == member.guild.owner_id): # # all people, not only Clanmates
                # if member.id in users_ids and checkrole in member.roles and not (member.id == member.guild.owner_id): #with Clanmates only clause
                    t_30days_ago = datetime.datetime.now(tz=tz) - datetime.timedelta(days=30)
                    warns = await db.fetchval("SELECT warns from discord_users WHERE id=$1;", member.id)
                    thirty_days_activity_records = await db.fetch(
                        "SELECT login, logoff from LogTable WHERE user_id=$1 AND login BETWEEN $2::timestamptz AND $3::timestamptz ORDER BY login DESC;", member.id, t_30days_ago, datetime.datetime.now(tz=tz))
                    activity = await count_result_activity(thirty_days_activity_records, warns)
                    time_in_clan = datetime.datetime.now(tz=tz) - member.joined_at
                    if time_in_clan.days//14 > 0:
                        if time_in_clan.days//7 <= 4:
                            if (activity//60)/(time_in_clan.days//7) < 10:
                                result_list.append((member.mention, activity, time_in_clan.days//7))
                        elif time_in_clan.days//7 >= 4 and activity//60 < 40:
                            result_list.append((member.mention, activity, '4+'))
    res = sorted(result_list, key=itemgetter(1), reverse=False)
    count = len(res) if count > len(res) else count
    output = "".join(f"{i + 1}: {res[i][0]}, актив: {res[i][1]//60} ч. {res[i][1] % 60} мин., В клане: {res[i][2]} нед.;\n" for i in range(count))
    embed = disnake.Embed(color=disnake.Colour(int('efff00', 16)))
    embed.add_field(name='АнтиТоп активности', value=output)
    await inter.delete_original_response()
    await inter.send(embed=embed)


@bot.slash_command(dm_permission=False)
@commands.has_permissions(administrator=True)
async def salary(inter:disnake.ApplicationCommandInteraction, amount: int = 1000):
    """
    Gives currency to moderation team with selected roles

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    amount: Сумма зарплаты, обычно 1000
    """
    salary_roles_ids = {651377975106732034, 449837752687656960}
    await inter.response.defer()
    async with pool.acquire() as db:
        got_salary = []
        for id in salary_roles_ids:
            role = disnake.utils.find(lambda r: (r.id == id), inter.guild.roles)
            for member in role.members:
                got_salary.append(member)
                gold_was = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
                newgold = int(gold_was) + amount
                await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, member.id)
    result = '\n'.join(_user.display_name for _user in got_salary)
    await inter.edit_original_response(f'Выдана зарплата: {amount} :coin: следующим Участникам:\n+{result}')


@bot.slash_command(dm_permission=False)
async def warn(inter, member: disnake.Member, count:int=1):
    """
    Command to warn activity rules violators

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    member: кому выдаём предупреждение
    count: сколько
    """
    await inter.response.defer(ephemeral=True)
    if member is not None:
        eligible_roles_ids = {651377975106732034, 449837752687656960}
        moderation_channel = bot.get_channel(1201486380497387530)
        chat_channel = bot.get_channel(442565510178013184)
        for role in inter.author.roles:
            if (role.id in eligible_roles_ids) or inter.author.guild_permissions.administrator:
                async with pool.acquire() as db:
                    user_warns = await db.fetchval('SELECT warns FROM discord_users WHERE id=$1', member.id)
                    if not isinstance(count, int):
                        try:
                            count = int(count)
                        except TypeError:
                            await member.guild.sys_channel.send(f'Ошибка при исполнении команды /warn для пользователя {member.display_name}, count={count}.\nНе удалось преобразовать количество предупреждений в число.')
                            print(f'Ошибка при исполнении команды /warn для пользователя {member.display_name}, count={count}.\nНе удалось преобразовать количество предупреждений в число.')
                            return
                    user_warns+=count
                    await db.execute('UPDATE discord_users SET warns=$1 WHERE id=$2', user_warns, member.id)
                await inter.delete_original_response()
                await moderation_channel.send(f'Модератор {inter.author.mention} ловит игрока {member.mention} на накрутке и отнимает у него время актива ({3*count} минут(ы).')
                return await chat_channel.send(f'Модератор {inter.author.mention} ловит игрока {member.mention} на накрутке и отнимает у него время актива.')
    else:
        await inter.edit_original_response('Вы указали несуществующего пользователя.')


# @message_command Это очень крутая штука, описанную функцию можно применить к любому сообщению, просто нажав
# ПКМ и выбрав, какую именно функцию к нему применить
@bot.message_command(dm_permission=False, name='Реакции')
async def react(inter, msg:disnake.Message, number:int=5):
    """
    Бот добавит реакции под указанное сообщение. ПКМ по сообщению -> Apps -> react.

    Parameters
    ----------
    inter: autofilled  argument
    msg: the message object
    number: сколько реакций поставить
    """
    await inter.response.defer(ephemeral=True)
    emoji_list = ['👍', '👀','😍','🎉','🥳','🤔','❤']
    for i in range(number):
        rnd = random.randint(0,len(emoji_list)-2)
        emoj = emoji_list.pop(rnd)
        await msg.add_reaction(emoj)
    await inter.delete_original_response()


@bot.slash_command(dm_permission=False)
async def roll(inter:disnake.ApplicationCommandInteraction, number:int=100):
    """
    Roll a dice. Бросьте кости.

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    number: от 1 и до этого числа
    """
    rnd = random.randint(1, number)
    await inter.send(f"{inter.author.display_name} rolled {rnd}")


# a command for setting up a pick a role message.
@bot.slash_command()
async def pickarole(inter:disnake.ApplicationCommandInteraction, num:int, text:str='Выберите свою роль под этим сообщением'):
    """
    Creates message with roles to select from

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    num: Количество добавляемых ролей на выбор
    text: Сообщение под которым будет выбор роли.
    """
    storage = {}
    messages_to_delete = []
    author = inter.author
    channel = inter.channel
    await inter.response.defer(ephemeral=True)
    def pickarole_check(msg:disnake.Message):
        """
        checks if the answering person is the one who entered the command

        Parameters
        ----------
        msg: message whose author to check
        """
        return msg.author == author and msg.channel == channel

    gid = inter.guild.id
    await inter.delete_original_response()
    #creating a new message with roles / создаём новое сообщение с ролями
    for i in range(num):
        temp_msg = await channel.send(f'Введите {i+1} подпись для роли / Enter the {i+1} role label')
        label = await bot.wait_for("message", check=pickarole_check, timeout=120)
        messages_to_delete.append(label)
        label = label.content
        storage[label] = 0
        messages_to_delete.append(temp_msg)
        temp_msg = await channel.send('Введите id роли, которую прикрепить к этой подписи / Enter the id of role matching this label')
        role_id = await bot.wait_for("message", check=pickarole_check, timeout=120)
        messages_to_delete.append(temp_msg)
        messages_to_delete.append(role_id)
        role_id = int(role_id.content)
        role = disnake.utils.find(lambda r: (role_id == r.id), inter.guild.roles)
        while role is None:
            temp_msg = await channel.send("There's no such role enter role id again/ Роль не найдена, введите id заново")
            role_id = await bot.wait_for("message", check=pickarole_check, timeout=120)
            messages_to_delete.append(role_id)
            role_id = int(role_id.content)
            role = disnake.utils.find(lambda r: (role_id == r.id), inter.guild.roles)
        storage[label] = role_id
    data_json = json.dumps(storage)

    # generate some id for the custom_id of component
    cid = 'roleMsg_'+''.join((map(str,(random.randint(0,9) for i in range(6)))))

    RoleList = disnake.ui.StringSelect(custom_id=cid)
    for lab, val in storage.items():
        RoleList.add_option(label=lab, value=str(val))

    await channel.send(content=text, components=RoleList)

    async with pool.acquire() as db:
        await db.execute('INSERT INTO PickaRole (guild_id, message_id, data) VALUES ($1, $2, $3)', gid, cid, data_json)

    final_msg = await channel.send('Success! Сообщение успешно создано.', delete_after=5)
    await channel.delete_messages(messages_to_delete)


@bot.slash_command(dm_permission=False)
async def giveaway(inter:disnake.ApplicationCommandInteraction, hours:float, winners:int, prize:str):
    """
    Организовать раздачу чего-то с выбором победителей из числа участников

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction
    hours: Длительность раздачи в часах
    winners: Количество победителей
    prize: Пpиз, что раздаём
    """
    await inter.response.defer(ephemeral=True)
    if hours is None or winners is None:
        return await inter.send('Для запуска розыгрыша введите /giveaway <кол-во часов> <кол-во победителей> <товар>.', ephemeral=True)
    author = inter.author
    hours = int(hours)
    winners_number = int(winners)
    channel = inter.channel
    participants_list = []
    embed = disnake.Embed(color=disnake.Colour.from_rgb(255,191,0))
    embed_text = f'\n**🎁 Награда:** "{prize}"\n🏆 **Количество победителей:** {winners_number},\n**⏰Время раздачи:** {hours} часов,\n**🕵️Раздает:** {author.mention}'
    embed.add_field(name='Внимание, новая раздача!', value=embed_text)

    @bot.event
    async def on_button_click(inter=disnake.MessageInteraction):
        """
        button click processor

        Parameters
        ----------
        inter: parameter is autofilled
        """
        if inter.component.custom_id == 'participate':
            if inter.author not in participants_list:
                if inter.author == author:
                    await inter.response.send_message('Автор не может участвовать в раздаче!', ephemeral=True)
                else:
                    participants_list.append(inter.author)
                    await inter.response.send_message('Теперь вы учавствуете в раздаче!', ephemeral=True)
            else:
                await inter.response.send_message('Вы уже участвуете в раздаче', ephemeral=True)

    view = Giveaway()
    await inter.send(embed=embed, view=view)
    await inter.delete_original_response()
    await asyncio.sleep(hours*3600)
    random.shuffle(participants_list)
    if winners_number > 1:
        i = winners_number
        winners = []
        for p in participants_list:
                winners.append(p)
                participants_list.remove(p)
                i-=1
                if len(participants_list) < i:
                    break
        win_emb = disnake.Embed(color=disnake.Colour.from_rgb(255,191,0))
        win_emb_fld = '\n'.join([winner.mention for winner in winners])
        win_emb.add_field(name='Победители:', value=win_emb_fld)
        await channel.send(f'{author.mention} розыгрыш "{prize}" завершён.', embed=win_emb)
    else:
        if len(participants_list) > 1:
            await channel.send(f'Розыгрыш "{prize}" от {author.mention} завершён. Победитель: {participants_list[0].mention}')
        else:
            await channel.send(f'В розыгрыше "{prize}" от {author.display_name} слишком мало участников, победителя нет. Ждем вас в следующих раздачах. 👋')


@bot.slash_command(dm_permission=False)
async def ticket(inter:disnake.ApplicationCommandInteraction, gold=False):
    """
    Покупка билета для розыгрыша

    Parameters
    ----------
    inter: parameter is autofilled
    """
    if gold is True:
        price = 1500
    else:
        price = 500

    await inter.response.defer(ephemeral=True)

    moderation_channel = bot.get_channel(696060547971547177)
    async with pool.acquire() as db:
        user_money = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1', inter.author.id)
        if user_money is None:
            return await inter.edit_original_response('Извините, эта возможность доступна только участникам клана с активностью в голосовых каналах.')
        if user_money < price:
            return await inter.edit_original_response('У вас недостаточно валюты для покупки')
        else:
            user_money -= price
            await db.execute('UPDATE discord_users set gold=$1 WHERE id=$2', user_money, inter.author.id)
            if gold is True:
                await inter.edit_original_response('Золотой билет успешно куплен')
                await moderation_channel.send(f'{inter.author.mention} купил золотой билет')
            else:
                await inter.edit_original_response('Билет успешно куплен')
                await moderation_channel.send(f'{inter.author.mention} купил билет')

@bot.slash_command(dm_permission=False)
async def goldticket(inter:disnake.ApplicationCommandInteraction):
    return await ticket(interaction=inter, gold=True)


@bot.slash_command(dm_permission=False)
@commands.has_permissions(administrator=True)
async def eraseachievements(inter:disnake.ApplicationCommandInteraction):
    await inter.response.defer(ephemeral=True)
    for member in inter.guild.members:
        _achievement_roles = []
        for achievement_role in member.roles:
            if 'ачивка' in achievement_role.name.lower():
                _achievement_roles.append(achievement_role)
        if len(_achievement_roles) > 0:
            await member.remove_roles(*_achievement_roles)


Sticker_options = commands.option_enum({'Add':'add', 'Delete':'delete'})
@bot.slash_command(dm_permission=False)
@commands.has_permissions(administrator=True)
async def sticker(inter:disnake.ApplicationCommandInteraction, option:Sticker_options):
    """add - создать закрепленное сообщение / delete - убрать закрепленное сообщение

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction parameter
    option: Add - создать закреп или delete - убрать закреп.
    """

    async def add(inter:disnake.ApplicationCommandInteraction):
        """add - создать закрепленное сообщение

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction parameter
        """
        channel = inter.channel

        await inter.response.send_modal(StickyNoteModal(title="Закрепление сообщения, как последнего в чате"))

        try:
            modal_inter = await bot.wait_for(
                "modal_submit",
                check=lambda i: i.author.id == inter.author.id,
                timeout=600)
        except asyncio.TimeoutError:
            return

        await modal_inter.response.defer(ephemeral=True)
        sticky_message = modal_inter.text_values["sticky_text"]
        async with pool.acquire() as db:
            try:
                await db.execute('INSERT INTO stickers (message, channel_id) VALUES($1, $2);', sticky_message, inter.channel_id)
            except Exception as e:
                if 'duplicate key value violates unique constraint "channel"' in e.__str__():
                    await inter.send("В канале может быть только одно закрепленное сообщение. Сначала удалите старое через /sticker delete", ephemeral=True)
                else:
                    await inter.send(f'Произошла ошибка:\n {e.__str__()}', ephemeral=True)
                return
        await channel.send(sticky_message)
        await inter.send('Сообщение успешно закреплено', ephemeral=True)

    async def delete(inter:disnake.ApplicationCommandInteraction):
        """убрать закрепленное сообщение

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction parameter
        """
        channel = inter.channel
        async with pool.acquire() as db:
            try:
                sticky_message = await db.fetchval(f'SELECT message FROM stickers WHERE channel_id={channel.id};')
                async for message in channel.history(limit=15):
                    if message.content == sticky_message:
                        await message.delete()
                        await db.execute(f'DELETE FROM stickers WHERE channel_id = {channel.id};')
                        await inter.send('Закрепленное сообщение успешно удалено', ephemeral=True)
            except Exception as e:
                await inter.send(f'Произошла ошибка:\n {e.__str__()}', ephemeral=True)
    # ---------------------------------------------------------------------------------------------------------
    if option == 'add':
        await add(inter=inter)
    elif option == 'delete':
        await delete(inter=inter)




#production bot
bot.run(token, reconnect=True)

