"""
Air Tracker: Flight Analytics - Interactive Streamlit Web Application
Features:
- Homepage Dashboard with Key Metrics & Charts
- Live Search & Multi-criteria Filtering
- Airport Details & Terminal Viewer
- Delay & Performance Analytics (Statistical table)
- Route Leaderboards & Congestion Maps
- Interactive SQL Query Runner executing all 11 evaluation queries with one click!
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database import run_query

st.set_page_config(
    page_title="Air Tracker: Flight Analytics",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header & Branding
st.markdown("""
<div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 22px; border-radius: 12px; color: white; margin-bottom: 25px;">
    <h1 style="margin: 0; color: white; font-family: sans-serif;">✈️ Air Tracker: Flight Analytics</h1>
    <p style="margin: 5px 0 0 0; opacity: 0.85; font-size: 1.05rem;">AeroDataBox API Aviation Intelligence, SQL Relational Analytics & Operational Dashboards</p>
</div>
""", unsafe_allow_html=True)

# Navigation Menu
menu = st.sidebar.radio(
    "Navigation",
    ["🏠 Executive Dashboard", "🔍 Search & Filter Flights", "🏢 Airport Explorer", "⏱️ Delay & Congestion Analytics", "🏆 Route Leaderboards", "💻 11 Evaluation SQL Queries"]
)

# Sidebar Quick Metrics
st.sidebar.markdown("---")
st.sidebar.subheader("📌 System Status")
stats_df = run_query("""
    SELECT 
        (SELECT COUNT(*) FROM airport) AS total_airports,
        (SELECT COUNT(*) FROM aircraft) AS total_aircraft,
        (SELECT COUNT(*) FROM flights) AS total_flights,
        (SELECT ROUND(AVG(delayed_flights * 100.0 / total_flights), 1) FROM airport_delays) AS avg_delay_rate
""")
if not stats_df.empty:
    st.sidebar.info(f"""
    • **Airports:** {stats_df.iloc[0]['total_airports']}  
    • **Aircraft:** {stats_df.iloc[0]['total_aircraft']}  
    • **Flights Tracked:** {stats_df.iloc[0]['total_flights']}  
    • **System Delay Avg:** {stats_df.iloc[0]['avg_delay_rate']}%
    """)

# ========================================================
# 1. EXECUTIVE DASHBOARD
# ========================================================
if menu == "🏠 Executive Dashboard":
    st.header("Global Operational Overview")
    
    # 4 Key Metrics Cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        total_apt = run_query("SELECT COUNT(*) AS c FROM airport")['c'][0]
        st.metric("Total Airports", total_apt, delta="Global Hubs")
    with kpi_col2:
        total_flt = run_query("SELECT COUNT(*) AS c FROM flights")['c'][0]
        st.metric("Flights Ingested", total_flt, delta="Active Movements")
    with kpi_col3:
        delayed_flt = run_query("SELECT COUNT(*) AS c FROM flights WHERE status = 'Delayed'")['c'][0]
        st.metric("Delayed Operations", delayed_flt, delta="Impacted Flights", delta_color="inverse")
    with kpi_col4:
        avg_delay = run_query("SELECT ROUND(AVG(median_delay_min), 1) AS m FROM airport_delays")['m'][0]
        st.metric("Avg Hub Delay", f"{avg_delay} mins", delta="Median Ground Time", delta_color="inverse")

    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Flight Status Distribution")
        status_df = run_query("SELECT status, COUNT(*) AS count FROM flights GROUP BY status")
        fig_pie = px.pie(
            status_df, 
            names="status", 
            values="count", 
            hole=0.45,
            color="status",
            color_discrete_map={"On Time": "#2ecc71", "Delayed": "#e67e22", "Cancelled": "#e74c3c"}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("Aircraft Fleet Utilization by Model")
        fleet_df = run_query("""
            SELECT a.model, COUNT(f.flight_id) AS flights_flown
            FROM aircraft a
            JOIN flights f ON a.registration = f.aircraft_registration
            GROUP BY a.model
            ORDER BY flights_flown DESC
        """)
        fig_bar = px.bar(
            fleet_df,
            x="model",
            y="flights_flown",
            color="flights_flown",
            color_continuous_scale="Viridis",
            labels={"flights_flown": "Total Flights", "model": "Aircraft Model"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ========================================================
# 2. SEARCH & FILTER FLIGHTS
# ========================================================
elif menu == "🔍 Search & Filter Flights":
    st.header("Flight Search & Filter Engine")
    
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        airline_list = ["All"] + run_query("SELECT DISTINCT airline_code FROM flights")['airline_code'].tolist()
        sel_airline = st.selectbox("Filter Airline Code", airline_list)
    with fcol2:
        status_list = ["All", "On Time", "Delayed", "Cancelled"]
        sel_status = st.selectbox("Filter Flight Status", status_list)
    with fcol3:
        search_kw = st.text_input("Search Flight # (e.g., 6E, AI, EK)", "")

    # Query generation
    where_parts = []
    params = []
    if sel_airline != "All":
        where_parts.append("f.airline_code = ?")
        params.append(sel_airline)
    if sel_status != "All":
        where_parts.append("f.status = ?")
        params.append(sel_status)
    if search_kw:
        where_parts.append("f.flight_number LIKE ?")
        params.append(f"%{search_kw}%")

    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    query = f"""
        SELECT 
            f.flight_number AS [Flight No],
            f.airline_code AS [Airline],
            f.origin_iata AS [Origin],
            orig.city AS [Origin City],
            f.destination_iata AS [Dest],
            dest.city AS [Dest City],
            f.scheduled_departure AS [Sched Departure],
            f.scheduled_arrival AS [Sched Arrival],
            f.status AS [Status],
            a.model AS [Aircraft Model],
            f.aircraft_registration AS [Registration]
        FROM flights f
        JOIN airport orig ON f.origin_iata = orig.iata_code
        JOIN airport dest ON f.destination_iata = dest.iata_code
        JOIN aircraft a ON f.aircraft_registration = a.registration
        {where_sql}
        ORDER BY f.scheduled_departure DESC
    """
    results_df = run_query(query, tuple(params))
    st.markdown(f"**Found {len(results_df)} flight records matching criteria**")
    st.dataframe(results_df, use_container_width=True)

# ========================================================
# 3. AIRPORT EXPLORER
# ========================================================
elif menu == "🏢 Airport Explorer":
    st.header("Airport Network & Details Explorer")
    
    airports = run_query("SELECT iata_code || ' - ' || name AS label, iata_code FROM airport ORDER BY name")
    selected_option = st.selectbox("Select Airport to Inspect", airports["label"].tolist())
    selected_iata = selected_option.split(" - ")[0]
    
    # Airport Info Card
    apt_info = run_query("SELECT * FROM airport WHERE iata_code = ?", (selected_iata,)).iloc[0]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("IATA / ICAO", f"{apt_info['iata_code']} / {apt_info['icao_code']}")
    c2.metric("City, Country", f"{apt_info['city']}, {apt_info['country']}")
    c3.metric("Timezone", apt_info['timezone'])
    c4.metric("Coordinates", f"{apt_info['latitude']:.2f}°N, {apt_info['longitude']:.2f}°E")

    st.markdown("---")
    
    # Associated flights
    subcol1, subcol2 = st.columns(2)
    with subcol1:
        st.subheader("Departures (Outbound Flights)")
        dep_df = run_query("""
            SELECT flight_number, destination_iata, scheduled_departure, status 
            FROM flights WHERE origin_iata = ? ORDER BY scheduled_departure DESC
        """, (selected_iata,))
        st.dataframe(dep_df, use_container_width=True)
        
    with subcol2:
        st.subheader("Arrivals (Inbound Flights)")
        arr_df = run_query("""
            SELECT flight_number, origin_iata, scheduled_arrival, status 
            FROM flights WHERE destination_iata = ? ORDER BY scheduled_arrival DESC
        """, (selected_iata,))
        st.dataframe(arr_df, use_container_width=True)

# ========================================================
# 4. DELAY & PERFORMANCE ANALYTICS
# ========================================================
elif menu == "⏱️ Delay & Congestion Analytics":
    st.header("Airport Delay & Congestion Intelligence")
    
    delay_df = run_query("""
        SELECT 
            ad.airport_iata,
            ap.name AS airport_name,
            ap.city,
            ad.total_flights,
            ad.delayed_flights,
            ROUND(ad.delayed_flights * 100.0 / ad.total_flights, 1) AS delay_pct,
            ad.median_delay_min,
            ad.canceled_flights
        FROM airport_delays ad
        JOIN airport ap ON ad.airport_iata = ap.iata_code
        ORDER BY delay_pct DESC
    """)
    
    st.subheader("Delay Index & On-Time Performance by Hub")
    fig_delay = px.bar(
        delay_df,
        x="airport_iata",
        y="delay_pct",
        color="median_delay_min",
        color_continuous_scale="Reds",
        labels={"delay_pct": "Delayed Flights (%)", "airport_iata": "Airport IATA", "median_delay_min": "Median Delay (min)"},
        title="Airport Delay Rate (%) and Median Delay Minutes"
    )
    st.plotly_chart(fig_delay, use_container_width=True)
    
    st.subheader("Detailed Statistical Delay Table")
    st.dataframe(delay_df, use_container_width=True)

# ========================================================
# 5. ROUTE LEADERBOARDS
# ========================================================
elif menu == "🏆 Route Leaderboards":
    st.header("Aviation Network Leaderboards")
    
    l_col1, l_col2 = st.columns(2)
    
    with l_col1:
        st.subheader("🔥 Busiest Routes (Most Flights)")
        busiest_df = run_query("""
            SELECT 
                orig.city || ' (' || f.origin_iata || ') ➔ ' || dest.city || ' (' || f.destination_iata || ')' AS route,
                COUNT(f.flight_id) AS flight_volume
            FROM flights f
            JOIN airport orig ON f.origin_iata = orig.iata_code
            JOIN airport dest ON f.destination_iata = dest.iata_code
            GROUP BY f.origin_iata, f.destination_iata
            ORDER BY flight_volume DESC
            LIMIT 10
        """)
        fig_routes = px.bar(busiest_df, x="flight_volume", y="route", orientation="h", color="flight_volume")
        fig_routes.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_routes, use_container_width=True)
        
    with l_col2:
        st.subheader("⚠️ Most Delayed Destination Airports")
        delayed_dest_df = run_query("""
            SELECT 
                ap.name AS airport,
                COUNT(f.flight_id) AS total_arrivals,
                COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) AS delayed_arrivals,
                ROUND(COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) * 100.0 / COUNT(f.flight_id), 1) AS delay_pct
            FROM airport ap
            JOIN flights f ON ap.iata_code = f.destination_iata
            GROUP BY ap.airport_id, ap.name
            HAVING total_arrivals > 0
            ORDER BY delay_pct DESC
            LIMIT 10
        """)
        st.dataframe(delayed_dest_df, use_container_width=True)

# ========================================================
# 6. 11 EVALUATION SQL QUERIES
# ========================================================
elif menu == "💻 11 Evaluation SQL Queries":
    st.header("Interactive SQL Evaluation Queries")
    st.write("Execute all 11 required Capstone evaluation queries with interactive SQL execution.")
    
    queries = {
        "1. Total flights for each aircraft model": """
SELECT a.model, COUNT(f.flight_id) AS total_flights
FROM aircraft a
JOIN flights f ON a.registration = f.aircraft_registration
GROUP BY a.model
ORDER BY total_flights DESC;
""",
        "2. Aircraft assigned to more than 5 flights": """
SELECT a.registration, a.model, COUNT(f.flight_id) AS flight_count
FROM aircraft a
JOIN flights f ON a.registration = f.aircraft_registration
GROUP BY a.registration, a.model
HAVING COUNT(f.flight_id) > 5
ORDER BY flight_count DESC;
""",
        "3. Airports with more than 5 outbound flights": """
SELECT ap.name, COUNT(f.flight_id) AS outbound_flights
FROM airport ap
JOIN flights f ON ap.iata_code = f.origin_iata
GROUP BY ap.airport_id, ap.name
HAVING COUNT(f.flight_id) > 5
ORDER BY outbound_flights DESC;
""",
        "4. Top 3 destination airports by arriving flights": """
SELECT ap.name, ap.city, COUNT(f.flight_id) AS arriving_flights
FROM airport ap
JOIN flights f ON ap.iata_code = f.destination_iata
GROUP BY ap.airport_id, ap.name, ap.city
ORDER BY arriving_flights DESC
LIMIT 3;
""",
        "5. Flight categorization: Domestic vs International (CASE WHEN)": """
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
""",
        "6. 5 most recent arrivals at DEL airport": """
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
""",
        "7. Airports with no arriving flights (never used as destination)": """
SELECT ap.iata_code, ap.name, ap.city, ap.country
FROM airport ap
LEFT JOIN flights f ON ap.iata_code = f.destination_iata
WHERE f.flight_id IS NULL;
""",
        "8. Flight count by status per airline (CASE WHEN)": """
SELECT 
    airline_code,
    COUNT(CASE WHEN status = 'On Time' THEN 1 END) AS on_time_count,
    COUNT(CASE WHEN status = 'Delayed' THEN 1 END) AS delayed_count,
    COUNT(CASE WHEN status = 'Cancelled' THEN 1 END) AS cancelled_count,
    COUNT(*) AS total_flights
FROM flights
GROUP BY airline_code
ORDER BY total_flights DESC;
""",
        "9. All cancelled flights with aircraft and both airports": """
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
""",
        "10. City pairs with > 2 different aircraft models operating": """
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
""",
        "11. % of delayed flights among arrivals by destination": """
SELECT 
    ap.name AS destination_airport,
    COUNT(f.flight_id) AS total_arrivals,
    COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) AS delayed_arrivals,
    ROUND(COUNT(CASE WHEN f.status = 'Delayed' THEN 1 END) * 100.0 / COUNT(f.flight_id), 2) AS delayed_percentage
FROM airport ap
JOIN flights f ON ap.iata_code = f.destination_iata
GROUP BY ap.airport_id, ap.name
ORDER BY delayed_percentage DESC;
"""
    }

    selected_query_title = st.selectbox("Select SQL Query to Execute", list(queries.keys()))
    sql_text = queries[selected_query_title]

    st.code(sql_text, language="sql")
    
    if st.button("▶️ Execute Query"):
        res = run_query(sql_text)
        st.success(f"Query returned {len(res)} rows:")
        st.dataframe(res, use_container_width=True)
