import argparse
import csv
import datetime as dt
import requests
import sqlite3
import time

import matplotlib.pyplot as plt
import matplotlib.dates as md
import matplotlib as mpl


class main:
    cur = None

    def __init__(self):
        parser = argparse.ArgumentParser(allow_abbrev=False)
        parser.add_argument("--update", action="store_true")

        # matplotlibrc figure.dpi default is 'figure' which is 100
        parser.add_argument("--dpi", default=100, type=int)
        parser.add_argument("--stats", action="store_true")
        parser.add_argument("models", nargs="*", default=["UK-512", "US-512"])
        parser.add_argument("--outfile", default="graph.png")
        self.args = parser.parse_args()
        
        # convert models to uppercase
        self.args.models = list(map(str.upper, self.args.models))
        self.con = sqlite3.connect("deck.db")
        self.cur = self.con.cursor()
        self.sql_tables()

        if self.args.update:
            self.get_sheet()
            self.parse_sheet()

        self.graph()

        if self.args.stats:
            self.stats()


    def get_sheet(self) -> None:
        """
        Downloads the Google Sheet as a csv file
        """
        csv_url = "https://docs.google.com/spreadsheets/d/1QqlSUpqhyBCBYeu_gW4w5vIxfcd7qablSviALDFJ0Dg/export?format=csv"
        res = requests.get(url = csv_url)
        open("google.csv", "wb").write(res.content)
        return None


    def stats(self) -> None:
        """
        Prints a breakdown of region/model entries in the database
        """

        self.cur.execute("SELECT count(*) FROM form")
        print(f"total entries: {self.cur.fetchone()[0]}")

        self.cur.execute("SELECT region, model, count(*) FROM form GROUP BY region, model")
        for row in self.cur.fetchall():
            print(f"{row[0]}-{row[1]} entries: {row[2]}")
        return None


    def parse_sheet(self) -> None:
        """
        Read the CSV file and insert any new entries into the database
        """
        
        with open("google.csv", newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            stmt = """INSERT OR IGNORE INTO form (
                "timestamp", region, model, rtReserveTime, initial_estimate, recent_estimate, ready_email
            ) VALUES (?, ?, ?, ?, ?, ?, ?)"""

            # skip the headers
            next(reader, None)

            newData = [self.format_row(row) for row in reader]
            
            self.cur.execute("BEGIN")
            ins = self.cur.executemany(stmt, newData).rowcount
            self.cur.execute("COMMIT")
            print(f"{ins} rows inserted")

            return None


    def graph_query(self, region: str = "US", model: int = 512) -> tuple:
        
        now_time = int(dt.datetime.today().timestamp())

        #the date the the steam deck was on sale (reserve)
        deck_prerelease = int(time.mktime(dt.datetime(2021, 7, 15).timetuple()))

        #only get info for orders within the first 2 days. Otherwise it's info overload and 512 orders get heavily squished.
        day3 = int(time.mktime(dt.datetime(2021, 7, 17).timetuple()))

        self.cur.execute("""SELECT rtReserveTime, ready_email FROM form 
            WHERE model = ? 
            AND region = ?
            AND ready_email > ?  AND ready_email < ? 
            AND rtReserveTime < ?
            """, [model, region, deck_prerelease, now_time, day3])
        res = self.cur.fetchall()

        #y axis
        y_email = [dt.datetime.fromtimestamp(t[1]) for t in res]

        #x axis
        x_reserve = [dt.datetime.fromtimestamp(t[0]) for t in res]
        return (x_reserve, y_email)


    def graph(self) -> None:
        """
        Use the data from the database to plot a scatter graph and save it as a png file.
        """

        fig, ax = plt.subplots()
        #plt.subplots_adjust(bottom=0.15)

        ax.set_xlabel("Reserve time")
        plt.xticks(rotation=45)
        ax.set_ylabel("Order email received")


        if "ALL" in self.args.models:
            self.args.models = [
                "EU-512",
                "EU-256",
                "EU-64",
                "UK-512",
                "UK-256",
                "UK-64",
                "US-512",
                "US-256",
                "US-64"
            ]

        for deck in self.args.models:
            region, model = deck.split("-")
            x, y = self.graph_query(region, model)
            ax.scatter(x, y, 10, label=deck)
            
        ax.legend()
        fig.savefig(self.args.outfile, bbox_inches="tight", dpi=self.args.dpi)
        return None


    def format_row(self, data) -> tuple:
        """
        Formats the 3, 4, and 7th column into ints.
        """
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
        """
        Create the SQL table
        """
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