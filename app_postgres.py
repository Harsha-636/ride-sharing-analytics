"""
Ride-Sharing Analytics Dashboard — Postgres-backed version
------------------------------------------------------------
Same dashboard as the main app, but reads from a real PostgreSQL
database (e.g. a free Supabase or Neon project) instead of bundled
CSVs. Connection string comes from Streamlit secrets — see the
"Deploy" section of README_POSTGRES.md for setup steps.

This file intentionally does NOT include the in-app data editor from
the SQLite version — editing production data through a public URL is
a bad idea. Use the Supabase/Neon SQL editor (or a proper admin tool)
to change data; this app is read-only, which is also a more honest
story for an interview ("the demo app is editable sandbox data; the
production-style app is read-only against a real database").
"""

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="Ride-Sharing Analytics (Postgres)", page_icon="🐘", layout="wide")


@st.cache_resource
def get_engine():
    db_url = st.secrets.get("DATABASE_URL")
    if not db_url:
        st.error(
            "No DATABASE_URL found in Streamlit secrets. Add one under "
            "Settings → Secrets in the Streamlit Cloud dashboard — see "
            "README_POSTGRES.md for the exact format."
        )
        st.stop()
    return create_engine(db_url, pool_pre_ping=True)


def q(sql, params=None):
    with get_engine().connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)


st.title("🐘 Ride-Sharing Analytics — Postgres Edition")
st.caption("Same dashboard, backed by a real PostgreSQL database instead of bundled sample data.")

try:
    summary = q("""
        SELECT
            COUNT(*) AS total_trips,
            SUM(CASE WHEN trip_status = 'Completed' THEN 1 ELSE 0 END) AS completed_trips,
            SUM(CASE WHEN trip_status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_trips,
            SUM(CASE WHEN trip_status = 'Completed' THEN fare ELSE 0 END) AS total_revenue,
            ROUND(AVG(CASE WHEN trip_status = 'Completed' THEN fare END)::numeric, 2) AS avg_fare,
            ROUND(AVG(CASE WHEN trip_status = 'Completed' THEN distance_km END)::numeric, 2) AS avg_distance
        FROM trips
    """).iloc[0]
except Exception as e:
    st.error(f"Couldn't query the database. Check your DATABASE_URL and that schema.sql / seed_data.sql "
              f"have been run. Error: {e}")
    st.stop()

cancel_rate = round(100 * summary["cancelled_trips"] / summary["total_trips"], 1)
fare_per_km = round(summary["total_revenue"] / (summary["avg_distance"] * summary["completed_trips"]), 2)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Trips", int(summary["total_trips"]))
c2.metric("Completed", int(summary["completed_trips"]))
c3.metric("Cancellation Rate", f"{cancel_rate}%")
c4.metric("Total Revenue", f"₹{summary['total_revenue']:,.0f}")
c5.metric("Avg Fare / km", f"₹{fare_per_km}")

st.divider()

tab_revenue, tab_trends, tab_insights = st.tabs(["💰 Revenue", "📈 Trends", "🔍 Insights"])

with tab_revenue:
    rev_city = q("""
        SELECT d.city, SUM(t.fare) AS revenue
        FROM trips t JOIN drivers d ON t.driver_id = d.driver_id
        WHERE t.trip_status = 'Completed'
        GROUP BY d.city ORDER BY revenue DESC
    """)
    st.subheader("Revenue by City")
    st.bar_chart(rev_city.set_index("city"))

    rev_vehicle = q("""
        SELECT d.vehicle_type, SUM(t.fare) AS revenue
        FROM trips t JOIN drivers d ON t.driver_id = d.driver_id
        WHERE t.trip_status = 'Completed'
        GROUP BY d.vehicle_type ORDER BY revenue DESC
    """)
    st.subheader("Revenue by Vehicle Type")
    st.bar_chart(rev_vehicle.set_index("vehicle_type"))

with tab_trends:
    monthly = q("""
        SELECT TO_CHAR(trip_date, 'YYYY-MM') AS month,
               SUM(CASE WHEN trip_status = 'Completed' THEN fare ELSE 0 END) AS revenue,
               COUNT(*) AS total_trips
        FROM trips GROUP BY month ORDER BY month
    """)
    st.subheader("Monthly Revenue Trend")
    st.line_chart(monthly.set_index("month")[["revenue"]])

with tab_insights:
    cancel_by_vehicle = q("""
        SELECT d.vehicle_type,
               ROUND(100.0*SUM(CASE WHEN t.trip_status='Cancelled' THEN 1 ELSE 0 END)/COUNT(*), 1) AS cancel_rate_pct
        FROM trips t JOIN drivers d ON t.driver_id = d.driver_id
        GROUP BY d.vehicle_type ORDER BY cancel_rate_pct DESC
    """)
    if len(cancel_by_vehicle) >= 2:
        worst, best = cancel_by_vehicle.iloc[0], cancel_by_vehicle.iloc[-1]
        st.markdown(
            f"**🚨 Cancellation gap:** `{worst['vehicle_type']}` trips cancel at "
            f"**{worst['cancel_rate_pct']}%**, vs. only **{best['cancel_rate_pct']}%** "
            f"for `{best['vehicle_type']}`."
        )

st.divider()
st.caption("Read-only dashboard backed by PostgreSQL. Edit data via the Supabase/Neon SQL editor, not this app.")
