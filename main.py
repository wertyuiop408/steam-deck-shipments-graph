import argparse
import csv
import datetime as dt
import requests
import sqlite3
import time

import matplotlib.pyplot as plt
import matplotlib.dates as md
import numpy as np


class main:
    cur = None
    def __init__(self):
        self.con = sqlite3.connect("deck.db")
        self.cur = self.con.cursor()

        self.sql_tables()
        self.get_sheet()
        self.parse_sheet()
        self.graph()


    def get_sheet(self) -> None:
        print("getting sheet")
        csv_url="https://docs.google.com/spreadsheets/d/1QqlSUpqhyBCBYeu_gW4w5vIxfcd7qablSviALDFJ0Dg/export?format=csv"
        res=requests.get(url=csv_url)
        open("google.csv", 'wb').write(res.content)
        return

    def parse_sheet(self) -> None:
        print("parsing sheet")
        
        with open("google.csv", newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            stmt = """INSERT OR IGNORE INTO form (
            "timestamp", region, model, rtReserveTime, initial_estimate, recent_estimate, ready_email
            ) VALUES (?, ?, ?, ?, ?, ?, ?)"""
            next(reader, None)  # skip the headers
            newData = [self.format_row(row) for row in reader]
            

            self.cur.execute("BEGIN")
            ins = self.cur.executemany(stmt, newData).rowcount
            self.cur.execute("COMMIT")
            print(f"{ins} rows inserted")
            

    def graph(self):
        now_time = int(dt.datetime.today().timestamp())
        deck_prerelease = int(time.mktime(dt.datetime(2021, 7, 15).timetuple()))
        day3 = int(time.mktime(dt.datetime(2021, 7, 17).timetuple()))

        self.cur.execute("""SELECT rtReserveTime, ready_email FROM form 
            WHERE model = 512 
            AND region = 'US'
            AND ready_email > ?  AND ready_email < ? 
            AND rtReserveTime < ?
            """, [deck_prerelease, now_time, day3])
        res = self.cur.fetchall()

        #y axis
        y_email = [dt.datetime.fromtimestamp(t[1]) for t in res]

        #x axis
        x_reserve = [dt.datetime.fromtimestamp(t[0]) for t in res]
        xvals = [1,2,2,4,5]
        yvals = [10,20,30, 40, 50]


        fig, ax = plt.subplots()

        ax.set_xlabel("Reserve time")
        ax.set_ylabel("Order email received")

        ax.scatter(x_reserve, y_email, 50)
        fig.savefig("mygraph.png")
        #plt.plot(res)

        """
        reserve = [dt.datetime.fromtimestamp(t[0]) for t in res]
        email = [dt.datetime.fromtimestamp(t[1]) for t in res]
        print(len(reserve), len(email))
        s = 10**2.
        plt.scatter(reserve, email, s)
        #plt.plot(reserve[0], email[0], "ro")
        plt.ylabel("order email received")
        plt.xlabel("Reserve time")
        #plt.show()

        plt.savefig("mygraph.png")
        """
        return


    def format_row(self, data):
        return (
            data[0],
            data[1],
            0 if data[2] == "" else int(data[2]),
            0 if data[3] == "" else int(data[3]),
            data[4],
            data[5],
            0 if data[6] == "" else int(data[6])
        )


    def sql_tables(self):
        self.cur.execute("BEGIN")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS "form" (
            row_id INTEGER PRIMARY KEY,
            timestamp TEXT,
            region TEXT,
            model INTEGER,
            rtReserveTime INTEGER,
            initial_estimate TEXT,
            recent_estimate TEXT,
            ready_email INTEGER,
            UNIQUE("timestamp", region, model, rtReserveTime, initial_estimate, recent_estimate, ready_email)
            )""")
        self.cur.execute("COMMIT")
     
if __name__ == "__main__":
    main()