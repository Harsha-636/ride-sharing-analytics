-- Schema only — CREATE DATABASE/USE removed since Supabase and Neon
-- give you an already-created database; their SQL editor runs
-- statements against it directly.

DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS drivers;
DROP TABLE IF EXISTS riders;

CREATE TABLE riders (
    rider_id     INT PRIMARY KEY,
    rider_name   VARCHAR(100),
    city         VARCHAR(50),
    signup_date  DATE
);

CREATE TABLE drivers (
    driver_id     INT PRIMARY KEY,
    driver_name   VARCHAR(100),
    vehicle_type  VARCHAR(30),
    city          VARCHAR(50),
    joining_date  DATE
);

CREATE TABLE trips (
    trip_id          INT PRIMARY KEY,
    rider_id         INT,
    driver_id        INT,
    trip_date        TIMESTAMP,
    pickup_location  VARCHAR(100),
    drop_location    VARCHAR(100),
    distance_km      DECIMAL(6,2),
    fare             DECIMAL(10,2),
    trip_status      VARCHAR(20),   -- Completed / Cancelled
    payment_method   VARCHAR(20),   -- UPI / Card / Cash
    FOREIGN KEY (rider_id)  REFERENCES riders(rider_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
);

-- Indexes worth having once you're on a real database (and a good
-- interview talking point: "why these three?")
CREATE INDEX idx_trips_trip_date ON trips(trip_date);
CREATE INDEX idx_trips_rider_id ON trips(rider_id);
CREATE INDEX idx_trips_driver_id ON trips(driver_id);
