import os, base64, streamlit as st

def get_logo_b64(path: str = 'assets/logo.png', fallback: str | None = None) -> str:
    fallback_data = fallback or (
        "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAQAAAAAYLlVAAAACXBIWXMAAAsTAAALEwEAmpwYAAABcElEQVR4nO2VwUoDQRBFX2sRFpY2FhZ2FrY2NrYW9hYWXgkrWytpY2/gN7C0ErGwsbGxsrCy8jBoGBkJBkP+nMjJmZ3Z2ZvJvJ7szuzszwCVqGkSikT1AQ7gG1gC6wAq4E8cQ7YAs8BI2AkvMf0I3c+AXuA0+Yk93QmwC4c8yyW8B64AC8wzqYgPR7AOC6mbERm4+H3ht9FN8hq6YgZkA4wBe4Bz7gVNtJ/4c6D4toHZEgE4zD/ADfkGv9QnU5ws5V8t5VEBv4e1nYW8BN6MBZy0RsgPXgIfv5zJHZhMhwGPObADtKf6DThtfmMkqmRJvIC3Jf1aRLUZkQnT1BCpaPBG3GxVDXNjpWpj8XSa1EIVp8JS9Lf6C7lX8l6ipiNZWAPzqpxBMWI58qnEG1t3L8PbQO1isCh1m6tVQA7jwCLYAvgC93gY6gIhgJfkVdYPfp6D9h2H5Dh7ukTJx0DPWhtW0v+n2l/XU47zKo7oBF1pgbJYkNzAAAAAElFTkSuQmCC"
    )
    if os.path.exists(path):
        try:
            with open(path,'rb') as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return fallback_data
    return fallback_data

def render_nav(active_page: str = 'home'):
    """Render top navigation with query-param based routing and AI chat button."""
    # Determine if chat is active (open) from query params for aria-pressed state
    chat_active = False
    try:
        qp = st.query_params if hasattr(st, 'query_params') else st.experimental_get_query_params()
        # qp may behave like dict -> handle both forms
        if isinstance(qp, dict):
            raw = qp.get('chat')
            if isinstance(raw, list):
                chat_active = '1' in raw
            elif isinstance(raw, str):
                chat_active = raw == '1'
        else:
            # mapping-like
            raw = qp.get('chat')
            if isinstance(raw, str):
                chat_active = raw == '1'
    except Exception:
        chat_active = False

    logo_b64 = get_logo_b64()
    links = [
        ("compare", "Compare"),
        ("insights", "Past Insights"),
        ("report", "Weather Report")
    ]
    links_html = []
    for page_key, label in links:
        base = page_key.split('&')[0]
        cls = 'active' if active_page == base else ''
        links_html.append(f"<a href='?page={page_key}' class='{cls}'>{label}</a>")
    brand_link = "<a href='?page=home' style='text-decoration:none;color:inherit;'>Astrocast</a>" if active_page != 'home' else 'Astrocast'
    aria_pressed = 'true' if (active_page == 'home' and chat_active) else 'false'
    st.markdown(f"""
    <nav class='astro-nav'>
      <div class='astro-nav-inner'>
        <div class='astro-brand' style='display:flex;align-items:center;gap:.55rem;'>
          <img src='data:image/png;base64,{logo_b64}' alt='logo' style='height:30px;width:30px;display:block;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.4);background:#0f172a;padding:2px;'>
          <span>{brand_link}</span>
        </div>
        <div class='astro-links'>
          {' '.join(links_html)}
          <button id="navChatBtn" class="nav-chat-btn" aria-label="AI Assistant" aria-pressed="{aria_pressed}" type="button">🤖 <span style='letter-spacing:.5px;'>AI Assistant</span></button>
        </div>
      </div>
    </nav>
    <script>
    document.addEventListener('DOMContentLoaded',()=>{{
      const btn=document.getElementById('navChatBtn');
      if(btn){{
        btn.addEventListener('click',()=>{{
          const url=new URL(window.location.href);
          const isActive = url.searchParams.get('chat')==='1' && url.searchParams.get('page')==='home';
          if(isActive){{
            // toggle off
            url.searchParams.delete('chat');
          }} else {{
            url.searchParams.set('page','home');
            url.searchParams.set('chat','1');
          }}
          window.location.href=url.toString();
        }});
      }}
    }});
    </script>
    """, unsafe_allow_html=True)
