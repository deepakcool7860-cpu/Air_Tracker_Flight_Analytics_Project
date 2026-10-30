-- ====================================================================
-- Project: Air Tracker: Flight Analytics (AeroDataBox API & SQL)
-- Description: Complete SQL schema DDL and 11 Evaluation SQL Queries
-- ====================================================================

-- -----------------------------------------------------
-- TABLE DDL SCHEMA
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS airport (
    airport_id INTEGER PRIMARY KEY AUTOINCREMENT,
    icao_code TEXT UNIQUE,
    iata_code TEXT UNIQUE,
    name TEXT,
    city TEXT,
    country TEXT,
    continent TEXT,
    latitude REAL,
    longitude REAL,
    timezone TEXT
);

CREATE TABLE IF NOT EXISTS aircraft (
    aircraft_id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration TEXT UNIQUE,
    model TEXT,
    manufacturer TEXT,
    icao_type_code TEXT,
    owner TEXT
);

CREATE TABLE IF NOT EXISTS flights (
    flight_id TEXT PRIMARY KEY,
    flight_number TEXT,
    aircraft_registration TEXT,
    origin_iata TEXT,
    destination_iata TEXT,
    scheduled_departure TEXT,
    actual_departure TEXT,
    scheduled_arrival TEXT,
    actual_arrival TEXT,
    status TEXT,
    airline_code TEXT,
    FOREIGN KEY (aircraft_registration) REFERENCES aircraft(registration),
    FOREIGN KEY (origin_iata) REFERENCES airport(iata_code),
    FOREIGN KEY (destination_iata) REFERENCES airport(iata_code)
);

CREATE TABLE IF NOT EXISTS airport_delays (
    delay_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_iata TEXT,
    delay_date TEXT,
    total_flights INTEGER,
    delayed_flights INTEGER,
    delay_index INTEGER,
    median_delay_min INTEGER,
    canceled_flights INTEGER,
    FOREIGN KEY (airport_iata) REFERENCES airport(iata_code)
);

-- =====================================================
-- 11 EVALUATION SQL QUERIES
-- =====================================================

-- Query 1: Show the total number of flights for each aircraft model, listing the model and its count.
SELECT 
    a.model, 
    COUNT(f.flight_id) AS total_flights
FROM aircraft a
JOIN flights f ON a.registration = f.aircraft_registration
GROUP BY a.model
ORDER BY total_flights DESC;

-- Query 2: List all aircraft (registration, model) that have been assigned to more than 5 flights.
SELECT 
    a.registration, 
    a.model, 
    COUNT(f.flight_id) AS flight_count
FROM aircraft a
JOIN flights f ON a.registration = f.aircraft_registration
GROUP BY a.registration, a.model
HAVING COUNT(f.flight_id) > 5
ORDER BY flight_count DESC;

-- Query 3: For each airport, display its name and the number of outbound flights, but only for airports with more than 5 flights.
SELECT 
    ap.name, 
    COUNT(f.flight_id) AS outbound_flights
FROM airport ap
JOIN flights f ON ap.iata_code = f.origin_iata
GROUP BY ap.airport_id, ap.name
HAVING COUNT(f.flight_id) > 5
ORDER BY outbound_flights DESC;

-- Query 4: Find the top 3 destination airports (name, city) by number of arriving flights, sorted by count descending.
SELECT 
    ap.name, 
    ap.city, 
    COUNT(f.flight_id) AS arriving_flights
FROM airport ap
JOIN flights f ON ap.iata_code = f.destination_iata
GROUP BY ap.airport_id, ap.name, ap.city
ORDER BY arriving_flights DESC
LIMIT 3;

-- Query 5: Show for each flight: number, origin, destination, and a label 'Domestic' or 'International' using CASE WHEN on country match.
SELECT 
    f.flight_number,
    f.origin_iata,
    f.destination_iata,
    orig.country AS origin_country,
    dest.country AS destination_country,
    CASE 
        WHEN orig.country = dest.country THEN 'Domestic'
        ELSE 'International'
    END AS flight_type
FROM flights f
JOIN airport orig ON f.origin_iata = orig.iata_code
JOIN airport dest ON f.destination_iata = dest.iata_code
ORDER BY f.flight_number;

-- Query 6: Show the 5 most recent arrivals at “DEL” airport including flight number, aircraft, departure airport name, and arrival time, ordered by latest arrival.
SELECT 
    f.flight_number,
    a.model AS aircraft_model,
    orig.name AS departure_airport_name,
    f.scheduled_arrival AS arrival_time
FROM flights f
JOIN aircraft a ON f.aircraft_registration = a.registration
JOIN airport orig ON f.origin_iata = orig.iata_code
WHERE f.destination_iata = 'DEL'
ORDER BY f.scheduled_arrival DESC
LIMIT 5;

-- Query 7: Find all airports with no arriving flights (never used as a destination in flights table).
SELECT 
    ap.iata_code, 
    ap.name, 
    ap.city, 
    ap.country
FROM airport ap
LEFT JOIN flights f ON ap.iata_code = f.destination_iata
WHERE f.flight_id IS NULL;

-- Query 8: For each airline, count the number of flights by status (e.g., 'On Time', 'Delayed', 'Cancelled') using CASE WHEN.
SELECT 
    airline_code,
    COUNT(CASE WHEN status = 'On Time' THEN 1 END) AS on_time_count,
    COUNT(CASE WHEN status = 'Delayed' THEN 1 END) AS delayed_count,
    COUNT(CASE WHEN status = 'Cancelled' THEN 1 END) AS cancelled_count,
    COUNT(*) AS total_flights
FROM flights
GROUP BY airline_code
ORDER BY total_flights DESC;

-- Query 9: Show all cancelled flights, with aircraft and both airports, ordered by departure time descending.
SELECT 
    f.flight_number,
    f.scheduled_departure,
    a.model AS aircraft_model,
    orig.name AS origin_airport,
    dest.name AS destination_airport
FROM flights f
JOIN aircraft a ON f.aircraft_registration = a.registration
JOIN airport orig ON f.origin_iata = orig.iata_code
JOIN airport dest ON f.destination_iata = dest.iata_code
WHERE f.status = 'Cancelled'
ORDER BY f.scheduled_departure DESC;

-- Query 10: List all city pairs (origin-destination) that have more than 2 different aircraft models operating flights between them.
SELECT 
    orig.city AS origin_city,
    dest.city AS destination_city,
    COUNT(DISTINCT a.model) AS unique_aircraft_models
FROM flights f
JOIN airport orig ON f.origin_iata = orig.iata_code
JOIN airport dest ON f.destination_iata = dest.iata_code
JOIN aircraft a ON f.aircraft_registration = a.registration
GROUP BY orig.city, dest.city
HAVING COUNT(DISTINCT a.model) > 2;

-- Query 11: For each destination airport, compute the % of delayed flights (status='Delayed') among all arrivals, sorted by highest percentage.
SELECT 
    ap.name AS destination_airport,
    COUNT(f.flight_id) AS total_arrivals,
    COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) AS delayed_arrivals,
    ROUND(COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) * 100.0 / COUNT(f.flight_id), 2) AS delayed_percentage
FROM airport ap
JOIN flights f ON ap.iata_code = f.destination_iata
GROUP BY ap.airport_id, ap.name
ORDER BY delayed_percentage DESC;
