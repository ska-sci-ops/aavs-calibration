CREATE TABLE calibration_fit
(
     fit_time TIMESTAMP WITH TIME ZONE NOT NULL UNIQUE,
     create_time TIMESTAMP WITH TIME ZONE NOT NULL UNIQUE,
     creator text,
     code_version text,
     PRIMARY KEY(fit_time,create_time)
);

CREATE TABLE calibration_solution
(
    fit_time TIMESTAMP WITH TIME ZONE NOT NULL references calibration_fit(fit_time),
    create_time TIMESTAMP WITH TIME ZONE NOT NULL references calibration_fit(create_time),
    ant_id  INTEGER NOT NULL,
    station_id INTEGER NOT NULL,
    x_gains REAL[],
    y_gains REAL[],
    x_gains_fit REAL[],
    y_gains_fit REAL[],
    x_pha REAL[],
    y_pha REAL[],
    x_delay REAL,
    y_delay REAL,
    x_phase0 REAL,
    y_phase0 REAL
    PRIMARY KEY (fit_time, create_time, ant_id, station_id)
);

CREATE UNIQUE INDEX fit_create_time
ON calibration_fit(create_time);

CREATE UNIQUE INDEX fit_fit_time
ON calibration_fit(fit_time);

CREATE INDEX solution_fit_time
ON calibration_solution(fit_time);

CREATE INDEX solution_create_time
ON calibration_solution(create_time);

CREATE INDEX solution_ant_id
ON calibration_solution(ant_id);

# MS 2023-03-20 : apparently name of the column changed from x_amp -> x_gains and eda2/aavs1 database uses names x_amp and x_amp_fit etc.
# ALTER TABLE calibration_solution ADD COLUMN x_amp_fit REAL[];
# ALTER TABLE calibration_solution ADD COLUMN y_amp_fit REAL[];

