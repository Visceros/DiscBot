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
        pool = await asyncpg.create_pool(host=db_address, port=5000, user=db_user, password=db_pwd, database=db_name)
        db = await pool.acquire()
    except Exception as e:
        print('Could not connect to database:\n', e.args)
        print(e)
        print('exiting...')
        exit(1)
    print('connection successful!')
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
        print('Attempt to create database tables failed')
        print(e, e.args, e.__cause__, e.__context__)
        exit(1)
    return pool
