"""
Database configuration and SQLite schema management for Air Tracker: Flight Analytics.
Implements the 4 required tables: airport, aircraft, flights, airport_delays.
"""

import sqlite3
import pandas as pd
from typing import Optional

DB_NAME = "air_tracker.db"

def get_connection(db_path: str = DB_NAME) -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str = DB_NAME):
    """Initializes the database schema according to the project specification."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Airport Table
    cursor.execute("""
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
    """)

    # 2. Aircraft Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aircraft (
        aircraft_id INTEGER PRIMARY KEY AUTOINCREMENT,
        registration TEXT UNIQUE,
        model TEXT,
        manufacturer TEXT,
        icao_type_code TEXT,
        owner TEXT
    );
    """)

    # 3. Flights Table
    cursor.execute("""
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
    """)

    # 4. Airport Delays Table
    cursor.execute("""
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
    """)

    # Create indexes for optimized analytical queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_flights_origin ON flights(origin_iata);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_flights_dest ON flights(destination_iata);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_flights_status ON flights(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_flights_aircraft ON flights(aircraft_registration);")

    conn.commit()
    conn.close()
    print(f"Database {db_path} schema initialized successfully.")

def run_query(query: str, params: tuple = (), db_path: str = DB_NAME) -> pd.DataFrame:
    """Executes a SQL query and returns results as a pandas DataFrame."""
    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)

if __name__ == "__main__":
    init_db()
