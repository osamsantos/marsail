import streamlit as st
import datetime
import time
import json
from collections import defaultdict

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Escale à Marseille",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --marseille-blue:   #1a3a5c;
    --sea:              #2e7dbd;
    --sun:              #f5a623;
    --coral:            #e8604c;
    --sand:             #f7f0e6;
    --mint:             #d4ede8;
    --text:             #1a1a2e;
    --muted:            #6b7280;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--sand) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}

[data-testid="stSidebar"] {
    background: var(--marseille-blue) !important;
    color: white !important;
}
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stRadio label { color: white !important; }

h1, h2, h3 { font-family: 'Playfair Display', serif; }

/* Hero banner */
.hero {
    background: linear-gradient(135deg, var(--marseille-blue) 0%, var(--sea) 60%, var(--coral) 100%);
    border-radius: 18px;
    padding: 2.5rem 2rem 2rem;
    margin-bottom: 1.8rem;
    color: white;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "⚓";
    font-size: 9rem;
    position: absolute;
    right: 2rem; top: -1rem;
    opacity: 0.08;
    line-height: 1;
}
.hero h1 { font-size: 2.4rem; margin: 0 0 0.3rem; letter-spacing: -0.5px; }
.hero p  { margin: 0; opacity: 0.88; font-size: 1.05rem; font-weight: 300; }

/* Cards */
.card {
    background: white;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 14px rgba(30,60,100,0.07);
    border-left: 4px solid var(--sun);
}
.card-blue  { border-left-color: var(--sea); }
.card-coral { border-left-color: var(--coral); }
.card-mint  { border-left-color: #3aab8a; }

/* Timer display */
.timer-box {
    background: var(--marseille-blue);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    color: white;
    margin-bottom: 1rem;
}
.timer-digits {
    font-family: 'Playfair Display', serif;
    font-size: 3.8rem;
    letter-spacing: 4px;
    line-height: 1;
    margin: 0.5rem 0;
}
.timer-label { font-size: 0.85rem; opacity: 0.7; letter-spacing: 2px; text-transform: uppercase; }

/* Itinerary step */
.step {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    align-items: flex-start;
}
.step-num {
    background: var(--sun);
    color: var(--marseille-blue);
    border-radius: 50%;
    width: 2rem; height: 2rem;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; flex-shrink: 0; font-size: 0.9rem;
}
.step-body { flex: 1; }
.step-title { font-weight: 600; margin-bottom: 0.2rem; }
.step-desc  { font-size: 0.88rem; color: var(--muted); }

/* Flag + feedback row */
.feedback-row {
    background: white;
    border-radius: 10px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.6rem;
    box-shadow: 0 1px 8px rgba(0,0,0,0.05);
    display: flex; gap: 0.8rem;
}

/* Tag pills */
.tag {
    display: inline-block;
    background: var(--mint);
    color: var(--marseille-blue);
    border-radius: 20px;
    padding: 0.2rem 0.75rem;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 0.15rem;
}

/* Stars */
.stars { color: var(--sun); font-size: 1.1rem; }

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: var(--marseille-blue);
    margin-bottom: 0.3rem;
}
.section-sub { color: var(--muted); font-size: 0.9rem; margin-bottom: 1.2rem; }

hr.fancy {
    border: none;
    height: 2px;
    background: linear-gradient(to right, var(--sun), transparent);
    margin: 1.5rem 0;
}

/* Streamlit widget overrides */
div[data-baseweb="select"] > div { border-radius: 10px !important; }
.stTextInput > div > input, .stTextArea textarea {
    border-radius: 10px !important;
    border-color: #d1d5db !important;
}
.stButton > button {
    background: var(--marseille-blue) !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 0.55rem 1.4rem !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stButton > button:hover {
    background: var(--sea) !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Session state defaults ──────────────────────────────────────────────────
def _init():
    defaults = {
        "page": "🏠 Découvrir",
        "profile": None,           # completed questionnaire result
        "itinerary": None,         # generated itinerary
        "departure_dt": None,      # datetime of cruise departure
        "feedbacks": [],           # list of dicts
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
_init()

# ─── Data ───────────────────────────────────────────────────────────────────
ITINERARIES = {
    ("culture", "half"): [
        {"place": "Vieux-Port", "emoji": "⛵", "duration": "30 min",
         "desc": "Start at the iconic old harbour – soak in the atmosphere and grab a café."},
        {"place": "Musée d'Histoire de Marseille", "emoji": "🏛️", "duration": "1 h",
         "desc": "Discover 2,600 years of history right in the city centre."},
        {"place": "La Canebière", "emoji": "🛍️", "duration": "30 min",
         "desc": "Stroll the famous boulevard and browse local boutiques."},
        {"place": "Noailles Market", "emoji": "🌶️", "duration": "30 min",
         "desc": "The spice-filled 'belly of Marseille' – vibrant and authentic."},
    ],
    ("culture", "full"): [
        {"place": "Vieux-Port", "emoji": "⛵", "duration": "45 min",
         "desc": "Start at the iconic harbour at sunrise for the best light."},
        {"place": "MuCEM", "emoji": "🏛️", "duration": "1 h 30",
         "desc": "World-class museum of Mediterranean civilisations – stunning architecture."},
        {"place": "Le Panier", "emoji": "🎨", "duration": "1 h",
         "desc": "The oldest neighbourhood: colourful streets, art galleries, craft shops."},
        {"place": "Noailles Market", "emoji": "🌶️", "duration": "45 min",
         "desc": "Lunch break at this multicultural spice market."},
        {"place": "Notre-Dame de la Garde", "emoji": "⛪", "duration": "1 h",
         "desc": "The iconic basilica with panoramic views over the whole city."},
        {"place": "Cours Julien", "emoji": "🎵", "duration": "45 min",
         "desc": "Hip neighbourhood – street art, vintage shops and evening aperitif."},
    ],
    ("nature", "half"): [
        {"place": "Plage des Catalans", "emoji": "🏖️", "duration": "1 h",
         "desc": "Closest beach to the port – perfect for a morning dip."},
        {"place": "Corniche Kennedy", "emoji": "🌊", "duration": "45 min",
         "desc": "Scenic coastal promenade with breathtaking sea views."},
        {"place": "Parc du Pharo", "emoji": "🌳", "duration": "30 min",
         "desc": "Peaceful gardens with a panorama over the Vieux-Port."},
    ],
    ("nature", "full"): [
        {"place": "Plage des Catalans", "emoji": "🏖️", "duration": "1 h",
         "desc": "Start with an early swim at the city beach."},
        {"place": "Corniche Kennedy", "emoji": "🌊", "duration": "1 h",
         "desc": "Walk the entire coastal promenade – sea spray included."},
        {"place": "Calanques (Sormiou)", "emoji": "🏔️", "duration": "2 h",
         "desc": "Hike to the most accessible calanque – turquoise water, white cliffs."},
        {"place": "Parc du Pharo", "emoji": "🌳", "duration": "45 min",
         "desc": "Wind down in these beautiful hillside gardens."},
        {"place": "Anse des Auffes", "emoji": "🐟", "duration": "45 min",
         "desc": "Tiny fishing village hidden beneath the Corniche – pure Marseille."},
    ],
    ("food", "half"): [
        {"place": "Vieux-Port Fish Market", "emoji": "🐠", "duration": "45 min",
         "desc": "Fishermen sell their morning catch directly – arrive early!"},
        {"place": "Noailles Market", "emoji": "🌶️", "duration": "45 min",
         "desc": "Sample North-African pastries and fresh spices."},
        {"place": "Chez Fonfon", "emoji": "🍲", "duration": "1 h 30",
         "desc": "Legendary bouillabaisse restaurant at the Anse des Auffes."},
    ],
    ("food", "full"): [
        {"place": "Vieux-Port Fish Market", "emoji": "🐠", "duration": "1 h",
         "desc": "Morning fish market – the heart of Marseille's culinary soul."},
        {"place": "Noailles Market", "emoji": "🌶️", "duration": "45 min",
         "desc": "Spices, dried fruits, halva – a feast for the senses."},
        {"place": "La Vieille Charité", "emoji": "☕", "duration": "45 min",
         "desc": "Beautiful baroque courtyard – ideal for a mid-morning coffee."},
        {"place": "Chez Fonfon", "emoji": "🍲", "duration": "1 h 30",
         "desc": "Iconic bouillabaisse restaurant – book ahead if you can."},
        {"place": "Cours Julien", "emoji": "🍦", "duration": "1 h",
         "desc": "Artisan ice cream, craft beer, and the best navettes in the city."},
    ],
    ("shopping", "half"): [
        {"place": "La Canebière", "emoji": "🛍️", "duration": "45 min",
         "desc": "Main shopping boulevard – from chains to local designers."},
        {"place": "Le Panier boutiques", "emoji": "🎁", "duration": "1 h",
         "desc": "Unique Provençal crafts, soaps, and artisan souvenirs."},
        {"place": "Vieux-Port souvenir shops", "emoji": "🧴", "duration": "30 min",
         "desc": "Pick up savon de Marseille and lavender gifts."},
    ],
    ("shopping", "full"): [
        {"place": "La Canebière", "emoji": "🛍️", "duration": "1 h",
         "desc": "Start with the main boulevard."},
        {"place": "Rue Saint-Ferréol", "emoji": "👗", "duration": "1 h",
         "desc": "Marseille's premium fashion street."},
        {"place": "Le Panier boutiques", "emoji": "🎁", "duration": "1 h 30",
         "desc": "Artisan soaps, ceramics, and Provence-inspired gifts."},
        {"place": "Noailles Market", "emoji": "🌶️", "duration": "45 min",
         "desc": "Edible souvenirs – spice blends, preserved lemons, harissa."},
        {"place": "Vieux-Port area", "emoji": "🧴", "duration": "45 min",
         "desc": "Last stop for savon de Marseille and regional delicacies."},
    ],
}

COUNTRIES = [
    "🇺🇸 United States", "🇬🇧 United Kingdom", "🇩🇪 Germany", "🇫🇷 France",
    "🇮🇹 Italy", "🇪🇸 Spain", "🇨🇦 Canada", "🇦🇺 Australia", "🇯🇵 Japan",
    "🇧🇷 Brazil", "🇳🇱 Netherlands", "🇧🇪 Belgium", "🇸🇪 Sweden", "🇳🇴 Norway",
    "🇨🇭 Switzerland", "🇵🇹 Portugal", "🇬🇷 Greece", "🇦🇹 Austria",
    "🇩🇰 Denmark", "🇫🇮 Finland", "🇵🇱 Poland", "🇨🇿 Czech Republic",
    "🇭🇺 Hungary", "🇷🇴 Romania", "🇷🇺 Russia", "🇨🇳 China", "🇮🇳 India",
    "🇲🇽 Mexico", "🇦🇷 Argentina", "🇿🇦 South Africa", "Other"
]

PLACES = [
    "Vieux-Port", "MuCEM", "Le Panier", "Notre-Dame de la Garde",
    "Calanques", "Noailles Market", "Cours Julien", "Corniche Kennedy",
    "Anse des Auffes", "Plage des Catalans", "La Canebière",
    "Château d'If", "Musée d'Histoire", "La Vieille Charité",
]

# ─── Sidebar navigation ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## ⚓ Escale à Marseille")
    st.markdown("<small style='opacity:.6'>Your Marseille layover guide</small>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["🏠 Découvrir", "🗺️ Mon Itinéraire", "⏳ Minuteur Croisière", "💬 Avis & Retours"],
        index=["🏠 Découvrir", "🗺️ Mon Itinéraire", "⏳ Minuteur Croisière", "💬 Avis & Retours"].index(st.session_state.page),
        label_visibility="collapsed",
    )
    st.session_state.page = page
    st.markdown("---")
    st.markdown("<small style='opacity:.5'>Marseille, France 🇫🇷<br>Made for cruise travellers</small>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 – DISCOVER (Questionnaire)
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Découvrir":
    st.markdown("""
    <div class="hero">
        <h1>Bienvenue à Marseille 🌊</h1>
        <p>Your cruise is docked — the city is yours. Tell us your tastes and we'll craft the perfect layover.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="section-title">Tell us about yourself</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Answer a few quick questions so we can suggest the best itinerary for your time ashore.</p>', unsafe_allow_html=True)

    with st.form("questionnaire"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your first name", placeholder="e.g. Maria")
            country = st.selectbox("Where are you from?", COUNTRIES)
        with col2:
            group_size = st.number_input("How many people in your group?", min_value=1, max_value=20, value=2)
            mobility = st.selectbox("Mobility level", ["🚶 Walker – I love exploring on foot",
                                                        "🚌 Mixed – some walking + transport",
                                                        "🚕 Easy – I prefer taxis/bus"])

        st.markdown("<hr class='fancy'>", unsafe_allow_html=True)

        interest = st.radio(
            "What excites you most about Marseille?",
            ["🏛️ Culture & History", "🌊 Nature & Beaches", "🍲 Food & Markets", "🛍️ Shopping"],
            horizontal=True,
        )
        time_avail = st.radio(
            "How much time do you have ashore?",
            ["⏱️ Half day (up to 4 h)", "🌅 Full day (6 h+)"],
            horizontal=True,
        )

        budget = st.select_slider(
            "Approximate budget per person (€)",
            options=["Under 20 €", "20–50 €", "50–100 €", "100 €+"],
            value="20–50 €",
        )

        dietary = st.multiselect(
            "Any dietary preferences? (optional)",
            ["Vegetarian", "Vegan", "Gluten-free", "Halal", "Kosher", "No restriction"],
            default=["No restriction"],
        )

        submitted = st.form_submit_button("✨ Build my itinerary")

    if submitted:
        interest_key = {"🏛️ Culture & History": "culture",
                        "🌊 Nature & Beaches": "nature",
                        "🍲 Food & Markets": "food",
                        "🛍️ Shopping": "shopping"}[interest]
        time_key = "half" if "Half" in time_avail else "full"
        st.session_state.profile = {
            "name": name or "Traveller",
            "country": country,
            "group_size": group_size,
            "mobility": mobility,
            "interest": interest,
            "interest_key": interest_key,
            "time_avail": time_avail,
            "time_key": time_key,
            "budget": budget,
            "dietary": dietary,
        }
        st.session_state.itinerary = ITINERARIES.get((interest_key, time_key), [])
        st.session_state.page = "🗺️ Mon Itinéraire"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 – ITINERARY
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Mon Itinéraire":
    if not st.session_state.profile:
        st.warning("Please complete the questionnaire first!")
        if st.button("Go to questionnaire →"):
            st.session_state.page = "🏠 Découvrir"
            st.rerun()
    else:
        p = st.session_state.profile
        itin = st.session_state.itinerary

        st.markdown(f"""
        <div class="hero">
            <h1>Bonjour, {p['name']}! 🎉</h1>
            <p>Your personalised Marseille itinerary — {p['time_avail']} · {p['interest']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Profile summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class="card card-blue">
                <div style="font-size:0.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px">From</div>
                <div style="font-size:1.1rem;font-weight:600;margin-top:0.2rem">{p['country']}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="card card-blue">
                <div style="font-size:0.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px">Group size</div>
                <div style="font-size:1.1rem;font-weight:600;margin-top:0.2rem">👥 {p['group_size']} people</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="card card-blue">
                <div style="font-size:0.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px">Budget</div>
                <div style="font-size:1.1rem;font-weight:600;margin-top:0.2rem">💶 {p['budget']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<p class="section-title" style="margin-top:1.5rem">Your Marseille Plan</p>', unsafe_allow_html=True)
        st.markdown('<p class="section-sub">Suggested stops in order — take your time between each one.</p>', unsafe_allow_html=True)

        for i, step in enumerate(itin, 1):
            st.markdown(f"""
            <div class="card">
                <div class="step">
                    <div class="step-num">{i}</div>
                    <div class="step-body">
                        <div class="step-title">{step['emoji']} {step['place']} <span style="font-weight:300;color:var(--muted);font-size:0.85rem">— {step['duration']}</span></div>
                        <div class="step-desc">{step['desc']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr class='fancy'>", unsafe_allow_html=True)

        # Practical tips
        st.markdown('<p class="section-title">💡 Practical Tips</p>', unsafe_allow_html=True)
        tips_col1, tips_col2 = st.columns(2)
        with tips_col1:
            st.markdown("""<div class="card card-mint">
                <b>🚌 Getting around</b><br>
                <small>RTM bus lines 83 & 60 link the port to main sites. Taxis are plentiful at the Vieux-Port stand.</small>
            </div>""", unsafe_allow_html=True)
            st.markdown("""<div class="card card-mint">
                <b>💳 Payment</b><br>
                <small>Cards accepted almost everywhere. Carry a little cash for markets.</small>
            </div>""", unsafe_allow_html=True)
        with tips_col2:
            st.markdown("""<div class="card card-mint">
                <b>🌡️ Weather today</b><br>
                <small>Marseille enjoys ~300 sunny days/year. Check the Mistral – a strong N/NW wind can make it cooler.</small>
            </div>""", unsafe_allow_html=True)
            st.markdown("""<div class="card card-mint">
                <b>⚓ Back to port</b><br>
                <small>Allow 20–30 min to return to the cruise terminal from any central location. Don't cut it close!</small>
            </div>""", unsafe_allow_html=True)

        if st.button("⏳ Set my departure timer →"):
            st.session_state.page = "⏳ Minuteur Croisière"
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 – DEPARTURE TIMER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⏳ Minuteur Croisière":
    st.markdown("""
    <div class="hero">
        <h1>⏳ Cruise Departure Timer</h1>
        <p>Set your departure time and never miss your ship. We'll keep you on track.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("timer_form"):
        col1, col2 = st.columns(2)
        with col1:
            dep_date = st.date_input("Departure date", value=datetime.date.today())
        with col2:
            dep_time = st.time_input("Departure time (local Marseille time)",
                                     value=datetime.time(17, 0))
        boarding_buffer = st.slider(
            "⚠️ I want to be back onboard this many minutes before departure",
            min_value=30, max_value=120, value=60, step=15,
            help="Most cruise lines close boarding 60–90 min before sailing."
        )
        set_timer = st.form_submit_button("🚀 Start timer")

    if set_timer:
        st.session_state.departure_dt = datetime.datetime.combine(dep_date, dep_time)

    if st.session_state.departure_dt:
        departure = st.session_state.departure_dt
        must_board = departure - datetime.timedelta(minutes=boarding_buffer)

        now = datetime.datetime.now()
        delta_sail = departure - now
        delta_board = must_board - now

        total_seconds_sail = int(delta_sail.total_seconds())
        total_seconds_board = int(delta_board.total_seconds())

        # Status
        if total_seconds_board < 0:
            status_msg = "🚨 YOU SHOULD BE ONBOARD NOW!"
            status_color = "#e8604c"
        elif total_seconds_board < 1800:
            status_msg = "⚠️ Head back to the ship soon!"
            status_color = "#f5a623"
        else:
            status_msg = "✅ You have time to explore!"
            status_color = "#3aab8a"

        def fmt_delta(secs):
            if secs <= 0:
                return "00:00:00"
            h = secs // 3600
            m = (secs % 3600) // 60
            s = secs % 60
            return f"{h:02d}:{m:02d}:{s:02d}"

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            <div class="timer-box">
                <div class="timer-label">⛴️ Until your ship sails</div>
                <div class="timer-digits">{fmt_delta(total_seconds_sail)}</div>
                <div style="font-size:0.85rem;opacity:0.7">{departure.strftime('%d %b %Y – %H:%M')}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div class="timer-box" style="background:{status_color if total_seconds_board < 1800 else 'var(--marseille-blue)'}">
                <div class="timer-label">🏃 You must board by</div>
                <div class="timer-digits">{fmt_delta(total_seconds_board)}</div>
                <div style="font-size:0.85rem;opacity:0.7">{must_board.strftime('%H:%M')} ({boarding_buffer} min buffer)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card" style="background:{status_color}15;border-left-color:{status_color};text-align:center;font-size:1.1rem;font-weight:600;color:{status_color}">
            {status_msg}
        </div>
        """, unsafe_allow_html=True)

        # Countdown progress bar
        if total_seconds_sail > 0:
            day_total = 12 * 3600  # reference 12h window
            pct = max(0.0, min(1.0, 1 - total_seconds_sail / day_total))
            st.progress(pct, text=f"Time elapsed since your ideal shore window started")

        st.info("🔄 Refresh the page to update the countdown — or keep this tab open and press F5 periodically.")

        # Suggestions based on remaining time
        st.markdown("<hr class='fancy'>", unsafe_allow_html=True)
        st.markdown('<p class="section-title">What can I do now?</p>', unsafe_allow_html=True)
        hours_left = total_seconds_board / 3600
        if hours_left >= 3:
            st.markdown("""<div class="card card-blue">
                🗺️ <b>Plenty of time!</b> You can visit 3–4 sites comfortably. Check your full itinerary.
            </div>""", unsafe_allow_html=True)
        elif hours_left >= 1.5:
            st.markdown("""<div class="card">
                ⚡ <b>Quick visits only.</b> Stick to 1–2 nearby spots: Vieux-Port, Le Panier, or grab a bouillabaisse.
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="card card-coral">
                🚕 <b>Head back now.</b> Call a taxi from the Vieux-Port stand — +33 4 91 02 20 20.
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 – FEEDBACK
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💬 Avis & Retours":
    st.markdown("""
    <div class="hero">
        <h1>Share your experience 💬</h1>
        <p>Your feedback helps fellow travellers — and local businesses — thrive. Merci !</p>
    </div>
    """, unsafe_allow_html=True)

    col_form, col_wall = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown('<p class="section-title">Leave a review</p>', unsafe_allow_html=True)
        st.markdown('<p class="section-sub">Visited a spot in Marseille? Tell us what you thought.</p>', unsafe_allow_html=True)

        with st.form("feedback_form"):
            fb_name    = st.text_input("Your name (optional)", placeholder="Anonymous")
            fb_country = st.selectbox("Your country", COUNTRIES, key="fb_country")
            fb_place   = st.selectbox("Place visited", PLACES)
            fb_rating  = st.select_slider(
                "Rating",
                options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
                value="⭐⭐⭐⭐",
            )
            fb_comment = st.text_area("Your comment", placeholder="What did you love? Any tips for others?", height=100)
            fb_tags    = st.multiselect(
                "Tags",
                ["👨‍👩‍👧 Family-friendly", "♿ Accessible", "💸 Budget-friendly",
                 "🌟 Hidden gem", "📸 Instagrammable", "🚶 Easy walk",
                 "🍽️ Great food nearby", "🔇 Quiet", "🎒 Must-see"],
            )
            submit_fb = st.form_submit_button("📤 Submit review")

        if submit_fb:
            if fb_comment.strip() or fb_rating:
                st.session_state.feedbacks.append({
                    "name": fb_name or "Anonymous",
                    "country": fb_country,
                    "place": fb_place,
                    "rating": fb_rating,
                    "comment": fb_comment,
                    "tags": fb_tags,
                    "ts": datetime.datetime.now().strftime("%d %b %Y, %H:%M"),
                })
                st.success("✅ Thank you! Your review has been shared.")
            else:
                st.warning("Please add a rating or comment before submitting.")

    with col_wall:
        st.markdown('<p class="section-title">Latest reviews</p>', unsafe_allow_html=True)
        st.markdown('<p class="section-sub">What travellers from around the world are saying.</p>', unsafe_allow_html=True)

        # Seed with some example reviews if none yet
        sample_feedbacks = [
            {"name": "Sophie", "country": "🇩🇪 Germany", "place": "MuCEM",
             "rating": "⭐⭐⭐⭐⭐", "comment": "Absolutely breathtaking – the views of the sea from the walkway are unforgettable!",
             "tags": ["📸 Instagrammable", "🌟 Hidden gem"], "ts": "22 Apr 2026, 14:30"},
            {"name": "Carlos", "country": "🇪🇸 Spain", "place": "Noailles Market",
             "rating": "⭐⭐⭐⭐", "comment": "Chaotic and wonderful. The best harissa I've ever tasted.",
             "tags": ["💸 Budget-friendly", "🍽️ Great food nearby"], "ts": "22 Apr 2026, 11:15"},
            {"name": "Yuki", "country": "🇯🇵 Japan", "place": "Vieux-Port",
             "rating": "⭐⭐⭐⭐⭐", "comment": "We arrived at sunrise and the fishing boats were still coming in. Magical.",
             "tags": ["📸 Instagrammable", "🚶 Easy walk"], "ts": "21 Apr 2026, 09:00"},
        ]
        display_feedbacks = sample_feedbacks + st.session_state.feedbacks[::-1]

        if not display_feedbacks:
            st.info("No reviews yet — be the first!")
        else:
            for fb in display_feedbacks[:12]:
                tag_html = "".join(f'<span class="tag">{t}</span>' for t in fb.get("tags", []))
                st.markdown(f"""
                <div class="card" style="margin-bottom:0.8rem">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start">
                        <div>
                            <span style="font-weight:600">{fb['name']}</span>
                            <span style="color:var(--muted);font-size:0.85rem;margin-left:0.5rem">{fb['country']}</span>
                        </div>
                        <span class="stars">{fb['rating']}</span>
                    </div>
                    <div style="font-size:0.82rem;color:var(--sea);font-weight:600;margin:0.3rem 0">📍 {fb['place']}</div>
                    <div style="font-size:0.9rem;color:var(--text);margin-bottom:0.5rem">{fb['comment']}</div>
                    <div>{tag_html}</div>
                    <div style="font-size:0.75rem;color:var(--muted);margin-top:0.5rem">{fb['ts']}</div>
                </div>
                """, unsafe_allow_html=True)

        # Stats
        if st.session_state.feedbacks:
            st.markdown("<hr class='fancy'>", unsafe_allow_html=True)
            st.markdown('<p class="section-title" style="font-size:1.1rem">📊 Review stats</p>', unsafe_allow_html=True)
            from collections import Counter
            country_counts = Counter(f["country"] for f in st.session_state.feedbacks)
            place_counts   = Counter(f["place"] for f in st.session_state.feedbacks)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Top countries:**")
                for country, count in country_counts.most_common(5):
                    st.markdown(f"- {country}: **{count}**")
            with c2:
                st.markdown("**Most reviewed places:**")
                for place, count in place_counts.most_common(5):
                    st.markdown(f"- 📍 {place}: **{count}**")
