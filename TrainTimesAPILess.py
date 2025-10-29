# Central = 200010
# St Leonards = 206520   10101115

# Run the script
# python -m streamlit run "C:/Users/Admin/Desktop/TrainTimes.py"

import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timezone
import pytz
from streamlit_autorefresh import st_autorefresh

# === Configuration ===
API_URL = "https://api.transport.nsw.gov.au/v1/tp/departure_mon"
STOP_ID = "10101115"
sydney_tz = pytz.timezone("Australia/Sydney")
now = datetime.now(sydney_tz)
now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)

HEADERS = {
    "Authorization": f"apikey {API_KEY}",
    "Accept": "application/json"
}

PARAMS = {
    "outputFormat": "rapidJSON",
    "type_dm": "stop",
    "name_dm": STOP_ID,
    "coordOutputFormat": "WGS84[DD.DDDDDD]",
    "mode": "direct",
    #"itdDate": now.strftime("%Y%m%d"),  # YYYYMMDD
    #"itdTime": now.strftime("%H%M"),    # HHMM (24h)
    "TfNSWDM": "true",
    "depArrMacro": "dep"
}

# === Streamlit UI ===

# Remove top padding
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    h1 {
        font-size: 50px !important;
        text-align: center;
        background-color: #bad8e0;
    }
    h2 {
        font-size: 50px !important;
        text-align: center;
        background-color: #ccd5d8;
    }
    h3 {
        font-size: 40px !important;
        text-align: center;
        background-color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True
) #f0f0f0

# Refresh every 20 seconds (20,000 ms)
count = st_autorefresh(interval=20 * 1000, key="datarefresh")

st.title("Upcoming Departures: St Leonards")
st.set_page_config(
    page_title="Train Departures",
    layout="wide"   # <-- makes the entire app use full page width
)
st.subheader(f"Last updated: {time.strftime('%H:%M')}")
num = 50   #st.sidebar.slider("Number of upcoming departures to show", 5, 20, 10)

# Function to color-code based on lateness
def get_color(minutes_late):
    if minutes_late >= 5:
        return "red"
    elif minutes_late > 1:
        return "orange"
    else:
        return "black"


# === Fetch Data Function ===
@st.cache_data(ttl=5)
def get_departures():
    try:
        response = requests.get(API_URL, headers=HEADERS, params=PARAMS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

data = get_departures()

# === Parse JSON ===
if data and "stopEvents" in data:
    departures = []
    for event in data["stopEvents"][:num]:
        dep = event.get("departureTimeBaseTimetable")
        actual = event.get("departureTimeEstimated",dep)
        dep_syd = datetime.fromisoformat(dep.replace("Z", "+00:00")).astimezone(sydney_tz)
        act_syd = datetime.fromisoformat(actual.replace("Z", "+00:00")).astimezone(sydney_tz)
        line = event["transportation"]["number"]
        dest = event["transportation"]["destination"]["name"]
        plat = event["location"]["properties"]["platformName"]
        platform = event["location"]["properties"]["platform"]
        stopID = event.get("stopId")
        
        # Convert departure time to minutes from now
        dep_time = datetime.strptime(dep, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        act_time = datetime.strptime(actual, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        minutes_until = int((act_time - now_utc).total_seconds() / 60)
        minutes_late = int((act_time - dep_time).total_seconds() / 60)
        time_display = f"{minutes_until} min" if minutes_until >= 0 else "departed"
        late_display = f"{minutes_late} late" if minutes_late > 0 else f"{minutes_late} early" if minutes_late < 0 else "on time"

        #if platform in {"A","STL2","STL3"}:  #,"A","B","%"   ,"STL3"
        departures.append({
            "Time": time_display,
            "Late": late_display,
            "MinsLate": minutes_late,
            "Leaving": act_syd.strftime("%H:%M"),   # "%Y-%m-%d %H:%M:%S"
            "Destination": dest,
            "Line": line,
            "Platform": plat,
            "Stand": platform
        })

    # Convert to full DataFrame
    df_all = pd.DataFrame(departures)

    # Split by platform
    df_plat1 = df_all[df_all["Stand"].str.contains("STL2", na=False)].head(5)
    df_plat2 = df_all[df_all["Stand"].str.contains("STL3", na=False)].head(5)
    df_plat3 = df_all[df_all["Line"].str.contains("267|114|144|653", na=False) & df_all["Platform"].str.contains("A", na=False)].head(5)

    # Streamlit display
    col1, div1, col2, div2, col3 = st.columns([1,0.05,1,0.05,1])

    with div1:
        st.markdown("<div style='border-left:2px solid #ccc; height:100%;'></div>", unsafe_allow_html=True)

    with div2:
        st.markdown("<div style='border-left:2px solid #ccc; height:100%;'></div>", unsafe_allow_html=True)

    with col1:
        st.header("🚉 to City")
        for _, row in df_plat1.iterrows():
            color = get_color(row["MinsLate"])
            st.markdown(
                f"""
                <div style="
                    font-size:70px;
                    color:{color};
                    font-weight:600;
                    line-height:1.4;
                    margin-bottom:4px;
                    text-align: center;
                    font-weight: bold;
                ">
                {row['Time']}
                </div>
                """,
                unsafe_allow_html=True
            ) #({row['Leaving']})

    with col2:
        st.header("🚉 Chatswood")
        for _, row in df_plat2.iterrows():
            color = get_color(row["MinsLate"])
            st.markdown(
                f"""
                <div style="
                    font-size:70px;
                    color:{color};
                    font-weight:600;
                    line-height:1.4;
                    margin-bottom:4px;
                    text-align: center;
                    font-weight: bold;
                ">
                {row['Time']}
                </div>
                """,
                unsafe_allow_html=True
            )

    with col3:
        st.header("🚌 to APPS")
        for _, row in df_plat3.iterrows():
            color = get_color(row["MinsLate"])
            st.markdown(
                f"""
                <div style="
                    font-size:70px;
                    color:{color};
                    font-weight:600;
                    line-height:1.4;
                    margin-bottom:4px;
                    text-align: center;
                    font-weight: bold;
                ">
                {row['Line']}: {row['Time']}
                </div>
                """,
                unsafe_allow_html=True
            )

else:
    st.warning("No departure data available.")


# Dump raw JSON for debugging
#response = requests.get(API_URL, headers=HEADERS, params=PARAMS)
#st.write("Raw JSON response:")
#st.json(response.json())



