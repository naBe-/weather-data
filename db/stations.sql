DROP TABLE IF EXISTS stations;
DROP TABLE IF EXISTS windy_observations;

CREATE TABLE stations (
	station INTEGER PRIMARY KEY AUTOINCREMENT,
	key TEXT NOT NULL,
	name TEXT,
	lat REAL,
	lon REAL,
	elevation INTEGER,
	tempheight INTEGER,
	windheight INTEGER
);

CREATE TABLE windy_observations (
	station INTEGER,
	dateutc TEXT,
	temp REAL,
	dewpoint REAL, 
	windspeedmph INTEGER,
	winddir INTEGER, 
	windgustmph INTEGER,
        rh INTEGER
	uv INTEGER,
	rainin INTEGER,
	baromin INTEGER,
	FOREIGN KEY(station) REFERENCES stations(station)
);

