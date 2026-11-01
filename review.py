import db
import argparse

def idscan(scantime):
    with db.DB(db.dbfile) as dbase:
        if scantime == None:
            query = "SELECT rowid FROM MediaScan ORDER BY starttime DESC;"
            return dbase.fetchone(query)[0]
        else:
            query = "SELECT rowid FROM MediaScan WHERE starttime=?;"
            return dbase.fetchone(query, scantime)[0]

def calccompression(scanid):
    mb = 1024 * 1024
    query = "SELECT COUNT(c), MIN(sz), AVG(sz), MAX(sz), MIN(dr), AVG(dr),"
    query += " MAX(dr), MIN(c), AVG(c), MAX(c) FROM ("
    query += " SELECT f.fsize AS sz, MAX(s.duration) AS dr,"
    query += " f.fsize / (MAX(s.duration)"
    query += " * MAX(s.framewidth) * MAX(s.frameheight)) AS c"
    query += " FROM MediaFile AS f LEFT JOIN MediaStream AS s"
    query += " ON f.rowid = s.fileid WHERE f.scanid = ? GROUP BY f.rowid)"
    query += " GROUP BY FLOOR(c * 10) ORDER BY c ASC;"
    with db.DB(db.dbfile) as dbase:
        for chunk in dbase.fetchgen(query, scanid):
            for line in chunk:
                ct, mnsz, avsz, mxsz, mndr, avdr, mxdr, mnc, avc, mxc = line
                if not ct: continue
                col1 = f"{ct:>4}: "
                col2 = f"[{mnsz/mb:07.2f} < {avsz/mb:07.2f} < {mxsz/mb:07.2f}]"
                col3 = f"({mndr/60:06.2f} < {avdr/60:06.2f} < {mxdr/60:06.2f})"
                col4 = '{' + f"{mnc*100:06.2f} < {avc*100:06.2f} < {mxc*100:06.2f}" + '}'
                print(f"{col1}  {col2}  {col3}  {col4}")

def main():
    progargs = {
        "prog": "review.py",
        "description": "Print a review of a scan"
    }
    helpdoc = {
        "scantime": "The timestamp of the scan to review. If none is provded, review the most recent scan"
    }
    parser = argparse.ArgumentParser(**progargs)
    parser.add_argument('scantime', help=helpdoc['scantime'], nargs='?')
    args = parser.parse_args()
    scanid = idscan(args.scantime)
    calccompression(scanid)

if __name__ == '__main__':
    main()