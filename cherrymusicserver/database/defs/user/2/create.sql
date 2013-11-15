
CREATE TABLE users(
    _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    _created INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _modified INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    _deleted INTEGER DEFAULT 0,
    username TEXT UNIQUE,	-- implies index
    admin INTEGER,
    realname TEXT,
    avatar_url TEXT,
    public_url TEXT,
    points INTEGER DEFAULT 0,
    password TEXT,
    salt TEXT
);
