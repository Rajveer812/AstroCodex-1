import streamlit as st

THEME_CSS = """
<style>
:root {
	--color-bg: #0f172a;
	--color-bg-alt: #1e293b;
	--color-surface: #16243a;
	--color-card: #1e2d44;
	--color-card-accent: #233650;
	--color-border: #2c425e;
	--color-accent: #4f8cff;
	--color-accent-grad: linear-gradient(90deg,#4f8cff,#6f6fff);
	--color-accent-soft: #4f8cff22;
	--color-text: #e2e8f0;
	--color-text-dim: #94a3b8;
	--color-danger: #dc2626;
	--color-success: #16a34a;
	--color-warn: #f59e0b;
	--radius-sm: 6px;
	--radius-md: 12px;
	--radius-lg: 18px;
	--shadow-sm: 0 2px 4px rgba(0,0,0,0.4);
	--shadow-md: 0 4px 12px rgba(0,0,0,0.35);
	--shadow-lg: 0 8px 28px rgba(0,0,0,0.35);
	--trans-fast: 120ms ease;
	--max-width: 1280px;
	--font-stack: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', Arial, sans-serif;
	--nav-height: 62px;
	--nav-offset: 48px; /* distance from very top before nav starts (increased) */
}

html, body, .main, .block-container { background: var(--color-bg) !important; }
/* Add top padding equal to nav height + small gap so first element not hidden */
.block-container { padding-top: calc(var(--nav-offset) + var(--nav-height) + 20px) !important; max-width: var(--max-width); }

* { font-family: var(--font-stack); }

/* Navigation */
.astro-nav { position:fixed; top:var(--nav-offset); left:0; right:0; height:var(--nav-height); z-index:1100; backdrop-filter: blur(12px); background:rgba(15,23,42,0.9); border-bottom:1px solid var(--color-border); }
.astro-nav-inner { display:flex; align-items:center; gap:2.2rem; padding:0.85rem 1.6rem; max-width: var(--max-width); margin:0 auto; }
.astro-brand { font-size:1.35rem; font-weight:700; background:var(--color-accent-grad); -webkit-background-clip:text; color:transparent; letter-spacing:.5px; }
.astro-links { display:flex; gap:1.4rem; }
.astro-links a { color: var(--color-text-dim); text-decoration:none; font-size:0.9rem; font-weight:500; letter-spacing:.5px; position:relative; padding:.35rem .2rem; }
.astro-links a:hover, .astro-links a:focus { color: var(--color-text); }
.astro-links a.active:after { content:""; position:absolute; left:0; bottom:-4px; height:2px; width:100%; background:var(--color-accent); border-radius:2px; }

/* Active City Badge */
.city-badge { background:var(--color-card-accent); color:var(--color-text-dim); padding:0.35rem 0.7rem; border-radius:18px; font-size:0.7rem; letter-spacing:.5px; display:flex; align-items:center; gap:.35rem; border:1px solid var(--color-border); }
.city-badge span { max-width:140px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.city-badge strong { color:var(--color-text); font-weight:600; }

/* Nav Chat Button */
.nav-chat-btn { display:flex; align-items:center; justify-content:center; padding:0 .9rem; height:38px; border-radius:19px; font-size:13px; font-weight:600; gap:.4rem; line-height:1; cursor:pointer; background:transparent; border:1px solid var(--color-border); color:var(--color-text-dim); transition:var(--trans-fast); }
.nav-chat-btn:hover, .nav-chat-btn:focus { color:var(--color-text); border-color:var(--color-accent); }
.nav-chat-btn[aria-pressed='true'] { background:var(--color-accent-grad); color:#fff; border:1px solid var(--color-accent); box-shadow:var(--shadow-sm); }



/* Hero */
.hero { padding:4.2rem 0 2.8rem; text-align:center; }
.hero h1 { font-size:3.1rem; line-height:1.1; margin:0; background:var(--color-accent-grad); -webkit-background-clip:text; color:transparent; font-weight:800; }
.hero p { font-size:1.05rem; color:var(--color-text-dim); margin:.9rem auto 1.4rem; max-width:760px; }
.hero-cta { display:flex; justify-content:center; gap:1rem; }
.hero-cta button { background:var(--color-accent-grad); border:none; padding:.85rem 1.4rem; border-radius:var(--radius-md); color:#fff; font-weight:600; font-size:0.95rem; cursor:pointer; box-shadow:var(--shadow-sm); transition:var(--trans-fast); }
.hero-cta button:hover { filter:brightness(1.15); }

/* Cards */
.astro-card { background:var(--color-card); border:1px solid var(--color-border); border-radius:var(--radius-lg); padding:1.3rem 1.25rem 1.15rem; box-shadow:var(--shadow-sm); position:relative; transition:var(--trans-fast); }
.astro-card:hover { border-color: var(--color-accent); box-shadow:var(--shadow-md); }
.astro-card h3 { margin:0 0 .5rem; font-size:1.05rem; font-weight:600; color:var(--color-text); }
.astro-card small { color:var(--color-text-dim); }

/* Sections */
section.astro-section { padding:2.4rem 0 2.2rem; border-top:1px solid var(--color-border); }
section.astro-section:first-of-type { border-top:none; }
section.astro-section .section-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:1.1rem; }
section.astro-section h2 { margin:0; font-size:1.55rem; font-weight:700; letter-spacing:.5px; color:var(--color-text); }
section.astro-section p.sub { margin:.35rem 0 0; font-size:0.88rem; color:var(--color-text-dim); }

/* Tables override */
div[data-testid='stDataFrame'] { border-radius:var(--radius-md); overflow:hidden; border:1px solid var(--color-border); }

/* Footer */
.astro-footer { margin-top:3rem; padding:2.5rem 0 3rem; border-top:1px solid var(--color-border); text-align:center; color:var(--color-text-dim); font-size:0.75rem; }
.astro-footer a { color:var(--color-accent); text-decoration:none; }

/* Scroll To Top */
#scrollTopBtn { position:fixed; right:18px; bottom:22px; width:42px; height:42px; border-radius:50%; border:1px solid var(--color-border); background:var(--color-card-accent); color:var(--color-text); cursor:pointer; font-size:1.1rem; display:none; align-items:center; justify-content:center; box-shadow:var(--shadow-sm); }
#scrollTopBtn:hover { background:var(--color-accent); color:#fff; }

/* Utility */
.grid { display:grid; gap:1.1rem; }
.grid.cols-2 { grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); }
.metrics-inline { display:flex; gap:1.4rem; flex-wrap:wrap; }
.badge { background:var(--color-card-accent); padding:.35rem .6rem; border-radius:var(--radius-sm); font-size:0.65rem; letter-spacing:.5px; text-transform:uppercase; color:var(--color-text-dim); }

</style>
<script>
document.addEventListener('DOMContentLoaded', ()=>{
	const links = Array.from(document.querySelectorAll('.astro-links a'));
	// Only links that point to in-page hash sections participate in scroll spy
	const hashLinks = links.filter(l => l.getAttribute('href')?.startsWith('#'));
	const activate = ()=>{
		if(!hashLinks.length) return; // nothing to do if no hash links
		const y = window.scrollY + 120;
		let current;
		document.querySelectorAll('section.astro-section').forEach(sec=>{
			if(sec.offsetTop <= y) current = sec.getAttribute('id');
		});
		hashLinks.forEach(l=>{
			l.classList.toggle('active', l.getAttribute('href') === '#' + current);
		});
	};
	window.addEventListener('scroll', activate, {passive:true});
	activate();
	// scroll top button
	const btn = document.getElementById('scrollTopBtn');
	if(btn){
		window.addEventListener('scroll', ()=>{ btn.style.display = window.scrollY>400 ? 'flex':'none'; });
		btn.addEventListener('click', ()=>window.scrollTo({top:0,behavior:'smooth'}));
	}
});
</script>
"""

def inject_theme():
		st.markdown(THEME_CSS, unsafe_allow_html=True)
