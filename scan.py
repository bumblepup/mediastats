import db
import argparse
import datetime
import ffprobe3
from pathlib import Path

# Create a partial MediaScan row
def startscan(dbase):
    ts = datetime.datetime.now()
    query = "INSERT INTO MediaScan (starttime) VALUES (?);"
    return dbase.send(query, ts)

# Complete the partial MediaScan row
def endscan(dbase, scanid, count):
    ts = datetime.datetime.now()
    query = "UPDATE MediaScan SET endtime=?, total=? WHERE rowid=?;"
    dbase.send(query, ts, count, scanid)

# Scan the given file with pathlib, and create a MediaFile row
def scanfile(dbase, libid, scanid, path):
    p = Path(path)
    stat = p.stat()
    try: btime = stat.st_birthtime
    except: btime = None
    query = "INSERT INTO MediaFile (libid, scanid, dirpath, fname,"
    query += " fmode, fsize, owneruid, ownergid, modified, created)"
    query += " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
    return dbase.send(query, libid, scanid, str(p.parent), p.name, stat.st_mode,
        stat.st_size, stat.st_uid, stat.st_gid, stat.st_mtime, btime)

# Scan the given file with ffprobe, and create a MediaStream row
def scanstream(fileid, path):
    probe = ffprobe3.probe(str(path))
    for stream in probe.streams:
        stype = 4
        width, height, pixfmt = None, None, None
        if stream.is_video():
            stype = 0
            width = stream.width
            height = stream.height
            pixfmt = stream.get("pix_fmt")
        elif stream.is_audio(): stype = 1
        elif stream.is_subtitle(): stype = 2
        elif stream.is_attachment(): stype = 3
        duration = stream.duration_secs
        codec = stream.codec_name
        if 'tags' in stream: lang = stream.get('tags').get('language')
        else: lang = None
        query = "INSERT INTO MediaStream (fileid, streamtype, framewidth,"
        query += " frameheight, duration, pixelfmt, streamlang, codec)"
        query += " VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
        with db.DB(db.dbfile) as dbase:
            dbase.send(query, fileid, stype, width, height, duration, pixfmt, lang, codec)

# Create a MediaStream row from a subtitle file
def scansub(fileid, path, lang):
    query = "INSERT INTO MediaStream (fileid, streamtype, streamlang)"
    query += " VALUES (?, 2, ?);"
    with db.DB(db.dbfile) as dbase:
        dbase.send(query, fileid, lang)

# Given a list of library names, get name/path pairs
def libpaths(dbase, libs):
    query = "SELECT rowid, libname, libpath FROM MediaLibrary;"
    libset = dbase.fetchall(query)
    if not libs: return libset
    return list(filter(lambda n: n[0] in libs, libset))

# Given a path, return:
# - True if the extension denotes a video file
# - A language string if the extension denotes a subtitle file
# - None otherwise
def checkext(path):
    if path.suffix in ['.webm', '.mkv', '.mp4', '.avi', '.mov', '.wmv']:
        return True
    elif path.suffix in ['.srt', '.sub', '.vtt', '.ass', '.ssa']:
        if len(path.suffixes) <= 1: return 'und'
        else: return path.suffixes[-2][1:]
    else: return None


# Parse args and run the scan
def main():
    progargs = {
        "prog": "scan.py",
        "description": "Scan libraries"
    }
    helpdoc = {
        "libraries": "The libraries to scan, or all if not specified"
    }
    parser = argparse.ArgumentParser(**progargs)
    parser.add_argument('libraries', help=helpdoc['libraries'], nargs='*')
    args = parser.parse_args()
    count = 0
    with db.DB(db.dbfile) as dbase:
        scanid = startscan(dbase)
        libs = libpaths(dbase, args.libraries)
    print(f"Scanning {len(libs)} total libraries")
    try:
        for (libid, name, path) in libs:
            print(f"Scanning library {name} at {path} ...")
            for f in Path(path).glob('**/*'):
                if not f.is_file(): continue
                lang = checkext(f)
                if lang == None: continue
                print(f"    Scanning file {f}")
                with db.DB(db.dbfile) as dbase:
                    fileid = scanfile(dbase, libid, scanid, f)
                if lang == True: scanstream(fileid, f)
                else: scansub(fileid, f, lang)
                count += 1
    finally:
        with db.DB(db.dbfile) as dbase:
            endscan(dbase, scanid, count)

if __name__ == '__main__':
    main()
