import requests
import streamlit as st
from datetime import datetime
from streamlit_folium import st_folium
import folium

# ---------------------- API KEYS ---------------------- #
AVIATIONSTACK_API_KEY = "fa6d9b7183dbdb0d28242f98257e2980"

# ---------------------- Streamlit Setup ---------------------- #
st.set_page_config(page_title="Flight Monitor", layout="wide")
st.title("✈️ Real-Time Global Flight Monitor")

# ---------------------- User Inputs ---------------------- #
st.markdown("Search for real-time international or domestic flights using flight number, or see departures from an airport.")

flight_number = st.text_input("🔍 Enter Flight Number (e.g., AI202, EK501)")
airport_code = st.text_input("🛫 Or Enter Airport IATA Code (e.g., DEL, BOM, JFK)")
destination_filter = st.text_input("🎯 Optional: Find number of flights to a destination (e.g., LHR for London Heathrow)")

# ---------------------- API Fetch ---------------------- #
def get_flight_by_number(flight_number):
    url = f"https://api.aviationstack.com/v1/flights?access_key={AVIATIONSTACK_API_KEY}&flight_iata={flight_number}"
    response = requests.get(url, timeout=10)
    return response.json()

def get_departures_by_airport(airport_code):
    url = f"https://api.aviationstack.com/v1/flights?access_key={AVIATIONSTACK_API_KEY}&dep_iata={airport_code}"
    response = requests.get(url, timeout=10)
    return response.json()

def count_flights_to_destination(destination_iata):
    indian_airports = ['DEL', 'BOM', 'BLR', 'HYD', 'MAA', 'CCU']
    total = 0
    flights_found = []

    for airport in indian_airports:
        url = f"https://api.aviationstack.com/v1/flights?access_key={AVIATIONSTACK_API_KEY}&dep_iata={airport}"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()

            if "data" in data:
                for flight in data["data"]:
                    arrival = flight.get("arrival", {})
                    arr_iata = arrival.get("iata")
                    if arr_iata == destination_iata:
                        total += 1
                        flights_found.append(flight)

        except Exception as e:
            st.error(f"❌ Error fetching from {airport}: {e}")

    return total, flights_found

# ---------------------- Display Functions ---------------------- #
def display_flight_info(data):
    if "data" in data and data["data"]:
        for flight in data["data"]:
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"🛫 {flight['departure']['airport']} ({flight['departure']['iata']})")
                st.write(f"Scheduled: {flight['departure']['scheduled']}")
            with col2:
                st.subheader(f"🛬 {flight['arrival']['airport']} ({flight['arrival']['iata']})")
                st.write(f"Scheduled: {flight['arrival']['scheduled']}")

            st.write(f"✈️ Airline: {flight['airline']['name']}")
            st.write(f"📍 Status: {flight['flight_status']}")
            st.write(f"🆔 Flight IATA: {flight['flight']['iata']}")
            st.write(f"🕓 Updated: {flight['updated_at'] if 'updated_at' in flight else 'N/A'}")
    else:
        st.warning("No flight data found.")

# ---------------------- Map Flights (Optional) ---------------------- #
def map_flights(data):
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=2)
    count = 0
    if "data" in data and data["data"]:
        for flight in data["data"]:
            dep = flight.get("departure")
            arr = flight.get("arrival")
            dep_lat, dep_lon = dep.get("latitude"), dep.get("longitude")
            arr_lat, arr_lon = arr.get("latitude"), arr.get("longitude")
            if dep_lat and dep_lon:
                folium.Marker(
                    location=[dep_lat, dep_lon],
                    popup=f"Departure: {dep['airport']} ({dep['iata']})",
                    icon=folium.Icon(color="green", icon="plane")
                ).add_to(m)
            if arr_lat and arr_lon:
                folium.Marker(
                    location=[arr_lat, arr_lon],
                    popup=f"Arrival: {arr['airport']} ({arr['iata']})",
                    icon=folium.Icon(color="red", icon="flag")
                ).add_to(m)
            count += 1
    m.get_root().html.add_child(folium.Element(f"<h4 align='center'>🛰 Showing {count} flights</h4>"))
    return m

# ---------------------- Main Logic ---------------------- #
if flight_number:
    st.subheader(f"🔍 Searching for Flight {flight_number.upper()}...")
    data = get_flight_by_number(flight_number.upper())
    display_flight_info(data)
    map_obj = map_flights(data)
    st_folium(map_obj, width=1000, height=600)
elif airport_code:
    st.subheader(f"📡 Departures from Airport: {airport_code.upper()}")
    data = get_departures_by_airport(airport_code.upper())
    display_flight_info(data)
    map_obj = map_flights(data)
    st_folium(map_obj, width=1000, height=600)
elif destination_filter:
    st.subheader(f"🎯 Flights going to: {destination_filter.upper()} from Indian Airports")
    total, flights = count_flights_to_destination(destination_filter.upper())
    st.success(f"✅ Total flights to {destination_filter.upper()}: {total}")
    for f in flights:
        st.markdown(f"- ✈️ {f['flight']['iata']} from {f['departure']['iata']} to {f['arrival']['iata']} — {f['airline']['name']}")
else:
    st.info("Enter a flight number, airport code, or destination to get started.")
