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
from Cog_utils import Games, Listeners, Shop
from buttons import Giveaway

# ds_logger = logging.getLogger('disnake')
# ds_logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename='disnake.log', encoding='utf-8', mode='w')
# ds_logger.addHandler(handler)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
token = os.getenv('bot_key')
if token is None:
    print('Could not receive token. Please check if your .env file has the correct token')
    exit(1)

prefix = '!'
intents = disnake.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
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
        _crown = False
        for guild in bot.guilds:
            if 'crown' in guild.name.lower():
                _crown = True
                current_members_list = []
                crown = guild
                global sys_channel
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
        try:
            role = disnake.utils.find(lambda r: ('РАДУЖНЫЙ НИК' in r.name.upper()), guild.roles)
            clr = random.choice(rgb_colors)
            if role is not None:
                await role.edit(color=disnake.Colour(int(clr, 16)))
        except disnake.NotFound:
            sys_channel.send('no role for rainbow nick found. See if you have the role with "радужный ник" in its name')
        except Exception as e:
            print(
                f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
            await sys_channel.send(
                f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
            await sys_channel.send(f'{e.__cause__}\n{e}')
            print(e.__cause__, e, sep='\n')


# функция сброса варнов у всех юзеров на 0 каждое первое число месяца (дописать очистку данных в LogTable старше 3 мес)
@tasks.loop(hours=24)
async def montly_task():

    # События в первый день месяца
    if datetime.datetime.now().day == 1:
        async with pool.acquire() as db:
            guild = bot.get_guild(198134036890255361)
            for user in guild.members:
                t_30days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                data = await db.fetchrow(f'SELECT * FROM discord_users WHERE id=$1;', user.id)
                if data is not None and data['warns'] is not None:
                    warns = int(data['warns'])
                    thirty_days_activity_records = await db.fetch(
                        "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login DESC;", t_30days_ago, datetime.datetime.now(), user.id)
                    hours, minutes = await count_result_activity(thirty_days_activity_records, warns)
                    time_in_clan = datetime.datetime.now() - user.joined_at
                    if minutes == 0 and time_in_clan.days//7 >= 8:
                        await db.execute('DELETE FROM LogTable CASCADE WHERE user_id=$1;', user.id)
                        await db.execute('DELETE FROM discord_users CASCADE WHERE id=$1;', user.id)
                        checkrole = disnake.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), guild.roles)
                        if checkrole in user.roles:
                            await user.remove_roles(checkrole)
                else:
                    await db.execute('DELETE FROM LogTable CASCADE WHERE user_id=$1;', user.id)
                    await db.execute('DELETE FROM discord_users CASCADE WHERE id=$1;', user.id)



    #События во второй день месяца
    if datetime.datetime.now().day == 2:

        #снятие варнов на 2 день месяца
        async with pool.acquire() as db:
            await db.execute('UPDATE discord_users SET warns=0;')

        # снятие ачивки "накрутчик" на 2 день месяца
        for user in bot.get_guild(198134036890255361).members:
            for role in user.roles:
                if role.name.lower() == 'накрутчик': await user.remove_role(role)

        #раздача зарплаты верховному совету на 2 день месяца
        for guild in bot.guilds:
            amount = 1000  # количество заработной платы
            salary_roles_ids = {651377975106732034, 449837752687656960} # ID ролей, которым начисляется зарплата
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
    while not (datetime.datetime.now().hour == 0 and datetime.datetime.now().minute == 0):
        await asyncio.sleep(10)
    else:
        global sys_channel
        #Проверяем не истёк ли срок каких-либо покупок из списка в Логе покупок
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

            # ПРОВЕРИТЬ КАК РАБОТАЕТ
                    #Если это скин профиля - меняем скин на дефолтный (если только не был куплен другой)
                    elif product['product_type'] == 'profile_skin':
                        current_profile_skin = await db.fetchval('SELECT profile_pic from discord_users WHERE id=$1', user.id)
                        json_data = json.loads(product['json_data'])
                        if current_profile_skin == json_data['image_name']:  #Если фон профиля не сменился
                            try:
                                await db.execute('UPDATE discord_users SET profile_pic=$1, profile_text_color=$2 WHERE id=$3', 'default_profile_pic.png', '(199,199,199,255)', user.id)
                                print('Вернул стандартный фон профиля пользователяю', user.display_name)
                            except Exception as e:
                                await sys_channel.send(f'{guild.owner.mention} Произошла ошибка при возвращении стандартного фона профиля для пользователя {user.mention}:')
                                await sys_channel.send(e)


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
        montly_task.start()
    except RuntimeError:
        montly_task.restart()
    daily_task.start()
    await accounting()
    print('I\'m ready to serve.')
    bot.add_cog(Games(bot, connection=pool))
    bot.add_cog(Listeners(bot, connection=pool))
    bot.add_cog(Shop(bot, connection=pool))




# -------------------- Функция ежедневного начисления клановой валюты  --------------------
@tasks.loop(minutes=1)
async def _increment_money(server: disnake.Guild):
    async with pool.acquire() as db:
        channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice']
        for member in server.members:
            if str(member.status) not in ['offline', 'idle'] and not member.bot and member.voice is not None:
                if any(item in member.voice.channel.name.lower() for item in channel_groups_to_account_contain) and not (member.voice.self_mute or member.voice.mute):
                    try:
                        gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
                        if gold is not None:
                            gold = int(gold) + 1
                            await db.execute(f'UPDATE discord_users SET gold=$1 WHERE id=$2;', gold, member.id)
                        else:
                            gold = 1
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

# -------------------- Конец функции ежедневного начисления клановой валюты --------------------

def subtract_time(time_arg):
    _tmp = time_arg.replace(microsecond=0) - datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0)
    ret = str(abs(_tmp)).replace('days', 'дней')
    return ret


@bot.command()
async def shutdown(ctx):
    async with pool.acquire() as db:
        sys_channel = disnake.utils.find(lambda r: (r.name.lower()=='system'), ctx.guild.channels)
        for member in ctx.guild.members:
            if member.voice is not None:
                gold = await db.fetchval(f'SELECT gold from discord_users WHERE id=$1;', member.id)
                await db.execute(
                    f"UPDATE LogTable SET logoff=NOW()::timestamptz(0), gold=$1 WHERE user_id=$2 AND logoff IS NULL;", int(gold), member.id)
                await member.move_to(None)
        clan_role = disnake.utils.find(lambda r: 'соклан' in r.name.lower(),ctx.guild.roles)
        chat_channel = disnake.utils.find(lambda r: ('чат-сервера' in r.name.lower()), ctx.guild.channels)
        await chat_channel.send(f'{clan_role.mention} вы были автоматически отключены от голосовых каналов в связи с перезапуском бота, чтобы у вас корректно учитывалась активность. Просим переподключиться, спасибо.')
        await asyncio.sleep(2)
        await sys_channel.send('Shutdown complete')
        exit(1)


@bot.command()
async def gchelp(ctx, arg:str=None):
    embed = disnake.Embed(color=disnake.Colour(int('efff00', 16)))
    basic_help = """    !me - посмотреть свой профиль\n
!top - посмотреть топ пользователей по активности\n
!antitop - посмотреть анти-топ пользователей по активности\n
!gmoney <имя_пользователя> <количество> или <id пользователя> <количество> - отдать кому-то свои деньги\n
!poll <кол-во опций> <длительность в минутах> - возможность сделать из сообщения опрос. Команда пишется, "ответом" на сообщение к которому хотите прикрепить опрос.
Сообщение, на которое вы отвечаете, дублируется и к нему в виде реакций назначаются опции для голосования (до 9 опций)\n
!chest - игра в сундучки (только в канале "сундучки")\n
!slots <ставка> - игра казино, где можно выиграть клановую валюту, или проиграть (только в канале казино) мин ставка = 50."""

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
    if arg==None:
        embed.add_field(name='Справка пользователя', value=basic_help)
        await ctx.send(embed=embed)
    elif arg=="mod":
        await ctx.send(mod_help)
    elif arg=="admin":
        if ctx.message.author.guild_permissions.administrator:
            await ctx.send(admin_help)
        else:
            await ctx.send('Этот раздел доступен только администраторам.')


# -------------НАЧАЛО БЛОКА АДМИН-МЕНЮ ПО УПРАВЛЕНИЮ ПОЛЬЗОВАТЕЛЯМИ--------------
@bot.group()
@commands.has_permissions(administrator=True)
async def user(ctx):
    """ "user" - меню-функция для админа - аргументы "add" "del" "show" "clear" """
    if ctx.message.author.guild_permissions.administrator:
        if ctx.invoked_subcommand is None:
            await ctx.send('You didn\'t specify any subcommand / Вы не указали, что делать с пользователем')
            await ctx.message.delete()
    else:
        await user.show(ctx, ctx.message.author)


@user.command()
@commands.has_permissions(administrator=True)
async def add(ctx, member: disnake.Member):
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
async def delete(ctx, member: disnake.Member):
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
    result_hours = int(result_activity.total_seconds()) // 3600
    result_minutes = (int(result_activity.total_seconds()) % 3600) // 60
    return result_hours, result_minutes


@user.command()
@commands.has_permissions(administrator=True)
async def show(ctx, member: disnake.Member):
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
                    if role.color == disnake.Colour(int('ff4f4f', 16)):
                        negative_achievements += 1
            positive_achievements = achievments - negative_achievements
            t_7days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
            t_30days_ago = datetime.datetime.now() - datetime.timedelta(days=30)

            try:
                seven_days_activity_records = await db.fetch(
                    "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login DESC;", t_7days_ago, datetime.datetime.now(), member.id)
                thirty_days_activity_records = await db.fetch(
                    "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login DESC;", t_30days_ago, datetime.datetime.now(), member.id)
                # db_messages = await db.fetch(
                #     "SELECT messages from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login ASC;",t_30days_ago, datetime.datetime.now(), member.id)
                # messages = 0
                # for msg_count in range(len(db_messages)):    ПЕРЕПИСАТЬ
                #     messages += int(msg_count)
            except asyncpg.InterfaceError:
                pool = await db_connection()

                # профиль картинкой
            hours7, minutes7 = await count_result_activity(seven_days_activity_records, warns)
            hours30, minutes30 = await count_result_activity(thirty_days_activity_records, warns)
            part_1 = f"ПОЛЬЗОВАТЕЛЬ:\nНикнейм: {member.display_name}\nБанковский счёт: {data['gold']} золота"
            part_2 = f"\nРЕПУТАЦИЯ:\nПозитивных ачивок: {positive_achievements}\nНегативных ачивок: {negative_achievements}"
            part_3 = f"\nАКТИВНОСТЬ:\nАктивность за 7 дней: {hours7} ч. {minutes7} мин.\nАктивность за 30 дней: {hours30} ч. {minutes30} мин."
            part_4 = f"\nПрочее:\nНа сервере с: {data['join_date']}"
            path = os.path.join('images', 'profile', data['profile_pic'])
            background = Image.open(path).convert('RGBA')
            background_img = background.copy()
            draw = ImageDraw.Draw(background_img)

            profile_text = part_1+'\n'+part_2+'\n'+part_3+'\n'+part_4   # текст профиля
            profile_font = ImageFont.truetype('Fonts/arialbd.ttf', encoding='UTF-8', size=22) # Шрифт текста профиля
            text_color = ast.literal_eval(data['profile_text_color'])
            background_width, background_height = background_img.size
            text_width, text_height = draw.textsize(profile_text, font=profile_font)
            x = (background_width-text_width)//2
            y = (background_height-text_height)//3
            draw.text((x,y), text=profile_text, fill=text_color, font=profile_font) # вписываем текст
            buffer = io.BytesIO()
            background_img.save(buffer, format='PNG')  # сохраняем в буфер обмена
            buffer.seek(0)
            await ctx.send(file=disnake.File(buffer, 'profile.png'))
            buffer.close()

        else:
            await ctx.send('Не найдена информация по вашему профилю.\n'
                           'Функция "Профиль", "Валюта" и "Репутация" доступна только игрокам с активностью в голосовых каналах.')


@user.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, member: disnake.Member):
    """Use this to clear the data about user to default and 0 values / Сбросить данные пользователя в базе"""
    await ctx.message.delete()
    async with pool.acquire() as db:
        await db.execute('DELETE CASCADE FROM discord_users WHERE id=$1;', member.id)
        await db.execute('INSERT INTO discord_users (id, nickname, join_date, gold, warns) VALUES($1, $2, $3);',
                         member.id, member.display_name, member.joined_at)
        # await db.execute('DELETE FROM LogTable WHERE user_id=$1;', member.id)


# -------------КОНЕЦ БЛОКА АДМИН-МЕНЮ ПО УПРАВЛЕНИЮ ПОЛЬЗОВАТЕЛЯМИ--------------

@bot.command()
async def gmoney(ctx, member: disnake.Member, gold):
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
async def mmoney(ctx, member: disnake.Member, gold):
    """This command takes the coins from selected user / Этой командой забираем у пользователя валюту."""
    await ctx.message.delete()
    async with pool.acquire() as db:
        gold_was = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
        newgold = int(gold_was) - int(gold)
        if newgold < 0:
            newgold = 0
        await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, member.id)
        await ctx.send(f'У Пользователя {member.mention} было отнято {gold} :coin:.')


@bot.command()
@commands.has_permissions(administrator=True)
async def echo(ctx, *args):
    """ prints your message like a bot said it / Бот пишет ваше сообщение так, будто это он сказал."""
    message = ''.join([arg+' ' for arg in args])
    await ctx.message.delete()
    await ctx.send(message)
    msg = str(ctx.message.author) + ' using !echo sent: ' + message
    await sys_channel.send(msg)


@bot.command()
async def me(ctx):
    """Command to see your profile / Этой командой можно увидеть ваш профиль"""
    if "клан-профиль" in ctx.channel.name or "system" in ctx.channel.name:
        usr = ctx.message.author
        await show(ctx, usr)
    else:
        msg = await ctx.send('Command is accessible only in predefined channel / Команда доступна только в специальном канале.')
        await asyncio.sleep(10)
        await msg.delete()


# просмотр урезанного профиля пользователей для модерации
@bot.command()
async def u(ctx, member: disnake.Member):
    eligible_roles_ids = {651377975106732034, 449837752687656960}
    await ctx.message.delete()
    #if any(role.id in eligible_roles_ids for role in ctx.author.roles) or ctx.message.author.guild_permissions.administrator is True:
    global pool
    async with pool.acquire() as db:
        data = await db.fetchrow(f'SELECT * FROM discord_users WHERE id=$1;', member.id)
        if data is not None:
            warns = int(data['warns'])
            t_7days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
            t_30days_ago = datetime.datetime.now() - datetime.timedelta(days=30)

            try:
                seven_days_activity_records = await db.fetch(
                    "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login ASC;",
                    t_7days_ago, datetime.datetime.now(), member.id)
                thirty_days_activity_records = await db.fetch(
                    "SELECT login, logoff from LogTable WHERE login BETWEEN $1::timestamptz AND $2::timestamptz AND user_id=$3 ORDER BY login ASC;",
                    t_30days_ago, datetime.datetime.now(), member.id)
            except asyncpg.InterfaceError:
                pool = await db_connection()
        time_in_clan = datetime.datetime.now() - member.joined_at

        part_1 = f"Никнейм: {member.mention}\n Банковский счёт: `{data['gold']}` :coin:"
        part_2 = f"`{time_in_clan.days//7} недель`"
        hours7d, minutes7d = await count_result_activity(seven_days_activity_records, warns)
        hours30d, minutes30d = await count_result_activity(thirty_days_activity_records, warns)
        part_3 = f"\nАктивность за 7 дней: {hours7d} час(ов) {minutes7d} минут\nАктивность за 30 дней: {hours30d} час(ов) {minutes30d} минут"
        embed = disnake.Embed(color=disnake.Colour(int('efff00', 16)))
        embed.add_field(name=f"Пользователь:", value=part_1, inline=False)
        embed.add_field(name=f"Состоит в клане", value=part_2, inline=False)
        embed.add_field(name=f"Активность:", value=part_3, inline=False)
        await ctx.send(embed=embed)
    #else:
        #await ctx.send('Вы не являетесь модератором или администратором.')


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
async def poll(ctx, options: int, time=60, arg=None):
    if arg=='help':
        await ctx.send(
            '''Как использовать: команда пишется, используя функцию "ответить" на сообщение из которого хотите сделать \
            опрос (в нём заранее пропишите для людей опции голосования). Сообщение, на которое вы отвечаете, дублируется\
             и к нему назначаются реакции для голосования (до 9). Базовая длительность - час.''')
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
    checkrole = disnake.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), ctx.guild.roles)
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
                    result_list.append((member.mention, activity[0], activity[1]))
    res = sorted(result_list, key=itemgetter(1), reverse=True)
    count = len(res) if count > len(res) else count
    output = "".join(f"{i + 1}: {res[i][0]}, актив: {res[i][1]} ч. {res[i][2]} мин.;\n" for i in range(count))
    while len(output) > 1024:
        count -=1
        output = "".join(f"{i + 1}: {res[i][0]}, актив: {res[i][1]} ч. {res[i][2]} мин.\n" for i in range(count))
    embed = disnake.Embed(color=disnake.Colour(int('efff00', 16)))
    embed.add_field(name='Топ активности', value=output)
    await ctx.send(embed=embed)


@bot.command()
async def antitop(ctx, count: int = 15):
    result_list = []
    await ctx.message.delete()
    async with pool.acquire() as db:
        users_count, users_ids = await initial_db_read()
        checkrole = disnake.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), ctx.guild.roles)
        for member in ctx.guild.members:
            if member.id in users_ids and checkrole in member.roles and not (member.id == member.guild.owner_id):
                t_30days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                warns = await db.fetchval("SELECT warns from discord_users WHERE id=$1;", member.id)
                thirty_days_activity_records = await db.fetch(
                    "SELECT login, logoff from LogTable WHERE user_id=$1 AND login BETWEEN $2::timestamptz AND $3::timestamptz ORDER BY login DESC;", member.id, t_30days_ago, datetime.datetime.now())
                activity = await count_result_activity(thirty_days_activity_records, warns)
                time_in_clan = datetime.datetime.now() - member.joined_at
                if time_in_clan.days//14 > 0:
                    if time_in_clan.days//7 <= 4:
                        if activity[0]/(time_in_clan.days//7) < 10:
                            result_list.append((member.mention, activity[0], activity[1], time_in_clan.days//7))
                    elif time_in_clan.days//7 >= 4 and activity[0] < 40:
                        result_list.append((member.mention, activity[0], activity[1], '4+'))
    res = sorted(result_list, key=itemgetter(1), reverse=False)
    count = len(res) if count > len(res) else count
    output = "".join(f"{i + 1}: {res[i][0]}, актив: {res[i][1]} ч. {res[i][2]} мин., В клане: {res[i][3]} нед.;\n" for i in range(count))
    embed = disnake.Embed(color=disnake.Colour(int('efff00', 16)))
    embed.add_field(name='АнтиТоп активности', value=output)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def salary(ctx, amount: int = 1000):
    await ctx.message.delete()
    salary_roles_ids = {651377975106732034, 449837752687656960}
    async with pool.acquire() as db:
        for id in salary_roles_ids:
            role = disnake.utils.find(lambda r: (r.id == id), ctx.guild.roles)
            for member in role.members:
                gold_was = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1;', member.id)
                newgold = int(gold_was) + amount
                await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2;', newgold, member.id)
                await ctx.send(f'Модератору {member.display_name} выдана зарплата: {amount} :coin:')


@bot.command()
async def warn(ctx, member: disnake.Member, count=1):
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


@bot.command()
async def react(ctx, number:int=5):
    msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    await ctx.message.delete()
    emoji_list = ['👍', '👀','😍','🎉','🥳','🤔','❤']
    for i in range(number):
        rnd = random.randint(0,len(emoji_list)-2)
        emoj = emoji_list.pop(rnd)
        await msg.add_reaction(emoj)


@bot.command()
async def roll(ctx, number:int=100):
    await ctx.message.delete()
    rnd = random.randint(1, number)
    await ctx.send(f"{ctx.message.author.display_name} rolled {rnd}")


# a command for setting up a pick a role message.
@bot.command()
async def pickarole(ctx):
    storage = {}
    messages_to_delete = []
    msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)

    def pickarole_check(msg:disnake.Message):
        return msg.author == ctx.author and msg.channel == ctx.channel

    gid = ctx.guild.id
    mid = msg.id

    #checking if the message already has roles associated with it / Проверяем, если сообщение уже имеет прикрепленные к нему роли
    async with pool.acquire() as db:
        data = await db.fetchval('SELECT data from PickaRole WHERE guild_id=$1, message_id=$2', gid, mid)
        storage = json.loads(data)
        if len(storage)>0:
            temp_msg = await ctx.send('Do you want to add more roles to this message? / Хотите добавить роли к этому сообщению?\nyes/no')
            answer = await bot.wait_for("message", check=pickarole_check, timeout=120)
            messages_to_delete.append(temp_msg)

            if answer.content.lower() == 'yes' or answer.content.lower().startswith('y'):
                temp_msg = await ctx.send('How many reaction-role pairs do you wish to add / Сколько пар реакция-роль хотите добавить?')
                messages_to_delete.append(temp_msg)
                num = await bot.wait_for("message", check=pickarole_check, timeout=120)
                try:
                    num = int(num.content)
                except ValueError:
                    temp_msg = await ctx.send('Error: you should send a digit / Ошибка: нужно отправить цифру')
                    messages_to_delete.append(temp_msg)
                for i in range(num):
                    temp_msg = await ctx.send(f'Enter the {i + 1} reaction emoji / Введите {i + 1} эмодзи реакции')
                    emoj = await bot.wait_for("message", check=pickarole_check, timeout=120)
                    messages_to_delete.append(emoj)
                    emoj = str(emoj.content)
                    storage[emoj] = 0
                    messages_to_delete.append(temp_msg)
                    temp_msg = await ctx.send('Enter the role id for this reaction / Введите id роли для этой реакции')
                    role_id = await bot.wait_for("message", check=pickarole_check, timeout=120)
                    messages_to_delete.append(temp_msg)
                    messages_to_delete.append(role_id)
                    role_id = int(role_id.content)
                    role = disnake.utils.find(lambda r: (role_id == r.id), ctx.guild.roles)
                    while role is None:
                        temp_msg = await ctx.send("There's no such role enter role id again/ Роль не найдена, введите id заново")
                        messages_to_delete.append(temp_msg)
                        role_id = await bot.wait_for("message", check=pickarole_check, timeout=120)
                        messages_to_delete.append(role_id)
                        role_id = int(role_id.content)
                        role = await disnake.utils.find(lambda r: (role_id == r.id), ctx.guild.roles)
                    await msg.add_reaction(emoji=emoj)
                    storage[emoj] = role_id
                data_json = json.dumps(storage)
                await db.execute('UPDATE PickaRole SET data=$1 WHERE guild_id=$2, message_id=$3', data_json, gid, mid,)

    #creating a new message with roles / создаём новое сообщение с ролями
    temp_msg = await ctx.send('How many reaction-role pairs do you wish to make / Сколько пар реакция-роль хотите создать?')
    messages_to_delete.append(temp_msg)
    num = await bot.wait_for("message", check=pickarole_check, timeout=120)
    num = int(num.content)
    for i in range(num):
        temp_msg = await ctx.send(f'Enter the {i+1} reaction emoji / Введите {i+1} эмодзи реакции')
        emoj = await bot.wait_for("message", check=pickarole_check, timeout=120)
        messages_to_delete.append(emoj)
        emoj = str(emoj.content)
        storage[emoj] = 0
        messages_to_delete.append(temp_msg)
        temp_msg = await ctx.send('Enter the role id for this reaction / Введите id роли для этой реакции')
        role_id = await bot.wait_for("message", check=pickarole_check, timeout=120)
        messages_to_delete.append(temp_msg)
        messages_to_delete.append(role_id)
        role_id = int(role_id.content)
        role = disnake.utils.find(lambda r: (role_id == r.id), ctx.guild.roles)
        while role is None:
            temp_msg = await ctx.send("There's no such role enter role id again/ Роль не найдена, введите id заново")
            role_id = await bot.wait_for("message", check=pickarole_check, timeout=120)
            messages_to_delete.append(role_id)
            role_id = int(role_id.content)
            role = await disnake.utils.find(lambda r: (role_id == r.id), ctx.guild.roles)
        storage[emoj] = role_id
    data_json = json.dumps(storage)

    async with pool.acquire() as db:
        await db.execute('INSERT INTO PickaRole (guild_id, message_id, data) VALUES ($1, $2, $3)', gid, mid, data_json)

    for emoji in storage.keys():
        await msg.add_reaction(emoji=emoji)

    final_msg = await ctx.send('Success!')
    await ctx.channel.delete_messages(messages_to_delete)
    await asyncio.sleep(5)
    await final_msg.delete()


@bot.command()
async def giveaway(ctx, hours=None, winners_number=None, *args):
    if hours is None or winners_number is None:
        await ctx.send('Для запуска розыгрыша введите !giveaway <кол-во часов> <кол-во победителей> <товар>.')
    author = ctx.message.author
    await ctx.message.delete()
    hours = int(hours)
    winners_number = int(winners_number)
    channel = ctx.message.channel
    messages_to_delete = []
    participants_list = []
    item = ''.join([arg+' ' for arg in args])
    embed = disnake.Embed(color=disnake.Color(0xefff00))
    embed.add_field(name='Новая раздача',
        value=f'Внимание, проводится раздача "**{item}**" от **{author.display_name}**\n**Победителей:** {winners_number},\n**Длительность:** {hours} часов.')

    async def on_button_click(inter=disnake.MessageInteraction):
        if inter.author not in participants_list:
            participants_list.append(inter.author)

    giveaway_message = await ctx.send(embed=embed, view=Giveaway)
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
        await channel.send(f'{author.mention} розыгрыш "{item}" завершён. Победители: {[winner.mention for winner in winners]}')
    else:
        if len(participants_list) > 1:
            await channel.send(f'Розыгрыш "{item}" от {author.mention} завершён. Победитель: {participants_list[0].mention}')
        else:
            await channel.send(f'В розыгрыше "{item}" от {author.display_name} недостаточно участников. Победителя нет.')


bot.run(token, reconnect=True)
