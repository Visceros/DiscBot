import os
import asyncpg


async def db_connection():
    """Returns a connection pool object using asyncpg.create_pool() method"""
    global pool
    db_user = os.getenv('db_user')
    db_pwd = os.getenv('db_pwd')
    db_name = os.getenv('db_name')
    db_address = os.getenv('db_address')  # reserved variable for database http address
    try:
        print('connecting to database server...')
        pool = await asyncpg.create_pool(min_size=20, max_size=30, host=db_address, port=5000, user=db_user, password=db_pwd, database=db_name)
    except Exception as e:
        print('Could not connect to database:\n', e.args)
        print(e)
        print('exiting...')
        exit(1)
    print('connection successful!')
    async with pool.acquire() as db:
        try:
            await db.execute('''CREATE TABLE IF NOT EXISTS discord_users (
                Id BIGINT PRIMARY KEY NOT NULL UNIQUE,
                Nickname varchar(255) NOT NULL UNIQUE,
                Join_date Date,
                Gold INT DEFAULT 0,
                Warns INT DEFAULT 0,
                HeadSymbol varchar(255) DEFAULT '⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜',
                RowSymbol varchar(32) DEFAULT '⬜',
                FootSymbol varchar(255) DEFAULT '⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜',
                CONSTRAINT users_unique UNIQUE (Id, Nickname));''')
            print('Table of users created or connection established...')

            # Таблица для слежения за активностью пользователей
            await db.execute('''CREATE TABLE IF NOT EXISTS LogTable (
            user_id BIGINT NOT NULL,
            login timestamp with time zone,
            logoff timestamp with time zone,
            gold INT DEFAULT 0,
            record_id SERIAL PRIMARY KEY NOT NULL,
            Messages INT DEFAULT 0,
            CONSTRAINT user_id_fkey FOREIGN KEY (user_id) REFERENCES discord_users (Id));''')
            print('Log Table online...')

            #Таблица с товарами в магазине
            await db.execute('''CREATE TABLE IF NOT EXISTS Shop (
            product_id SERIAL PRIMARY KEY NOT NULL,
            name text NOT NULL,
            price INT NOT NULL,
            duration INT DEFAULT NULL,
            CONSTRAINT unique_id UNIQUE (product_id));''')

            await db.execute('''CREATE TABLE IF NOT EXISTS ShopLog (
            record_id SERIAL PRIMARY KEY NOT NULL,
            product_id int NOT NULL,
            buyer_id BIGINT NOT NULL,
            item_name text,
            buyer_name text,
            purchase_date timestamp with time zone,
            CONSTRAINT customer_id FOREIGN KEY (buyer_id) REFERENCES discord_users (Id),
            CONSTRAINT item_id FOREIGN KEY (product_id) REFERENCES Shop (product_id)
            );''')
            print('Shop is working.')
        except Exception as e:
            print('Attempt to create database tables failed')
            print(e, e.args, e.__cause__, e.__context__)
            exit(1)
    return pool
