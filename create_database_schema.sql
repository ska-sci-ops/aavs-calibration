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
    x_gains REAL[],
    y_gains REAL[],
    PRIMARY KEY (fit_time, create_time, ant_id)
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
