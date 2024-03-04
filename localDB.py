import sqlite3
import datetime

db = sqlite3.connect("eggs.db", check_same_thread=False)
create_table0 = '''CREATE TABLE IF NOT EXISTS counted (
   datetime NUMERIC,
   count INTEGER,
   sync INTEGER
);'''
rows = db.execute(create_table0)
cursor = db.cursor()

def count_one_day(date):
    # this function for the date
    cursor.execute(f"SELECT sum(count) FROM counted where date(datetime) == date('{date}')")
    rows = cursor.fetchall()
    return rows[0][0]


def count_today():
    # this function for the date
    cursor.execute(f"SELECT sum(count) FROM counted where date(datetime) == date('now')")
    rows = cursor.fetchall()
    return rows[0][0]

def insert(dt,N,status):
    # this function inserts one row to DB
    strDateTime = datetime.datetime.fromtimestamp(dt).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(f"INSERT INTO counted VALUES('{strDateTime}', {N}, {status})") 
    db.commit()

def full_table(dateFROM,dateTO):
    #returns all rows in table from [dateFrom] to [dateTO] 
    cursor.execute(f"SELECT * FROM counted where datetime > datetime('{dateFROM}') AND datetime < datetime('{dateTO}')")
    result = "sep=,\nDatetime, N, status\n"
    for row in cursor:
        result = result + f"{row[0]}, {row[1]}, {row[2]}\n"
    return result

def undelivered():
    #returns all undelivered rows in table 
    cursor.execute(f"SELECT unixepoch(datetime,'-3 hours'), count, sync  FROM counted where sync == 0")
    rows = cursor.fetchall()
    return rows

def updateStatus(datetime):
    query = f"Update counted  set sync = 1 where unixepoch(datetime, '-3 hours') == {datetime}"
    cursor.execute(query)
    db.commit()
