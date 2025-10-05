"""
Main Streamlit app for Will It Rain On My Parade?
Organized and cleaned for clarity and maintainability.
"""
# --- Imports ---
import streamlit as st
import datetime
import pandas as pd
import calendar
import html
import textwrap
# Third-party and local imports
from services.nasa_api import fetch_nasa_power_monthly_averages
from services.weather_api import get_forecast
from services.pollution_api import get_pollution_stats
from utils.helpers import process_forecast, process_forecast_with_fallback
from utils.scoring import parade_suitability_score, get_event_suggestion
from ui.components import show_result
from ui.sections import render_header, render_inputs, render_suitability_card, render_nasa_section, render_nasa_results, render_pollution_stats
from services.openai_ai import summarize_weather as oa_summarize, answer_weather_question as oa_answer, is_openai_configured
from ui.map_panel import render_map_section
# OpenAI-only helper wrappers
def ai_summarize(weather_dict):
    if is_openai_configured():
        return oa_summarize(weather_dict)
    return 'OpenAI not configured (add OPENAI_API_KEY).'

def ai_answer(question: str, context: str):
    if is_openai_configured():
        return oa_answer(question, context)
    return '(AI disabled) Configure OPENAI_API_KEY.'

# --- Set Page Config ---
st.set_page_config(
    page_title="Astrocast",
    page_icon="🌦️",
    layout="wide"
)

from ui.theme import inject_theme
from ui.branding import render_nav

# Inject theme
inject_theme()

# Determine active page from query params (post-experimental API)
try:
    qp = st.query_params  # Streamlit >= 1.32 style object-like mapping
    active_page = qp.get('page', 'home') if isinstance(qp.get('page', None), str) else (qp.get('page') or 'home')
except Exception:
    # Fallback for older versions
    legacy_q = st.experimental_get_query_params()
    active_page = legacy_q.get('page', ['home'])[0]

render_nav(active_page)

def _goto(page_key: str):
    try:
        st.query_params.update({'page': page_key})
    except Exception:
        st.experimental_set_query_params(page=page_key)
    st.rerun()

# --- Chat Assistant Styles ---
st.markdown("""
<style>
.chat-panel { position:fixed; bottom:100px; right:26px; width:360px; max-height:520px; background:#ffffff; border-radius:18px; box-shadow:0 10px 28px rgba(0,0,0,0.28); padding:14px 16px 18px; z-index:10001; display:flex; flex-direction:column; }
.chat-header { font-weight:700; font-size:1.05rem; margin-bottom:4px; color:#274b7a; display:flex; align-items:center; justify-content:space-between; }
.chat-messages { flex:1; overflow-y:auto; border:1px solid #e2e8f0; border-radius:12px; padding:8px 10px; background:#f8fbff; }
.chat-msg-user { background:#4f8cff; color:#fff; padding:6px 10px; border-radius:14px; margin:6px 0; font-size:0.85rem; align-self:flex-end; max-width:85%; }
.chat-msg-bot { background:#eef4ff; color:#1e293b; padding:6px 10px; border-radius:14px; margin:6px 0; font-size:0.85rem; align-self:flex-start; max-width:90%; }
.chat-input-row { display:flex; gap:6px; margin-top:8px; }
.chat-input-row textarea { flex:1; border-radius:12px !important; }
.chat-close { cursor:pointer; font-size:1.2rem; line-height:1; padding:2px 8px; border-radius:8px; }
.chat-close:hover { background:#e2e8f0; }
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [20, 0]
if 'map_pin' not in st.session_state:
    st.session_state['map_pin'] = None
if 'clicked_coords' not in st.session_state:
    st.session_state['clicked_coords'] = None
if 'show_chat' not in st.session_state:
    st.session_state['show_chat'] = False
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []  # list of dicts: {role:'user'|'bot', 'text':str}

# Auto-open chat if ?page=home&chat=1
try:
    if active_page == 'home':
        # Access query params robustly
        open_chat = False
        try:
            qp_chat = st.query_params.get('chat') if hasattr(st, 'query_params') else None
            if isinstance(qp_chat, str) and qp_chat == '1':
                open_chat = True
        except Exception:
            legacy_q = st.experimental_get_query_params()
            if legacy_q.get('chat', ['0'])[0] == '1':
                open_chat = True
        if open_chat:
            st.session_state['show_chat'] = True
except Exception:
    pass



# Removed legacy inline brand bar (now handled by render_nav())
if active_page == 'home':
    # --- UI: Inputs ---
    city, date, check_weather, forecast_placeholder, cols = render_inputs()
else:
    # Provide common inputs for pages that still need a city context (compare / insights / report)
    with st.container():
        st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)
        city = st.text_input("City", value="", help="Enter a city to fetch data")
        date = datetime.date.today()
        check_weather = False
        forecast_placeholder = st.empty()
        cols = st.columns(3)
# Remove unnecessary empty white box
# st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

# --- Compare Feature (Weekend Parade) ---
if 'show_compare' not in st.session_state:
    st.session_state['show_compare'] = False
if 'compare_ai_summary' not in st.session_state:
    st.session_state['compare_ai_summary'] = None

@st.cache_data(show_spinner=False, ttl=1800)
def cached_forecast(city_name: str):
    return get_forecast(city_name)

@st.cache_data(show_spinner=False, ttl=3600)
def cached_nasa(city_name: str, year: int, month: int):
    return fetch_nasa_power_monthly_averages(city_name, year, month)

# (Removed compare toggle button formerly here – direct navigation via top navbar now controls access.)

def _next_weekend_day(day_name: str):
    today = datetime.date.today()
    target_weekday = 5 if day_name == 'Saturday' else 6
    delta = (target_weekday - today.weekday()) % 7
    return today + datetime.timedelta(days=delta)

def compute_city_score(city_name: str, target_dt: datetime.date):
    if not city_name:
        return None, "Empty city"
    try:
        data = cached_forecast(city_name)
    except Exception as e:
        return None, f"Forecast error: {e}".strip()
    date_str = target_dt.strftime('%Y-%m-%d')
    try:
        weather, used_date, substituted = process_forecast_with_fallback(data, date_str)
    except Exception as e:
        return None, f"Process error: {e}".strip()
    if not weather:
        return None, "No forecast data in window"
    # Fetch historical monthly averages (NASA) for scoring context
    hist = None
    try:
        hist = cached_nasa(city_name, target_dt.year, target_dt.month)
    except Exception:
        hist = None
    rain_prob = 90 if weather['total_rain'] > 5 else 70 if weather['total_rain'] > 0 else 0
    wind_speed = weather.get('avg_wind', 10)
    forecast_input = {
        'rain_probability': rain_prob,
        'temp': weather['avg_temp'],
        'humidity': weather['avg_humidity'],
        'wind_speed': wind_speed
    }
    historical_input = {
        'avg_rainfall_mm': hist['avg_rainfall_mm'] if hist else 0,
        'avg_temp_c': hist['avg_temperature_c'] if hist else weather['avg_temp']
    }
    result = parade_suitability_score(forecast_input, historical_input)
    suggestion = get_event_suggestion(forecast_input)
    payload = {
        'City': city_name.title(),
        'Score': result['score'],
        'RainProb(%)': rain_prob,
        'Temp(°C)': round(weather['avg_temp'],1),
        'Humidity(%)': round(weather['avg_humidity']),
        'Wind(m/s)': round(wind_speed,1),
        'Rain(mm)': round(weather['total_rain'],1),
        'Cond': f"{weather.get('condition_emoji','')} {weather.get('condition','')}",
        'Suggestion': suggestion,
        '_used_date': used_date,
        '_substituted': substituted
    }
    return payload, None

if active_page == 'compare':
    st.markdown("""
    <div style='margin-top:1.2rem'></div>
    <div class='astro-card' style='margin-top:0;'>
      <h3 style='margin:0 0 .35rem;'>🏁 Weekend Parade Comparison</h3>
      <p class='sub' style='margin:0 0 .75rem; font-size:0.75rem;'>Compare two cities for the upcoming weekend.</p>
    </div>
    """, unsafe_allow_html=True)
    with st.form("compare_form"):
        col_a, col_b, col_day = st.columns([1,1,0.6])
        with col_a:
            city_a = st.text_input("City A", value="")
        with col_b:
            city_b = st.text_input("City B", value="")
        with col_day:
            day_choice = st.selectbox("Day", ["Saturday","Sunday"], index=0)
        submitted_compare = st.form_submit_button("Compare")
    if submitted_compare:
        target_dt = _next_weekend_day(day_choice)
        rows = []
        errors = []
        for cty in [city_a, city_b]:
            payload, err = compute_city_score(cty.strip(), target_dt)
            if payload:
                rows.append(payload)
            else:
                errors.append(f"{cty}: {err}")
        if rows:
            df_cmp = pd.DataFrame(rows).sort_values('Score', ascending=False).reset_index(drop=True)
            # Drop internal fields if present
            internal_cols = [c for c in ['_used_date','_substituted'] if c in df_cmp.columns]
            if internal_cols:
                display_df = df_cmp.drop(columns=internal_cols)
            else:
                display_df = df_cmp
            # Reorder columns for readability
            desired_order = [c for c in ['City','Cond','Score','RainProb(%)','Temp(°C)','Humidity(%)','Wind(m/s)','Rain(mm)','Suggestion'] if c in display_df.columns]
            display_df = display_df[desired_order]
            df_cmp.index = df_cmp.index + 1
            # Color bar for Score
            styled = display_df.style.bar(subset=['Score'], color='#4f8cff').format({
                'Temp(°C)': '{:.1f}', 'Wind(m/s)': '{:.1f}', 'Rain(mm)': '{:.1f}'
            })
            st.markdown(f"**Target Date:** {target_dt} (next {day_choice})")
            st.dataframe(styled, width='stretch')
            leader = df_cmp.iloc[0]
            st.success(f"Best city: {leader['City']} • Score {leader['Score']}/100 – {leader['Suggestion']}")
            # Fallback notice(s)
            subs = [r for r in rows if r.get('_substituted')]
            if subs:
                parts = [f"{r['City']}→{r['_used_date']}" for r in subs]
                st.info("Forecast fallback used (nearest available date): " + ", ".join(parts))
            # AI comparison summary
            if is_openai_configured():
                try:
                    comp_prompt = "Compare these cities for a weekend outdoor parade and give pros and cons then a recommendation.\n" + df_cmp.to_csv(index=False)
                    ai_cmp = oa_answer("Which city is better and why?", comp_prompt)
                    st.session_state['compare_ai_summary'] = ai_cmp
                except Exception as e:
                    st.warning(f"AI summary failed: {e}")
            if st.session_state.get('compare_ai_summary'):
                with st.expander("AI Comparison Summary"):
                    st.write(st.session_state['compare_ai_summary'])
        if errors:
            for e in errors:
                st.warning(e)

# --- Main Logic: Weather, Score, Suggestions ---
if active_page == 'home' and check_weather:
    if not city:
        st.error("⚠️ Please enter a city name")
    else:
        try:
            data = get_forecast(city)
        except Exception as e:
            st.error(f"Weather API error: {e}")
            data = None
        if not data:
            st.error("❌ Failed to fetch data. Check city name or API key.")
        else:
            target_date = date.strftime("%Y-%m-%d")
            try:
                weather, used_date, substituted = process_forecast_with_fallback(data, target_date)
            except Exception as e:
                st.error(f"Forecast processing error: {e}")
                weather = None; used_date = target_date; substituted = False
            if not weather:
                # Differentiate between API empty window vs city not found vs other
                if not data or 'list' not in data:
                    st.error("No forecast entries returned (possible API issue or invalid response).")
                else:
                    st.warning("⚠️ No forecast data available in returned window.")
            else:
                if substituted:
                    st.info(f"Selected date has no forecast points. Showing closest available forecast for {used_date} instead.")
                with cols[1]:
                    # We'll inject summary & share buttons into the same card after computing summary
                    pass
                try:
                    # Use month/year from the used date (fallback aware)
                    used_dt_obj = datetime.datetime.strptime(used_date, "%Y-%m-%d")
                    hist = fetch_nasa_power_monthly_averages(city, used_dt_obj.year, used_dt_obj.month)
                except Exception as e:
                    hist = None
                    st.error(f"NASA POWER error: {e}")
                show_result(city, used_date, weather)
                if hist:
                    rain_prob = 0
                    if weather['total_rain'] > 5:
                        rain_prob = 90
                    elif weather['total_rain'] > 0:
                        rain_prob = 70
                    else:
                        rain_prob = 0
                    wind_speed = weather.get('avg_wind', 10)
                    forecast_input = {
                        'rain_probability': rain_prob,
                        'temp': weather['avg_temp'],
                        'humidity': weather['avg_humidity'],
                        'wind_speed': wind_speed
                    }
                    historical_input = {
                        'avg_rainfall_mm': hist['avg_rainfall_mm'],
                        'avg_temp_c': hist['avg_temperature_c']
                    }
                    result = parade_suitability_score(forecast_input, historical_input)
                    suggestion = get_event_suggestion(forecast_input)
                    render_suitability_card(result['score'], result['message'], suggestion,
                                           condition_emoji=weather.get('condition_emoji'),
                                           condition_desc=weather.get('condition_desc'))
                    # Build AI summary
                    summary = ai_summarize({
                        "temp": weather['avg_temp'],
                        "humidity": weather['avg_humidity'],
                        "wind": weather['avg_wind'],
                        "rain": weather['total_rain']
                    })
                    # Minimal share text: key metrics + single summary line
                    concise_summary = summary  # single summary sentence
                    # Simple share/copy container (no editing, minimal JS)
                    # (Legacy light forecast card removed; summary now integrated into themed purple panel below.)

                # --- 5-Day Weather Forecast Cards ---
                st.markdown("""
<style>
.forecast-grid { display:grid; gap:1rem; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); margin-top:1.2rem; }
.purple-forecast-card { background:#5d5488; color:#fff; border-radius:26px; padding:1.05rem .9rem .95rem; position:relative; box-shadow:0 6px 18px -4px rgba(0,0,0,0.45); font-size:.8rem; line-height:1.25; }
.purple-forecast-card h4 { margin:0 0 .4rem; font-size:.78rem; font-weight:700; letter-spacing:.5px; text-align:center; }
.purple-forecast-card .metric { display:flex; justify-content:space-between; font-size:.72rem; margin:.15rem 0; }
.purple-forecast-card .cond { text-align:center; font-size:.85rem; margin-bottom:.25rem; }
.today-forecast-wrapper { background:#6b6299; color:#fff; border-radius:30px; padding:1.3rem 1.4rem 1.2rem; margin:1.4rem 0 0; box-shadow:0 10px 26px -6px rgba(0,0,0,.55); }
.today-forecast-wrapper h3 { margin:0 0 .55rem; text-align:center; font-size:1.05rem; font-weight:700; }
.today-forecast-wrapper .summary { font-size:.72rem; text-align:center; line-height:1.35; }
.today-forecast-wrapper .metrics { font-size:.7rem; display:flex; flex-wrap:wrap; gap:.6rem; justify-content:center; margin:0 0 .6rem; }
.today-forecast-wrapper .metrics span { background:rgba(255,255,255,0.12); padding:.4rem .55rem; border-radius:14px; display:flex; align-items:center; gap:.25rem; }
</style>
""", unsafe_allow_html=True)
                # Replace earlier forecast_simple_card injection with themed container (reuse concise summary if available)
                if 'concise_summary' in locals():
                    st.markdown(f"""
                    <div class='today-forecast-wrapper'>
                        <h3>Today's Forecast {weather.get('condition_emoji','')} {weather.get('condition','')}</h3>
                        <div class='metrics'>
                            <span>🌡️ {weather['avg_temp']:.1f}°C</span>
                            <span>💧 {weather['avg_humidity']:.0f}%</span>
                            <span>🌬️ {weather['avg_wind']:.1f} m/s</span>
                            <span>🌧️ {weather['total_rain']:.1f} mm</span>
                            <span>🎯 Score {result['score']}/100</span>
                        </div>
                        <div class='summary'>{html.escape(concise_summary)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("<h3 style='margin:1.4rem 0 .4rem;'>🗓️ 5-Day Forecast</h3>", unsafe_allow_html=True)
                forecast_list = data.get("list", [])
                daily = {}
                for entry in forecast_list:
                    date_str = entry["dt_txt"].split()[0]
                    if date_str not in daily:
                        daily[date_str] = {
                            "temps": [], "humidity": [], "wind": [], "rain": [], "conditions": [], "phases": []
                        }
                    daily[date_str]["temps"].append(entry["main"]["temp"])
                    daily[date_str]["humidity"].append(entry["main"]["humidity"])
                    daily[date_str]["wind"].append(entry["wind"]["speed"])
                    rain_val = entry.get("rain", {}).get("3h", 0)
                    daily[date_str]["rain"].append(rain_val)
                    weather_obj = (entry.get('weather') or [{}])[0]
                    cond_main = weather_obj.get('main','Clear')
                    icon_code = weather_obj.get('icon','')  # e.g. 10d, 01n
                    is_day = icon_code.endswith('d') if icon_code else True
                    phase = 'day' if is_day else 'night'
                    daily[date_str]["conditions"].append(cond_main)
                    daily[date_str]["phases"].append(phase)
                # Only show next 5 days
                days = list(daily.keys())[:5]
                rows = []
                from utils.helpers import WEATHER_EMOJI_MAP
                for d in days:
                    temps = daily[d]["temps"]
                    humidity = daily[d]["humidity"]
                    wind = daily[d]["wind"]
                    rain = daily[d]["rain"]
                    conds = daily[d]["conditions"]
                    phases = daily[d]["phases"]
                    if conds:
                        # frequency of (condition, phase) to distinguish day/night if needed
                        freq = {}
                        for c, ph in zip(conds, phases):
                            key = (c, ph)
                            freq[key] = freq.get(key,0)+1
                        dominant_pair = sorted(freq.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))[0][0]
                        dominant, dom_phase = dominant_pair
                    else:
                        dominant, dom_phase = 'Clear', 'day'
                    emoji = WEATHER_EMOJI_MAP.get((dominant, dom_phase), WEATHER_EMOJI_MAP.get((dominant,'day'), '☀️'))
                    rows.append({
                        "Date": d,
                        "Cond": f"{emoji} {dominant}",
                        "Avg Temp (°C)": round(sum(temps)/len(temps), 1),
                        "Avg Humidity (%)": round(sum(humidity)/len(humidity), 1),
                        "Avg Wind (m/s)": round(sum(wind)/len(wind), 1),
                        "Total Rain (mm)": round(sum(rain), 1)
                    })
                # Render cards via helper for consistent formatting
                from utils.forecast_cards import render_forecast_cards
                render_forecast_cards(rows)
            # --- Pollution Stats Section ---
            try:
                pollution_data = get_pollution_stats(city)
                render_pollution_stats(city, pollution_data)
            except Exception as e:
                st.error(f"Pollution API error: {e}")

# --- NASA POWER Historical Monthly Averages Section ---
if active_page == 'insights':
    show_hist, month_hist, year_hist = render_nasa_section(city, date)
    if show_hist:
        if not city:
            st.error("⚠️ Please enter a city name")
        else:
            with st.spinner("Fetching NASA POWER data..."):
                try:
                    result = fetch_nasa_power_monthly_averages(city, int(year_hist), int(month_hist))
                    render_nasa_results(city, month_hist, year_hist, result)
                except Exception as e:
                    st.error(f"Failed to fetch NASA POWER data: {e}")

# --- Unified Map Panel ---
if active_page == 'home':
    render_map_section()

# --- Climate Change Insight Section ---
# Climate section specific minimal overrides (retain risk message styling)
st.markdown("""
<style>
.risk-msg { font-size:0.85rem; font-weight:600; margin-top:0.9rem; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=3600)
def _climate_multi_year(city_name: str, month: int, start_year: int, end_year: int):
    """Fetch monthly NASA POWER averages for a range of years and aggregate.
    Returns DataFrame with Year, Rainfall(mm/day), Temp(°C) and the averaged metrics."""
    records = []
    for yr in range(start_year, end_year+1):
        try:
            res = fetch_nasa_power_monthly_averages(city_name, yr, month)
            if not res:
                continue
            # Assuming existing helper returns daily average rainfall (mm) and avg temp
            records.append({
                'Year': yr,
                'Rainfall(mm/day)': res.get('avg_rainfall_mm'),
                'Temp(°C)': res.get('avg_temperature_c')
            })
        except Exception:
            continue
    if not records:
        return pd.DataFrame(), None, None
    df = pd.DataFrame(records).dropna()
    if df.empty:
        return df, None, None
    return df, df['Rainfall(mm/day)'].mean(), df['Temp(°C)'].mean()

if active_page == 'report':
    with st.expander("🌍 Climate Change Insight", expanded=True):
        if not city:
            st.info("Enter a city above to view climate change insight.")
        else:
            insight_month = date.month
            # --- Custom Period Selection ---
            st.markdown("<div style='font-size:0.8rem; color:#475569; margin-bottom:0.4rem;'>Choose historical and recent periods for comparison (min span 5 years, non-overlapping).</div>", unsafe_allow_html=True)
            pcol1, pcol2, pcol3, pcol4 = st.columns(4)
            with pcol1:
                hist_start = st.number_input("Hist Start", min_value=1950, max_value=2090, value=1985, step=1)
            with pcol2:
                hist_end = st.number_input("Hist End", min_value=1950, max_value=2090, value=2000, step=1)
            with pcol3:
                recent_start = st.number_input("Recent Start", min_value=1950, max_value=2090, value=2015, step=1)
            with pcol4:
                recent_end = st.number_input("Recent End", min_value=1950, max_value=2090, value=2025, step=1)

            # Validate
            valid = True
            err_msgs = []
            if hist_start > hist_end:
                valid = False; err_msgs.append("Historical start must be <= end")
            if recent_start > recent_end:
                valid = False; err_msgs.append("Recent start must be <= end")
            if (hist_end - hist_start) < 4:
                valid = False; err_msgs.append("Historical span must be at least 5 years")
            if (recent_end - recent_start) < 4:
                valid = False; err_msgs.append("Recent span must be at least 5 years")
            if not (recent_start > hist_end):
                err_msgs.append("Recent period should start after historical period ends to avoid overlap")
            if err_msgs:
                for m in err_msgs:
                    st.warning(m)
            if valid and not err_msgs:
                hist_df, hist_rain_avg, hist_temp_avg = _climate_multi_year(city, insight_month, int(hist_start), int(hist_end))
                recent_df, recent_rain_avg, recent_temp_avg = _climate_multi_year(city, insight_month, int(recent_start), int(recent_end))
            else:
                hist_df = recent_df = pd.DataFrame()
            if (hist_df is None or hist_df.empty) or (recent_df is None or recent_df.empty):
                st.warning("Climate data not sufficient for comparison.")
            else:
                # Combine for chart
                chart_df = pd.concat([hist_df, recent_df]).drop_duplicates('Year').sort_values('Year')
                st.markdown(f"<div class='astro-card' style='margin-top:1.1rem;'>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='margin:0 0 .4rem;'>Climate Insight – {city.title()} ({calendar.month_name[insight_month]})</h3>", unsafe_allow_html=True)
                st.markdown("<p class='sub' style='margin:0 0 1rem;font-size:0.72rem;'>Monthly precipitation & temperature comparison across custom historical vs recent periods with anomalies and AI context.</p>", unsafe_allow_html=True)

                # Anomaly percentages (recent vs historical)
                rain_delta_abs = recent_rain_avg - hist_rain_avg
                rain_delta_pct = (rain_delta_abs / hist_rain_avg * 100) if hist_rain_avg else 0
                temp_delta_abs = recent_temp_avg - hist_temp_avg
                temp_delta_pct = (temp_delta_abs / hist_temp_avg * 100) if hist_temp_avg else 0

                period_label_hist = f"{int(hist_start)}–{int(hist_end)}"
                period_label_recent = f"{int(recent_start)}–{int(recent_end)}"
                colA, colB, colC, colD = st.columns(4)
                colA.metric(f"{period_label_hist} Rain", f"{hist_rain_avg:.2f} mm/d")
                colB.metric(f"{period_label_recent} Rain", f"{recent_rain_avg:.2f} mm/d", delta=f"{rain_delta_abs:+.2f} ({rain_delta_pct:+.1f}%)")
                colC.metric(f"{period_label_hist} Temp", f"{hist_temp_avg:.1f} °C")
                colD.metric(f"{period_label_recent} Temp", f"{recent_temp_avg:.1f} °C", delta=f"{temp_delta_abs:+.1f} ({temp_delta_pct:+.1f}%)")

                # Risk evaluation based on rainfall + temp change
                rain_change_ratio = (recent_rain_avg - hist_rain_avg) / hist_rain_avg if hist_rain_avg else 0
                temp_change = recent_temp_avg - hist_temp_avg if hist_temp_avg else 0
                if rain_change_ratio > 0.5:
                    risk_note = f"🚨 Rainfall increased by {rain_change_ratio*100:.0f}%; higher precipitation risk for events."
                elif rain_change_ratio < -0.2:
                    risk_note = f"🌿 Rainfall decreased by {abs(rain_change_ratio)*100:.0f}%; slightly lower rain risk."
                else:
                    risk_note = "✅ Rainfall change is moderate." 
                if temp_change > 1.5:
                    temp_note = f"🔥 Temp up {temp_change:.1f}°C – added heat stress potential."
                elif temp_change < -1:
                    temp_note = f"❄️ Temp down {abs(temp_change):.1f}°C – cooler conditions trend." 
                else:
                    temp_note = "🌡️ Temperature shift modest." 
                st.markdown(f"<div class='risk-msg'>{risk_note}<br>{temp_note}</div>", unsafe_allow_html=True)

                # Confidence: years actually fetched vs expected span
                expected_hist_years = (int(hist_end) - int(hist_start) + 1)
                expected_recent_years = (int(recent_end) - int(recent_start) + 1)
                actual_hist_years = len(hist_df)
                actual_recent_years = len(recent_df)
                def conf_label(actual, expected):
                    if expected == 0:
                        return "n/a"
                    ratio = actual / expected
                    if ratio >= 0.8:
                        return "High"
                    if ratio >= 0.5:
                        return "Moderate"
                    return "Low"
                confidence_overall = min(actual_hist_years/expected_hist_years if expected_hist_years else 0,
                                          actual_recent_years/expected_recent_years if expected_recent_years else 0)
                qual = "High" if confidence_overall >= 0.8 else ("Moderate" if confidence_overall >= 0.5 else "Low")
                st.caption(f"Data Confidence: {qual} (Hist {actual_hist_years}/{expected_hist_years} yrs; Recent {actual_recent_years}/{expected_recent_years} yrs)")

                # Dual-axis Plotly chart
                try:
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=chart_df['Year'], y=chart_df['Rainfall(mm/day)'], name='Rainfall (mm/day)', marker_color='#4f8cff', yaxis='y'))
                    fig.add_trace(go.Scatter(x=chart_df['Year'], y=chart_df['Temp(°C)'], name='Temp (°C)', mode='lines+markers', line=dict(color='#ff7f0e', width=2), yaxis='y2'))
                    fig.update_layout(
                        height=320,
                        margin=dict(l=50,r=50,t=30,b=40),
                        legend=dict(orientation='h', y=-0.2),
                        barmode='group',
                        template='plotly_white',
                        xaxis=dict(title='Year', tickmode='linear', dtick=2),
                        yaxis=dict(title='Rainfall (mm/day)', showgrid=True, gridcolor='#e2e8f0'),
                        yaxis2=dict(title='Temperature (°C)', overlaying='y', side='right')
                    )
                    st.plotly_chart(fig, width='stretch')
                except Exception as e:
                    st.warning(f"Plotly chart error: {e}")
                # AI Climate Commentary
                if 'climate_ai_comment' not in st.session_state:
                    st.session_state['climate_ai_comment'] = None
                ai_cols = st.columns([1,3])
                with ai_cols[0]:
                    if is_openai_configured() and st.button("AI Commentary", help="Generate AI summary of climate trends"):
                        try:
                            # Build concise CSV-like context
                            sample_tail = chart_df.tail(10)
                            ctx = sample_tail.to_csv(index=False)
                            prompt = textwrap.dedent(f"""
                            Provide a concise (<=120 words) climate trend commentary for {city.title()} for month {calendar.month_name[insight_month]}. Highlight rainfall and temperature direction, magnitude (% and °C), and event planning implications. Data confidence is {qual}. Data (recent vs historical):\nRain delta {rain_delta_abs:+.2f} mm/day ({rain_delta_pct:+.1f}%), Temp delta {temp_delta_abs:+.1f} °C ({temp_delta_pct:+.1f}%).\nRecent period {period_label_recent} vs historical {period_label_hist}.\nRecent tail data:\n{ctx}
                            """)
                            ai_resp = oa_answer("Climate trend commentary", prompt)
                            st.session_state['climate_ai_comment'] = ai_resp
                        except Exception as e:
                            st.warning(f"AI commentary failed: {e}")
                if st.session_state.get('climate_ai_comment'):
                    st.markdown(f"<div style='margin-top:0.5rem; padding:0.75rem 0.9rem; background:#f1f5f9; border-radius:12px; font-size:0.8rem; line-height:1.35;'><b>AI Climate Commentary:</b><br>{html.escape(st.session_state['climate_ai_comment'])}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

# (Map FAB removed per request)

# Workaround: Use a button element rendered via empty placeholder to toggle (since JS can't call Python directly here)
toggle_col = st.empty()
if toggle_col.button("", key="hidden_toggle_button", help="internal", on_click=lambda: st.session_state.update(show_chat=not st.session_state['show_chat'])):
    pass

# Display chat panel if toggled
if st.session_state['show_chat']:
    with st.container():
        st.markdown("<div class='chat-panel'>", unsafe_allow_html=True)
        on = is_openai_configured()
        badge = f"<span style='background:{'#16a34a' if on else '#64748b'}; color:#fff; padding:2px 8px; border-radius:12px; font-size:0.65rem; font-weight:600;'>{'AI OpenAI' if on else 'AI OFF'}</span>"
        st.markdown(f"""
            <div class='chat-header'>AI Weather Assistant {badge}
                <span class='chat-close' onClick=\"window.parent.postMessage({{type:'chat_toggle_py'}},'*')\">✕</span>
            </div>
            <div style='font-size:0.70rem; margin-bottom:4px; color:#475569;'>
                Ask about current or upcoming weather. Examples:
                <em>'Rain tomorrow in London?'</em> • <em>'Compare temp Delhi vs Mumbai'</em>
            </div>
            """, unsafe_allow_html=True)
        if not on:
            st.warning("OpenAI not configured. Add OPENAI_API_KEY to .streamlit/secrets.toml")
        # Messages
        msgs_html = [f"<div class='chat-msg-{m['role']}'>{m['text']}</div>" for m in st.session_state['chat_messages']]
        st.markdown(f"<div class='chat-messages'>{''.join(msgs_html) if msgs_html else '<div style=\"font-size:0.75rem;color:#64748b;\">No messages yet. Ask a weather question.</div>'}</div>", unsafe_allow_html=True)
        with st.form(key='chat_form', clear_on_submit=True):
            user_q = st.text_area("Your question", height=70, key='chat_input')
            submitted = st.form_submit_button("Send")
        if submitted and user_q.strip():
            st.session_state['chat_messages'].append({'role':'user','text': user_q.strip()})
            ctx_parts = []
            if 'weather' in locals() and weather:
                ctx_parts.append(f"Forecast target date metrics: temp {weather['avg_temp']:.1f}C, humidity {weather['avg_humidity']:.0f}%, wind {weather['avg_wind']:.1f} m/s, rain {weather['total_rain']:.1f} mm")
            if city:
                ctx_parts.append(f"Current selected city: {city}")
            context = " | ".join(ctx_parts)
            answer = ai_answer(user_q.strip(), context=context)
            st.session_state['chat_messages'].append({'role':'bot','text': answer})
            try:
                st.rerun()
            except AttributeError:
                if hasattr(st, 'experimental_rerun'):
                    st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown(f"""
<div class='astro-footer' id='about'>
    <div style='font-weight:600; letter-spacing:.5px; margin-bottom:.4rem;'>Astrocast</div>
    <div style='margin-bottom:.6rem;'>Weather & climate insights powered by OpenWeather, NASA POWER & optional OpenAI summaries.</div>
    <div style='margin-bottom:.4rem;'>Created for educational & planning purposes – always verify critical event decisions.</div>
    <div>© {datetime.date.today().year} Astrocast • <a href='https://github.com/' target='_blank'>GitHub</a></div>
</div>
""", unsafe_allow_html=True)
