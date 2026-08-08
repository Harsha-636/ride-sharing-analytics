import os
import sqlite3
import pandas as pd
import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="RideFlow Analytics",
    page_icon="🚖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM UI
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #f5f7fb;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #172033;
    }

    .hero {
        background: linear-gradient(135deg, #172033, #263b63);
        padding: 32px;
        border-radius: 22px;
        margin-bottom: 24px;
    }

    .hero-title {
        color: white;
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .hero-text {
        color: #dbe5f5;
        font-size: 16px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 750;
        color: #172033;
        margin-top: 10px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e9f0;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.04);
    }

    div[data-testid="stExpander"] {
        background: white;
        border: 1px solid #e5e9f0;
        border-radius: 14px;
    }

    div.stButton > button {
        border-radius: 10px;
        font-weight: 650;
    }

    div[data-testid="stDataEditor"] {
        border-radius: 14px;
        overflow: hidden;
    }

    .footer {
        text-align: center;
        color: #7b8494;
        padding: 25px;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# GROQ
# ============================================================

GROQ_MODEL = "openai/gpt-oss-120b"


def call_groq(messages, temperature=0.3):

    api_key = st.secrets.get("GROQ_API_KEY")

    if not api_key:
        return None, (
            "GROQ_API_KEY is missing from Streamlit Secrets. "
            "Add your Groq API key as GROQ_API_KEY."
        )

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": temperature
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"], None

    except requests.exceptions.HTTPError:
        return None, (
            f"Groq API error ({response.status_code}): "
            f"{response.text[:400]}"
        )

    except Exception as e:
        return None, f"Request to Groq failed: {e}"


# ============================================================
# LOAD DATA
# ============================================================

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def load_default(csv_name, fallback_rows, columns):

    path = os.path.join(APP_DIR, csv_name)

    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            pass

    return pd.DataFrame(
        fallback_rows,
        columns=columns
    )


DEFAULT_RIDERS = load_default(
    "riders_data.csv",
    [
        [1, "Rahul", "Mumbai", "2024-01-10"],
        [2, "Priya", "Delhi", "2024-02-15"],
        [3, "Amit", "Hyderabad", "2024-03-01"]
    ],
    [
        "rider_id",
        "rider_name",
        "city",
        "signup_date"
    ]
)


DEFAULT_DRIVERS = load_default(
    "drivers_data.csv",
    [
        [101, "Arjun", "Sedan", "Mumbai", "2023-05-10"],
        [102, "Priya", "SUV", "Delhi", "2023-06-15"],
        [103, "Ravi", "Bike", "Hyderabad", "2023-07-20"]
    ],
    [
        "driver_id",
        "driver_name",
        "vehicle_type",
        "city",
        "joining_date"
    ]
)


DEFAULT_TRIPS = load_default(
    "trips_data.csv",
    [
        [
            1001,
            1,
            101,
            "2025-01-05 09:15:00",
            "Andheri",
            "Bandra",
            12.5,
            420,
            "Completed",
            "UPI"
        ],
        [
            1002,
            2,
            102,
            "2025-01-05 18:30:00",
            "Connaught Place",
            "Airport",
            18.0,
            550,
            "Completed",
            "Card"
        ],
        [
            1003,
            3,
            103,
            "2025-01-06 08:30:00",
            "Madhapur",
            "Hitech City",
            8.0,
            220,
            "Cancelled",
            "UPI"
        ]
    ],
    [
        "trip_id",
        "rider_id",
        "driver_id",
        "trip_date",
        "pickup_location",
        "drop_location",
        "distance_km",
        "fare",
        "trip_status",
        "payment_method"
    ]
)


# ============================================================
# SESSION STATE
# ============================================================

if "riders_df" not in st.session_state:
    st.session_state.riders_df = DEFAULT_RIDERS.copy()

if "drivers_df" not in st.session_state:
    st.session_state.drivers_df = DEFAULT_DRIVERS.copy()

if "trips_df" not in st.session_state:
    st.session_state.trips_df = DEFAULT_TRIPS.copy()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ============================================================
# DATABASE
# ============================================================

def build_connection(riders_df, drivers_df, trips_df):

    conn = sqlite3.connect(
        ":memory:",
        check_same_thread=False
    )

    riders_df.to_sql(
        "riders",
        conn,
        index=False,
        if_exists="replace"
    )

    drivers_df.to_sql(
        "drivers",
        conn,
        index=False,
        if_exists="replace"
    )

    trips_df.to_sql(
        "trips",
        conn,
        index=False,
        if_exists="replace"
    )

    return conn


def query(conn, sql, params=None):

    return pd.read_sql_query(
        sql,
        conn,
        params=params
    )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🚖 RideFlow Analytics</div>
        <div class="hero-text">
            Explore trips, revenue, drivers, riders and routes
            through an interactive analytics dashboard.
            Edit your data and watch every insight update live.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TABS
# ============================================================

tabs = st.tabs(
    [
        "📊 Overview",
        "✏️ Edit Data",
        "💰 Revenue",
        "🚗 Drivers",
        "🧍 Riders",
        "⏰ Peak Times",
        "📍 Routes",
        "📈 Trends",
        "🔍 Insights",
        "💬 Ask the Data",
        "🗄️ Raw SQL"
    ]
)


(
    tab_overview,
    tab_edit,
    tab_revenue,
    tab_drivers,
    tab_riders,
    tab_time,
    tab_routes,
    tab_trends,
    tab_insights,
    tab_chat,
    tab_raw
) = tabs


# ============================================================
# EDIT DATA
# ============================================================

with tab_edit:

    st.header("✏️ Edit Your Data")

    st.caption(
        "Edit cells directly. Charts and KPIs update automatically."
    )

    st.subheader("🧍 Riders")

    edited_riders = st.data_editor(
        st.session_state.riders_df,
        num_rows="dynamic",
        use_container_width=True,
        key="riders_editor",
        column_config={
            "rider_id": st.column_config.NumberColumn(
                "Rider ID",
                required=True
            ),
            "rider_name": st.column_config.TextColumn(
                "Name",
                required=True
            ),
            "city": st.column_config.TextColumn(
                "City"
            ),
            "signup_date": st.column_config.TextColumn(
                "Signup Date"
            )
        }
    )

    st.subheader("🚗 Drivers")

    edited_drivers = st.data_editor(
        st.session_state.drivers_df,
        num_rows="dynamic",
        use_container_width=True,
        key="drivers_editor",
        column_config={
            "driver_id": st.column_config.NumberColumn(
                "Driver ID",
                required=True
            ),
            "driver_name": st.column_config.TextColumn(
                "Name",
                required=True
            ),
            "vehicle_type": st.column_config.SelectboxColumn(
                "Vehicle Type",
                options=[
                    "Sedan",
                    "SUV",
                    "Bike",
                    "Auto",
                    "Mini"
                ],
                required=True
            ),
            "city": st.column_config.TextColumn(
                "City"
            ),
            "joining_date": st.column_config.TextColumn(
                "Joining Date"
            )
        }
    )

    st.subheader("🚖 Trips")

    edited_trips = st.data_editor(
        st.session_state.trips_df,
        num_rows="dynamic",
        use_container_width=True,
        key="trips_editor",
        column_config={
            "trip_id": st.column_config.NumberColumn(
                "Trip ID",
                required=True
            ),
            "rider_id": st.column_config.NumberColumn(
                "Rider ID",
                required=True
            ),
            "driver_id": st.column_config.NumberColumn(
                "Driver ID",
                required=True
            ),
            "trip_date": st.column_config.TextColumn(
                "Trip Date / Time"
            ),
            "pickup_location": st.column_config.TextColumn(
                "Pickup"
            ),
            "drop_location": st.column_config.TextColumn(
                "Drop"
            ),
            "distance_km": st.column_config.NumberColumn(
                "Distance (km)",
                format="%.1f"
            ),
            "fare": st.column_config.NumberColumn(
                "Fare (₹)",
                format="%.0f"
            ),
            "trip_status": st.column_config.SelectboxColumn(
                "Status",
                options=[
                    "Completed",
                    "Cancelled"
                ],
                required=True
            ),
            "payment_method": st.column_config.SelectboxColumn(
                "Payment",
                options=[
                    "UPI",
                    "Card",
                    "Cash"
                ],
                required=True
            )
        }
    )

    st.session_state.riders_df = edited_riders
    st.session_state.drivers_df = edited_drivers
    st.session_state.trips_df = edited_trips

    st.divider()

    if st.button(
        "↩️ Reset Everything to Sample Data",
        use_container_width=True
    ):

        st.session_state.riders_df = DEFAULT_RIDERS.copy()
        st.session_state.drivers_df = DEFAULT_DRIVERS.copy()
        st.session_state.trips_df = DEFAULT_TRIPS.copy()

        st.rerun()


# ============================================================
# CURRENT DATABASE
# ============================================================

conn = build_connection(
    st.session_state.riders_df,
    st.session_state.drivers_df,
    st.session_state.trips_df
)


# ============================================================
# SUMMARY
# ============================================================

summary = query(
    conn,
    """
    SELECT
        COUNT(*) AS total_trips,

        SUM(
            CASE
                WHEN trip_status = 'Completed'
                THEN 1 ELSE 0
            END
        ) AS completed_trips,

        SUM(
            CASE
                WHEN trip_status = 'Cancelled'
                THEN 1 ELSE 0
            END
        ) AS cancelled_trips,

        SUM(
            CASE
                WHEN trip_status = 'Completed'
                THEN fare ELSE 0
            END
        ) AS total_revenue,

        AVG(
            CASE
                WHEN trip_status = 'Completed'
                THEN fare
            END
        ) AS avg_fare,

        AVG(
            CASE
                WHEN trip_status = 'Completed'
                THEN distance_km
            END
        ) AS avg_distance

    FROM trips
    """
).iloc[0]


total_trips = int(summary["total_trips"] or 0)

completed = int(
    summary["completed_trips"] or 0
)

cancelled = int(
    summary["cancelled_trips"] or 0
)

total_revenue = float(
    summary["total_revenue"] or 0
)

avg_distance = float(
    summary["avg_distance"] or 0
)


cancel_rate = (
    cancelled / total_trips * 100
    if total_trips
    else 0
)


fare_per_km = (
    total_revenue / (avg_distance * completed)
    if completed and avg_distance
    else 0
)


# ============================================================
# OVERVIEW
# ============================================================

with tab_overview:

    st.header("📊 Business Overview")

    st.caption(
        "Live analytics calculated from your current dataset."
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Total Trips",
        f"{total_trips:,}"
    )

    c2.metric(
        "Completed",
        f"{completed:,}"
    )

    c3.metric(
        "Cancellation Rate",
        f"{cancel_rate:.1f}%"
    )

    c4.metric(
        "Total Revenue",
        f"₹{total_revenue:,.0f}"
    )

    c5.metric(
        "Avg Fare / km",
        f"₹{fare_per_km:.2f}"
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🚦 Trip Status")

        status = query(
            conn,
            """
            SELECT trip_status, COUNT(*) AS trips
            FROM trips
            GROUP BY trip_status
            """
        )

        if not status.empty:
            st.bar_chart(
                status.set_index("trip_status")
            )

    with col2:

        st.subheader("💳 Payment Methods")

        payment = query(
            conn,
            """
            SELECT payment_method, COUNT(*) AS trips
            FROM trips
            GROUP BY payment_method
            """
        )

        if not payment.empty:
            st.bar_chart(
                payment.set_index("payment_method")
            )


# ============================================================
# REVENUE
# ============================================================

with tab_revenue:

    st.header("💰 Revenue Analytics")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Revenue by City")

        data = query(
            conn,
            """
            SELECT
                d.city,
                SUM(t.fare) AS revenue
            FROM trips t
            JOIN drivers d
                ON t.driver_id = d.driver_id
            WHERE t.trip_status = 'Completed'
            GROUP BY d.city
            ORDER BY revenue DESC
            """
        )

        if not data.empty:
            st.bar_chart(
                data.set_index("city")
            )
        else:
            st.info("No completed trips.")

    with col2:

        st.subheader("Revenue by Vehicle")

        data = query(
            conn,
            """
            SELECT
                d.vehicle_type,
                SUM(t.fare) AS revenue
            FROM trips t
            JOIN drivers d
                ON t.driver_id = d.driver_id
            WHERE t.trip_status = 'Completed'
            GROUP BY d.vehicle_type
            ORDER BY revenue DESC
            """
        )

        if not data.empty:
            st.bar_chart(
                data.set_index("vehicle_type")
            )

    st.subheader("Payment Method Distribution")

    payment = query(
        conn,
        """
        SELECT
            payment_method,
            COUNT(*) AS trips
        FROM trips
        GROUP BY payment_method
        """
    )

    if not payment.empty:
        st.bar_chart(
            payment.set_index("payment_method")
        )


# ============================================================
# DRIVERS
# ============================================================

with tab_drivers:

    st.header("🚗 Driver Analytics")

    driver_stats = query(
        conn,
        """
        SELECT
            d.driver_name,
            d.city,
            d.vehicle_type,

            COUNT(t.trip_id) AS total_trips,

            SUM(
                CASE
                    WHEN t.trip_status = 'Completed'
                    THEN 1 ELSE 0
                END
            ) AS completed_trips,

            SUM(
                CASE
                    WHEN t.trip_status = 'Completed'
                    THEN t.fare ELSE 0
                END
            ) AS earnings

        FROM drivers d

        LEFT JOIN trips t
            ON t.driver_id = d.driver_id

        GROUP BY
            d.driver_name,
            d.city,
            d.vehicle_type

        ORDER BY earnings DESC
        """
    )

    st.subheader("Driver Performance")

    st.dataframe(
        driver_stats,
        use_container_width=True,
        hide_index=True
    )

    if not driver_stats.empty:

        st.subheader("💰 Driver Earnings")

        chart_data = driver_stats[
            ["driver_name", "earnings"]
        ].set_index("driver_name")

        st.bar_chart(
            chart_data
        )


# ============================================================
# RIDERS
# ============================================================

with tab_riders:

    st.header("🧍 Rider Analytics")

    rider_stats = query(
        conn,
        """
        SELECT
            r.rider_name,
            r.city,

            COUNT(t.trip_id) AS total_trips,

            SUM(
                CASE
                    WHEN t.trip_status = 'Completed'
                    THEN t.fare ELSE 0
                END
            ) AS total_spend

        FROM riders r

        LEFT JOIN trips t
            ON t.rider_id = r.rider_id

        GROUP BY
            r.rider_name,
            r.city

        ORDER BY
            total_trips DESC,
            total_spend DESC
        """
    )

    st.dataframe(
        rider_stats,
        use_container_width=True,
        hide_index=True
    )

    retention_df = query(
        conn,
        """
        WITH rc AS (
            SELECT
                rider_id,
                COUNT(*) AS completed_trips

            FROM trips

            WHERE trip_status = 'Completed'

            GROUP BY rider_id
        )

        SELECT
            CASE
                WHEN COUNT(*) = 0 THEN 0
                ELSE ROUND(
                    100.0 *
                    SUM(
                        CASE
                            WHEN completed_trips > 1
                            THEN 1 ELSE 0
                        END
                    ) / COUNT(*),
                    1
                )
            END AS retention_pct

        FROM rc
        """
    )

    retention = (
        float(
            retention_df.iloc[0]["retention_pct"]
        )
        if not retention_df.empty
        else 0
    )

    st.metric(
        "🔁 Rider Retention Rate",
        f"{retention:.1f}%"
    )


# ============================================================
# PEAK TIMES
# ============================================================

with tab_time:

    st.header("⏰ Peak Time Analytics")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Peak Booking Hour")

        hours = query(
            conn,
            """
            SELECT
                CAST(
                    strftime('%H', trip_date)
                    AS INTEGER
                ) AS hour,

                COUNT(*) AS trips

            FROM trips

            GROUP BY hour

            ORDER BY hour
            """
        )

        if not hours.empty:
            st.bar_chart(
                hours.set_index("hour")
            )

    with col2:

        st.subheader("Peak Booking Day")

        days = query(
            conn,
            """
            SELECT
                strftime('%w', trip_date) AS dow,
                COUNT(*) AS trips

            FROM trips

            GROUP BY dow

            ORDER BY dow
            """
        )

        if not days.empty:

            names = {
                "0": "Sun",
                "1": "Mon",
                "2": "Tue",
                "3": "Wed",
                "4": "Thu",
                "5": "Fri",
                "6": "Sat"
            }

            days["day"] = days["dow"].map(names)

            st.bar_chart(
                days.set_index("day")["trips"]
            )


# ============================================================
# ROUTES
# ============================================================

with tab_routes:

    st.header("📍 Route Analytics")

    routes = query(
        conn,
        """
        SELECT
            pickup_location,
            drop_location,
            COUNT(*) AS trips,
            SUM(fare) AS revenue

        FROM trips

        WHERE trip_status = 'Completed'

        GROUP BY
            pickup_location,
            drop_location

        ORDER BY revenue DESC
        """
    )

    st.subheader("🏆 Highest Revenue Routes")

    st.dataframe(
        routes,
        use_container_width=True,
        hide_index=True
    )

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Top Pickup Locations")

        pickup = query(
            conn,
            """
            SELECT
                pickup_location,
                COUNT(*) AS trips

            FROM trips

            GROUP BY pickup_location

            ORDER BY trips DESC
            """
        )

        if not pickup.empty:
            st.bar_chart(
                pickup.set_index(
                    "pickup_location"
                )
            )

    with col2:

        st.subheader("Top Drop Locations")

        drop = query(
            conn,
            """
            SELECT
                drop_location,
                COUNT(*) AS trips

            FROM trips

            GROUP BY drop_location

            ORDER BY trips DESC
            """
        )

        if not drop.empty:
            st.bar_chart(
                drop.set_index(
                    "drop_location"
                )
            )


# ============================================================
# TRENDS
# ============================================================

with tab_trends:

    st.header("📈 Business Trends")

    monthly = query(
        conn,
        """
        SELECT
            strftime('%Y-%m', trip_date) AS month,

            SUM(
                CASE
                    WHEN trip_status = 'Completed'
                    THEN fare ELSE 0
                END
            ) AS revenue,

            COUNT(*) AS total_trips

        FROM trips

        GROUP BY month

        ORDER BY month
        """
    )

    if not monthly.empty:

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("💰 Monthly Revenue")

            st.line_chart(
                monthly.set_index("month")[
                    ["revenue"]
                ]
            )

        with col2:

            st.subheader("🚖 Monthly Trips")

            st.bar_chart(
                monthly.set_index("month")[
                    ["total_trips"]
                ]
            )

        monthly["mom_growth_pct"] = (
            monthly["revenue"]
            .pct_change()
            .mul(100)
            .round(2)
        )

        st.subheader(
            "📊 Month-over-Month Revenue Growth"
        )

        st.dataframe(
            monthly,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No trend data available.")


# ============================================================
# INSIGHTS
# ============================================================

with tab_insights:

    st.header("🔍 Business Insights")

    st.caption(
        "These insights are calculated from live SQL queries."
    )

    insight_lines = []

    # --------------------------------------------------------
    # Cancellation
    # --------------------------------------------------------

    cancel_by_vehicle = query(
        conn,
        """
        SELECT
            d.vehicle_type,

            ROUND(
                100.0 *
                SUM(
                    CASE
                        WHEN t.trip_status = 'Cancelled'
                        THEN 1 ELSE 0
                    END
                ) / COUNT(*),
                1
            ) AS cancel_rate_pct

        FROM trips t

        JOIN drivers d
            ON t.driver_id = d.driver_id

        GROUP BY d.vehicle_type

        ORDER BY cancel_rate_pct DESC
        """
    )

    if len(cancel_by_vehicle) >= 2:

        worst = cancel_by_vehicle.iloc[0]
        best = cancel_by_vehicle.iloc[-1]

        line = (
            f"{worst['vehicle_type']} has the highest "
            f"cancellation rate at "
            f"{worst['cancel_rate_pct']}%, while "
            f"{best['vehicle_type']} has "
            f"{best['cancel_rate_pct']}%."
        )

        insight_lines.append(
            "Cancellation: " + line
        )

        st.warning(
            "🚨 **Cancellation Insight**\n\n"
            + line
        )


    # --------------------------------------------------------
    # Revenue concentration
    # --------------------------------------------------------

    rider_rev = query(
        conn,
        """
        SELECT
            rider_id,
            SUM(fare) AS spend

        FROM trips

        WHERE trip_status = 'Completed'

        GROUP BY rider_id

        ORDER BY spend DESC
        """
    )

    if len(rider_rev) >= 5:

        top_n = max(
            1,
            int(len(rider_rev) * 0.2)
        )

        total_spend = rider_rev["spend"].sum()

        if total_spend > 0:

            pct = (
                rider_rev.head(top_n)["spend"].sum()
                / total_spend
                * 100
            )

            line = (
                f"The top 20% of riders "
                f"({top_n} of {len(rider_rev)}) "
                f"generate {pct:.1f}% of completed-trip revenue."
            )

            insight_lines.append(
                "Revenue concentration: " + line
            )

            st.info(
                "💰 **Revenue Concentration**\n\n"
                + line
            )


    # --------------------------------------------------------
    # Rush hour
    # --------------------------------------------------------

    surge = query(
        conn,
        """
        SELECT

            CASE
                WHEN CAST(
                    strftime('%H', trip_date)
                    AS INTEGER
                ) IN (8, 9, 18, 19)

                THEN 'Rush Hour'

                ELSE 'Off-Peak'
            END AS period,

            AVG(
                CASE
                    WHEN distance_km > 0
                    THEN fare / distance_km
                END
            ) AS fare_per_km

        FROM trips

        WHERE trip_status = 'Completed'

        GROUP BY period
        """
    )

    if len(surge) == 2:

        rush = surge[
            surge["period"] == "Rush Hour"
        ]["fare_per_km"]

        off = surge[
            surge["period"] == "Off-Peak"
        ]["fare_per_km"]

        if (
            not rush.empty
            and not off.empty
            and off.iloc[0] > 0
        ):

            premium = (
                (rush.iloc[0] - off.iloc[0])
                / off.iloc[0]
                * 100
            )

            line = (
                f"Rush-hour trips have a "
                f"{premium:.0f}% difference in "
                f"average fare per km compared with off-peak trips."
            )

            insight_lines.append(
                "Rush-hour pricing: " + line
            )

            st.success(
                "⏰ **Rush-Hour Insight**\n\n"
                + line
            )


    if not insight_lines:

        st.info(
            "Not enough data to generate detailed insights yet."
        )


# ============================================================
# ASK THE DATA
# ============================================================

with tab_chat:

    st.header("💬 Ask the Data")

    st.caption(
        "Ask questions about the current dashboard in plain English."
    )

    current_context = f"""
Current ride-sharing dashboard:

Total trips: {total_trips}
Completed trips: {completed}
Cancelled trips: {cancelled}
Cancellation rate: {cancel_rate:.1f}%
Total revenue: ₹{total_revenue:,.0f}
Average fare per km: ₹{fare_per_km:.2f}

Insights:
{chr(10).join(insight_lines)}
"""

    system_prompt = f"""
You are a helpful business data analyst.

Explain the dashboard in simple English.

Only use the data provided below.
Do not invent numbers.

Keep answers concise, around 3-5 sentences unless
the user asks for more detail.

If the data cannot answer the question,
clearly say that.

DATA:
{current_context}
"""

    col1, col2 = st.columns([4, 1])

    with col2:

        if st.button(
            "✨ Explain Insights",
            use_container_width=True
        ):

            st.session_state.chat_history.append(
                {
                    "role": "user",
                    "content": (
                        "Explain the most important things "
                        "I should know about this dashboard."
                    )
                }
            )

    for message in st.session_state.chat_history:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


    question = st.chat_input(
        "Ask something about the data..."
    )


    if question:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question
            }
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ] + st.session_state.chat_history

        with st.chat_message("assistant"):

            with st.spinner(
                "🤖 Analyzing your data..."
            ):

                answer, error = call_groq(
                    messages
                )

                if error:

                    st.error(error)

                else:

                    st.markdown(answer)

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": answer
                        }
                    )


    if st.session_state.chat_history:

        st.divider()

        if st.button(
            "🗑️ Clear Chat"
        ):

            st.session_state.chat_history = []

            st.rerun()


# ============================================================
# RAW SQL
# ============================================================

with tab_raw:

    st.header("🗄️ SQL Playground")

    st.caption(
        "Run SELECT queries against the live in-memory database."
    )

    sql = st.text_area(
        "SQL Query",
        value="SELECT * FROM trips LIMIT 10;",
        height=130
    )

    if st.button(
        "▶️ Run Query",
        use_container_width=True
    ):

        try:

            sql_clean = sql.strip().lower()

            if not sql_clean.startswith(
                "select"
            ):

                st.error(
                    "For safety, only SELECT queries are allowed."
                )

            else:

                result = query(
                    conn,
                    sql
                )

                st.success(
                    f"Query returned {len(result)} rows."
                )

                st.dataframe(
                    result,
                    use_container_width=True,
                    hide_index=True
                )

        except Exception as e:

            st.error(
                f"SQL error: {e}"
            )

    st.divider()

    st.subheader("📋 Current Tables")

    with st.expander("🧍 Riders Table"):

        st.dataframe(
            query(
                conn,
                "SELECT * FROM riders"
            ),
            use_container_width=True,
            hide_index=True
        )

    with st.expander("🚗 Drivers Table"):

        st.dataframe(
            query(
                conn,
                "SELECT * FROM drivers"
            ),
            use_container_width=True,
            hide_index=True
        )

    with st.expander("🚖 Trips Table"):

        st.dataframe(
            query(
                conn,
                "SELECT * FROM trips"
            ),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        🚖 RideFlow Analytics &nbsp;•&nbsp;
        Built with Streamlit + SQLite + Groq AI
        <br>
        Edit data → Explore analytics → Ask the data
    </div>
    """,
    unsafe_allow_html=True
)
