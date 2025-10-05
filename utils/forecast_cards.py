import streamlit as st
from datetime import datetime

def render_forecast_cards(rows: list[dict]):
	"""Render forecast cards given processed daily rows.
	Each row expected keys: Date, Cond, Avg Temp (°C), Avg Humidity (%), Avg Wind (m/s), Total Rain (mm)
	"""
	if not rows:
		return
	cards_html = []
	for r in rows:
		# Parse date -> weekday label
		try:
			dt_obj = datetime.strptime(r['Date'], '%Y-%m-%d')
			day_label = dt_obj.strftime('%a')
		except Exception:
			day_label = r['Date']
		wind_val = f"{r['Avg Wind (m/s)']:.1f} m/s"
		rain_raw = r['Total Rain (mm)']
		rain_val = ("—" if rain_raw == 0 else f"{rain_raw:.1f} mm")
		temp_val = f"{r['Avg Temp (°C)']:.1f}°C"
		hum_val = f"{r['Avg Humidity (%)']:.0f}%"
		cards_html.append(
			f"<div class='purple-forecast-card'><h4>{day_label} <span style='font-weight:400;opacity:.85;font-size:.65rem;'>{r['Date']}</span></h4>"
			f"<div class='cond'>{r['Cond']}</div>"
			f"<div class='metric'><span>Temp</span><span>{temp_val}</span></div>"
			f"<div class='metric'><span>Hum</span><span>{hum_val}</span></div>"
			f"<div class='metric'><span>Wind</span><span>{wind_val}</span></div>"
			f"<div class='metric'><span>Rain</span><span>{rain_val}</span></div>"
			f"</div>"
		)
	st.markdown("<div class='forecast-grid'>" + "".join(cards_html) + "</div>", unsafe_allow_html=True)

