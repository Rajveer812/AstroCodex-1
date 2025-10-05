# 🌦️ Astrocast

Astrocast is an intelligent, dark‑themed weather & climate planning assistant for outdoor events. It blends real-time forecasts, NASA climatology, air quality, geospatial layers, and optional AI commentary—now with a redesigned multi‑page experience (Home, Compare, Past Insights, Weather Report) and shareable forecast cards.

---

## 🚀 Key Features
✅ Multi-page Navigation (Home • Compare • Past Insights • Weather Report)  
✅ City + Date Weather Forecast (5-day window)  
✅ Purple Card UI (Today + 5-day compact cards with icons)  
✅ Parade / Event Suitability Score (0–100)  
✅ AI Weather Summary & Share/Copy (concise)  
✅ Dual-City Weekend Comparison (scores, rain probability, emoji conditions, AI pros/cons)  
✅ NASA POWER Historical Monthly Averages (Past Insights)  
✅ Climate Change Insight (custom periods, anomalies %, dual-axis Plotly chart, AI commentary)  
✅ Air Pollution Metrics (AQI + key pollutants)  
✅ Interactive Map (NASA GIBS layers + OWM metrics + floating 🌍 FAB)  
✅ Floating FABs (🌍 Map access • 🤖 AI Chat toggle)  
✅ Weather Emoji Mapping (day/night aware base support)  

---

## 🛠️ Tech Stack
- Python 3  
- Streamlit (UI)  
- OpenWeatherMap API (Forecast)  
- NASA POWER API (Climatology)  
- OpenAI API (Summaries & Insights)  
- Folium + NASA GIBS (Map Layers)  
- Plotly (Dual-axis climate chart)  

---

## 📂 Project Structure (simplified)
```
AstroCodex/
├─ app.py                 # Main multi-page dispatcher (query-param routing)
├─ requirements.txt       # Dependencies
├─ readme.md
├─ assets/
│   └─ logo.png           # Brand logo
├─ config/                # Settings / API keys
├─ services/              # External API wrappers (weather, nasa, pollution, ai)
├─ ui/                    # UI components (cards, sections, branding, theme, map)
└─ utils/                 # Helpers, scoring, forecast processing, emojis
```


---

## ⚡ Quick Start
1. Clone:
   ```bash
   git clone https://github.com/YOUR_USERNAME/astrocast.git
   cd astrocast
   ```
2. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure API keys (create/modify `config/settings.py` or `.streamlit/secrets.toml`):
   - `OPENWEATHERMAP_API_KEY`
   - (Optional) `OPENAI_API_KEY` for AI summaries/comparisons
4. Run:
   ```bash
   streamlit run app.py
   ```
5. Navigate via top bar or query params, e.g. `?page=compare` or `?page=report`.

### Environment Notes
| Service | Purpose | Required |
|---------|---------|----------|
| OpenWeatherMap | 5-day forecast + pollution | Yes |
| NASA POWER | Climatology & climate insight | Yes |
| OpenAI | Natural language summaries | Optional |
## 🖼 UI Redesign Highlights
| Element | Before | After |
|--------|--------|-------|
| Navigation | Single scroll page | Multi-page (query-param) top nav |
| Forecast | White tables | Purple rounded cards + emoji conditions |
| Sharing | Verbose summary | Concise copy/share buttons |
| Comparison | Basic table | Scored table + AI rationale + fallback date flag |
| Climate | Simple stats | Custom period anomalies + dual-axis chart + AI commentary |
| Map | Separate style | Unified dark theme + astro-card + FAB launch |

Add a screenshot once captured:
`/assets/screenshot_dark_home.png`

👨‍💻 Team
[Rajveer Jain] (BCA Student, Udaipur)
[Kapil Paliwal] (BCA Student, Udaipur)
[Vinisha Vyas] (BCA Student, Udaipur)
[Grishma Saini] (ACCA Student, Udaipur)

NASA Space Apps Challenge 2025 Participant

## 📊 Roadmap Ideas
- 3+ city comparison matrix
- Downloadable PDF / report export
- ML-based localized rain probability refinement
- Multi-language support
- User accounts & saved locations
- Event-type specific scoring profiles
- Geospatial severe weather alert overlay

Copy code
---

## � Dev Tips
- Query param routing: `?page=home|compare|insights|report`
- Add `map=1` param on home to auto-open map toggle (future enhancement can auto-open).
- All styling tokens live in `ui/theme.py` (CSS variables) for quick theming.
- Branding & nav in `ui/branding.py`.

## 🪪 License
See `LICENSE` file.