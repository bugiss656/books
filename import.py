import psycopg2
from psycopg2.extras import execute_batch
import csv


def csv_to_db():

    with open('books.csv', newline = '') as f:
        filereader = csv.reader(f)
        data = [tuple(row) for row in filereader]

    try:
        conn = psycopg2.connect(
            dbname = 'djhp6mrfhj0rf',
            user = 'yelenexdhudlbm',
            password = '9405ea1d7bfa3771b5b076ef2c670a2d814f89d96d4a491273e76e44e7e68998',
            host = 'ec2-54-217-235-87.eu-west-1.compute.amazonaws.com',
            port = '5432'
        )

        cur = conn.cursor()

        sql_query = """INSERT INTO books(isbn, title, author, year)
                       VALUES (%s, %s, %s, %s)"""

        execute_batch(cur, sql_query, data)
        conn.commit()
        print("Table created successfully...")

    except(Exception, psycopg2.Error) as error:
        print("Error has occured: ", error)
    finally:
        if(conn):
            cur.close()
            conn.close()
            print("Connection closed")

    return data

csv_to_db()
