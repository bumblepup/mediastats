import sqlite3
import argparse
from pathlib import Path

dbfile = "mediastats.db"

class DB:
    def __init__(self, path, chunksize=10):
        self.path = path
        self.chunksize = chunksize

    # Open a connection to the database in a `with` statement
    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        self._makeupdatetabs()
        return self
    
    # Commit and close the connection automatically, rollback on error
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type == None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()
        self.conn = None

    # Initialize or update tables
    def _makeupdatetabs(self):
        rev = 0
        parent = Path(__file__).parent
        cursor = self.conn.cursor()
        # Check the version table
        # # "ask permission" version, use this if the other doesn't work
        # cursor.execute('SELECT 1 from sqlite_master WHERE type="table" AND name="Version";')
        # if cursor.fetchone():
        #     cursor.execute('SELECT rev FROM Version;')
        #     fromrev = cursor.fetchone() or 0
        try:
            cursor.execute('SELECT rev FROM Version ORDER BY rev DESC;')
            rev = cursor.fetchone()[0] or 0
        except: pass
        # Upgrade the database by running all new versions sequentially
        while True:
            rev += 1
            path = Path(parent, "schema", f"rev{rev}.sql")
            if not path.exists():
                break
            with open(path) as f:
                cursor.executescript(f.read())

    # Send an update query to the database
    def send(self, query, *args):
        cursor = self.conn.cursor()
        cursor.execute(query, args)
        return cursor.lastrowid
    
    # Send an update query to the database many times with different values
    def sendmany(self, query, *args):
        self.conn.cursor().executemany(query, args)

    # Send a fetch query to the database, and return first result
    def fetchone(self, query, *args):
        cursor = self.conn.cursor()
        cursor.execute(query, args)
        return cursor.fetchone()

    # Send a fetch query to the database, and return some results
    def fetchmany(self, query, *args, count=None):
        cursor = self.conn.cursor()
        cursor.arraysize = count or self.chunksize
        cursor.execute(query, args)
        return cursor.fetchmany(count)

    # Send a fetch query to the database, and return all results
    def fetchall(self, query, *args, chunksize=None):
        cursor = self.conn.cursor()
        cursor.arraysize = chunksize or self.chunksize
        cursor.execute(query, args)
        return cursor.fetchall()

    # Send a fetch query to the database, and return a results generator
    def fetchgen(self, query, *args, chunksize=None):
        cursor = self.conn.cursor()
        cursor.arraysize = chunksize or self.chunksize
        cursor.execute(query, args)
        while True:
            chunk = cursor.fetchmany(chunksize or self.chunksize)
            if chunk: yield chunk
            else: return

# Commandline wrapper to send queries to the db
def send(args):
    with DB(dbfile) as db:
        rowid = db.send(args.query)
        if rowid: print(f"Inserted row id: {rowid}")

# Commandline wrapper to fetch results from the db
def fetch(args):
    with DB(dbfile) as db:
        match args.limit:
            case 1: fmtrows([db.fetchone(args.query)])
            case None: fmtrows(db.fetchall(args.query))
            case _: fmtrows(db.fetchmany(args.query, count=args.limit))

# Commandline wrapper to list, create, and move libraries
def library(args):
    with DB(dbfile) as db:
        if not args.name:
            # Return a list of libraries
            query = "SELECT * FROM MediaLibrary ORDER BY libname;"
            match args.limit:
                case 1: fmtrows([db.fetchone(query)])
                case None: fmtrows(db.fetchall(query))
                case _: fmtrows(db.fetchmany(query, count=args.limit))
        elif args.delete:
            # Delete the library from the database
            query = "DELETE FROM MediaLibrary WHERE libname=?;"
            db.send(query, args.name)
        elif args.path:
            # Create or update the library
            query = "INSERT INTO MediaLibrary (libname, libpath)"
            query += " VALUES (?, ?) ON CONFLICT(libname) DO"
            query += " UPDATE SET libpath=?;"
            db.send(query, args.name, args.path, args.path)
        else:
            # Display the selected library
            query = "SELECT * FROM MediaLibrary WHERE libname=?;"
            fmtrows([db.fetchone(query, args.name)])

# Format the database output and display it
def fmtrows(rows):
    if not rows or rows == [None]: rows = []
    print(f'{len(rows)} results retrieved:')
    for row in rows:
        if row:
            row = list(map(lambda v: 'NULL' if v is None else v, row))
            print(('{:<15}'*len(row)).format(*row))

# Parse args and run the correct command
def main():
    progargs = {
        "prog": "db.py",
        "description": "Basic database access and management"
    }
    sendargs = {
        "prog": "db.py send",
        "description": "Send a query to update the database"
    }
    fetchargs = {
        "prog": "db.py fetch",
        "description": "Send a query to fetch from the database"
    }
    libargs = {
        "prog": "db.py library",
        "description": "Manage the list of libraries"
    }
    helpdoc = {
        "name": "The library name",
        "path": "The library path",
        "delete": "Delete the library",
        "query": "The query to execute",
        "limit": "The number of results to fetch"
    }
    parser = argparse.ArgumentParser(**progargs)
    subparsers = parser.add_subparsers()
    sendcmd = subparsers.add_parser('send', **sendargs)
    fetchcmd = subparsers.add_parser('fetch', **fetchargs)
    libcmd = subparsers.add_parser('library', **libargs)
    sendcmd.add_argument('query', help=helpdoc['query'])
    sendcmd.set_defaults(func=send)
    fetchcmd.add_argument('query', help=helpdoc['query'])
    fetchcmd.add_argument('-l', '--limit', help=helpdoc['limit'])
    fetchcmd.set_defaults(func=fetch)
    libcmd.add_argument('name', help=helpdoc['name'], nargs='?')
    libcmd.add_argument('-p','--path', help=helpdoc['path'])
    libcmd.add_argument('-d','--delete', help=helpdoc['delete'], action='store_true')
    libcmd.add_argument('-l', '--limit', help=helpdoc['limit'], type=int)
    libcmd.set_defaults(func=library)
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_usage()

if __name__ == '__main__':
    main()
