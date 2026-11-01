CREATE TABLE IF NOT EXISTS Version (
    rev INTEGER PRIMARY KEY NOT NULL
);

INSERT INTO Version (rev) VALUES (1);

CREATE TABLE IF NOT EXISTS MediaLibrary (
    libname TEXT UNIQUE NOT NULL,
    libpath TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS MediaScan (
    starttime TEXT UNIQUE NOT NULL,
    endtime   TEXT,
    total     INTEGER
);

CREATE TABLE IF NOT EXISTS MediaFile (
    libid    INTEGER NOT NULL,
    scanid   INTEGER NOT NULL,
    dirpath  TEXT    NOT NULL,
    fname    TEXT    NOT NULL,
    fmode    TEXT    NOT NULL,
    fsize    INTEGER NOT NULL,
    owneruid INTEGER NOT NULL,
    ownergid INTEGER NOT NULL,
    modified TEXT    NOT NULL,
    created  TEXT
);

-- Stream Types:
-- 0: Video
-- 1: Audio
-- 2: Subtitle
-- 3: Attachment

CREATE TABLE IF NOT EXISTS MediaStream (
    fileid      INTEGER NOT NULL,
    streamtype  INTEGER NOT NULL,
    framewidth  INTEGER,
    frameheight INTEGER,
    duration    INTEGER,
    pixelfmt    TEXT,
    streamlang  TEXT,
    codec       TEXT
);