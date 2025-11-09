# app.py
# Pro TreasureHunt - single-file Streamlit app
# Responsive layout (desktop / mobile), always-ticking timer, sprites + sounds + leaderboard

import streamlit as st
import os
import json
import random
import time
from pathlib import Path
from datetime import datetime

# -------------------------
# Config & paths
# -------------------------
st.set_page_config(page_title="Treasure Hunt", page_icon="💎", layout="wide", initial_sidebar_state="auto")

BASE_DIR = Path(__file__).parent
SPRITES_DIR = BASE_DIR / "sprites"
SOUNDS_DIR = BASE_DIR / "sounds"
HIGHSCORES_FILE = BASE_DIR / "highscores.json"

# Files expected (adjust if you named differently)
EXPECTED_SPRITES = {
    "player": SPRITES_DIR / "player.png",
    "treasure": SPRITES_DIR / "treasure.gif",
    "coin": SPRITES_DIR / "coin.gif",
    "heart": SPRITES_DIR / "heart.gif",
    "rock": SPRITES_DIR / "rock.png",
    "trap": SPRITES_DIR / "trap.png",
    "fog": SPRITES_DIR / "fog.png",
}
EXPECTED_SOUNDS = {
    "treasure": SOUNDS_DIR / "treasure.mp3",
    "trap": SOUNDS_DIR / "trap.mp3",
    "levelup": SOUNDS_DIR / "levelup.mp3",
    # optional extra sounds can be added
}

# -------------------------
# Utility: load highscores
# -------------------------
def load_highscores():
    if HIGHSCORES_FILE.exists():
        try:
            with open(HIGHSCORES_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def save_highscores(hs):
    (HIGHSCORES_FILE.parent).mkdir(parents=True, exist_ok=True)
    with open(HIGHSCORES_FILE, "w") as f:
        json.dump(hs, f, indent=4)

highscores = load_highscores()

# -------------------------
# Settings (play with these)
# -------------------------
GRID_SIZE_DESKTOP = 6  # desktop default
GRID_SIZE_MOBILE = 5   # mobile default (smaller to fit viewport)
TREASURE_COUNT = 3
COIN_COUNT = 2
HEART_COUNT = 1
TRAP_COUNT = 3
MAX_LIVES = 3

# -------------------------
# Responsive CSS
# - we scale tiles based on viewport width (vw) so grid fits on mobile
# - mobile controls are made compact and always visible by limiting grid height
# -------------------------
RESPONSIVE_CSS = """
<style>
/* Root adjustments */
.game-grid {
  margin: 0 auto;
}

/* Buttons style (solid rounded) */
.game-control {
  background-color: #005f73;
  color: #fff;
  border: none;
  padding: 12px 18px;
  margin: 6px;
  font-size: 18px;
  border-radius: 12px;
  box-shadow: 0 3px 0 rgba(0,0,0,0.15);
}
.game-control:active {
  transform: translateY(1px);
  box-shadow: 0 1px 0 rgba(0,0,0,0.12);
}

/* Mobile: compact controls container sticky bottom */
@media (max-width: 799px) {
  .stApp .mobile-controls {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 8px;
    display:flex;
    justify-content:center;
    align-items:center;
    z-index: 9999;
    background: linear-gradient(180deg, rgba(255,255,255,0.0), rgba(255,255,255,0.02));
    padding: 6px 4px;
  }
  .stApp .mobile-controls .game-control {
    padding: 10px 14px;
    font-size: 16px;
    margin: 4px;
    border-radius: 10px;
    opacity: 0.98;
  }
  /* reduce grid image sizes so it fits mobile height */
  .stApp .game-tile img {
    width: 9vw !important;
    height: 9vw !important;
  }
}

/* Desktop: place controls in right column - keep them visible */
@media (min-width: 800px) {
  .stApp .desktop-controls {
    position: static;
    padding: 8px;
  }
  .stApp .game-tile img {
    width: 60px !important;
    height: 60px !important;
  }
}

/* Generic tile container size */
.game-table {
  border-collapse: collapse;
  margin: 0 auto;
}
.game-table td {
  width: 64px;
  height: 64px;
  text-align: center;
  vertical-align: middle;
  border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.02);
}
.game-tile {
  display:flex;
  align-items:center;
  justify-content:center;
}
</style>
"""

st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)

# -------------------------
# Check for expected files & warn if missing
# -------------------------
missing_sprites = [n for n,p in EXPECTED_SPRITES.items() if not p.exists()]
missing_sounds = [n for n,p in EXPECTED_SOUNDS.items() if not p.exists()]

if missing_sprites:
    st.warning(f"Missing sprite files: {', '.join(missing_sprites)}. Place them in `sprites/` with correct names.")
if missing_sounds:
    st.info(f"Missing sound files (optional): {', '.join(missing_sounds)}. Place them in `sounds/` if you want SFX.")

# -------------------------
# Session state initialization
# -------------------------
if "player_pos" not in st.session_state:
    st.session_state.player_pos = [0, 0]
if "level" not in st.session_state:
    st.session_state.level = 1
if "score" not in st.session_state:
    st.session_state.score = 0
if "lives" not in st.session_state:
    st.session_state.lives = MAX_LIVES
if "grid_objects" not in st.session_state:
    st.session_state.grid_objects = []  # list of dicts: {"type":..., "pos":[x,y]}
if "revealed" not in st.session_state:
    st.session_state.revealed = []
if "move" not in st.session_state:
    st.session_state.move = None
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "screen_mode" not in st.session_state:
    st.session_state.screen_mode = "desktop"  # or mobile
if "grid_size" not in st.session_state:
    st.session_state.grid_size = GRID_SIZE_DESKTOP

# -------------------------
# Auto-detect small screens via a tiny HTML+JS component
# - This sets a small query param on reload to pass viewport width.
# - The component will run once per session (we use a key to avoid spamming)
# -------------------------
if "screen_probe_done" not in st.session_state:
    probe_html = """
    <script>
    (function() {
      const w = window.innerWidth || document.documentElement.clientWidth;
      // call Streamlit by adding a query param and reloading (lightweight)
      const params = new URLSearchParams(window.location.search);
      params.set('vw', String(w));
      const newUrl = window.location.pathname + '?' + params.toString();
      if (!window.location.search.includes('vw=')) {
        window.history.replaceState({}, '', newUrl);
      }
      // notify python by appending hidden element (session persists)
      // we won't force reload to avoid rerun loops
    })();
    </script>
    """
    st.components.v1.html(probe_html, height=0, key="screen_probe")
    st.session_state.screen_probe_done = True

# Read viewport width (in query params) to set mobile/desktop mode
try:
    q = st.experimental_get_query_params()
    if "vw" in q:
        vw = int(q["vw"][0])
        if vw < 800:
            st.session_state.screen_mode = "mobile"
            st.session_state.grid_size = GRID_SIZE_MOBILE
        else:
            st.session_state.screen_mode = "desktop"
            st.session_state.grid_size = GRID_SIZE_DESKTOP
except Exception:
    # fallback defaults already set
    pass

GRID_SIZE = st.session_state.grid_size

# -------------------------
# Helper: play sound (safe)
# -------------------------
def play_sound(name):
    path = EXPECTED_SOUNDS.get(name)
    if path and path.exists() and st.session_state.get("sound_on", True):
        try:
            with open(path, "rb") as f:
                audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/mp3")
        except Exception:
            # silently ignore audio errors
            pass

# -------------------------
# Initialize grid objects (treasures, coins, hearts, traps)
# -------------------------
def regen_objects(level):
    objects = []
    def place(count, type_name):
        for _ in range(count):
            attempt = 0
            while True:
                attempt += 1
                pos = [random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)]
                if pos != st.session_state.player_pos and pos not in [o["pos"] for o in objects]:
                    objects.append({"type": type_name, "pos": pos})
                    break
                if attempt > 200:
                    break
    place(TREASURE_COUNT + level//2, "treasure")
    place(COIN_COUNT + level//3, "coin")
    place(HEART_COUNT, "heart")
    place(TRAP_COUNT + level//2, "trap")
    return objects

if not st.session_state.grid_objects:
    st.session_state.grid_objects = regen_objects(st.session_state.level)

# revealed grid
if not st.session_state.revealed or len(st.session_state.revealed) != GRID_SIZE:
    st.session_state.revealed = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
    st.session_state.revealed[0][0] = True

# -------------------------
# Movement helper
# -------------------------
def process_move(dx, dy):
    x, y = st.session_state.player_pos
    nx, ny = x + dx, y + dy
    if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
        return
    st.session_state.player_pos = [nx, ny]
    st.session_state.revealed[nx][ny] = True

    # Check objects
    for obj in st.session_state.grid_objects[:]:
        if obj["pos"] == [nx, ny]:
            t = obj["type"]
            if t == "treasure":
                st.session_state.score += 10
                play_sound("treasure")
                st.success("Treasure collected! +10")
            elif t == "coin":
                st.session_state.score += 5
                play_sound("treasure")
                st.info("Coin +5")
            elif t == "heart":
                st.session_state.score += 15
                st.session_state.lives = min(MAX_LIVES, st.session_state.lives + 1)
                play_sound("treasure")
                st.success("Heart +15 and +1 life")
            elif t == "trap":
                st.session_state.score = max(0, st.session_state.score - 5)
                st.session_state.lives -= 1
                play_sound("trap")
                st.error("Hit a trap! -5 and lost a life")
            st.session_state.grid_objects.remove(obj)

    # Level up if no treasures left
    treasures_left = [o for o in st.session_state.grid_objects if o["type"] == "treasure"]
    if not treasures_left:
        st.session_state.level += 1
        st.session_state.score += 20  # bonus
        play_sound("levelup")
        st.balloons()
        st.info(f"Level up! Now level {st.session_state.level}")
        st.session_state.grid_objects = regen_objects(st.session_state.level)

# -------------------------
# Handle move from session_state.move (set by buttons)
# -------------------------
if st.session_state.move:
    m = st.session_state.move
    if m == "up":
        process_move(-1, 0)
    elif m == "down":
        process_move(1, 0)
    elif m == "left":
        process_move(0, -1)
    elif m == "right":
        process_move(0, 1)
    st.session_state.move = None

# -------------------------
# Timer (Stopwatch) - always ticking
# We store start_time in session_state and compute elapsed on each rerun.
# To visually update every second we inject a tiny JS that triggers a self-refresh
# by updating the URL query param with the current timestamp (lightweight).
# -------------------------
if "timer_auto_refresh" not in st.session_state:
    st.session_state.timer_auto_refresh = True

# Add a tiny invisible component to update query param timestamp every 1s to force rerun
# NOTE: this is a harmless replaceState and won't create new history entries after the first call.
tick_js = """
<script>
(function() {
  const key = 'treasure_tick';
  // Update the 't' query param with current seconds every 1s to force streamlit to re-evaluate query params.
  setInterval(function(){
    const params = new URLSearchParams(window.location.search);
    params.set('t', Math.floor(Date.now()/1000));
    const newurl = window.location.pathname + '?' + params.toString();
    window.history.replaceState({}, '', newurl);
  }, 1000);
})();
</script>
"""
# inject the script (hidden) - it only manipulates the URL, Streamlit reads the query params above on reruns
st.components.v1.html(tick_js, height=0)

# compute elapsed
elapsed = int(time.time() - st.session_state.start_time)
# Display timer in chosen place (we'll render it in the UI below)

# -------------------------
# Layout: main UI (responsive)
# Desktop: two columns - grid (left) and controls+info (right)
# Mobile: single column; grid scaled to viewport; controls placed below and fixed via CSS
# -------------------------
# Build leaderboard string for sidebar
st.sidebar.title("Leaderboard (Top 10)")
if highscores:
    for idx, e in enumerate(sorted(highscores, key=lambda x: x["score"], reverse=True)[:10]):
        st.sidebar.markdown(f"**{idx+1}. {e['name']}** — {e['score']} pts | Lv {e.get('level',1)} | {e.get('treasures_collected',0)} treasures | {e.get('date','-')}")
else:
    st.sidebar.write("No scores yet. Play and save your score!")

# Sound toggle
if "sound_on" not in st.session_state:
    st.session_state.sound_on = True
if st.sidebar.button("Toggle Sound"):
    st.session_state.sound_on = not st.session_state.sound_on
    st.sidebar.success("Sound ON" if st.session_state.sound_on else "Sound OFF")

# Reset game controls
st.sidebar.markdown("---")
if st.sidebar.button("Reset Game"):
    # reset core session state but keep highscores
    st.session_state.player_pos = [0,0]
    st.session_state.score = 0
    st.session_state.level = 1
    st.session_state.lives = MAX_LIVES
    st.session_state.grid_objects = regen_objects(1)
    st.session_state.revealed = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
    st.session_state.revealed[0][0] = True
    st.session_state.start_time = time.time()
    st.experimental_rerun()

# Info header
st.markdown("<h2 style='text-align:center;margin-bottom:6px'>Treasure Hunt</h2>", unsafe_allow_html=True)

# layout columns for desktop; single column stacks on narrow screens automatically
if st.session_state.screen_mode == "desktop":
    left_col, right_col = st.columns([3,1])
else:
    # mobile: grid full width, controls below
    left_col = st.container()
    right_col = st.container()

# -------------------------
# Render Grid in left_col
# -------------------------
with left_col:
    # show stats and timer above the grid
    st.markdown(f"**Level:** {st.session_state.level}  &nbsp;&nbsp; **Score:** {st.session_state.score}  &nbsp;&nbsp; **Lives:** {st.session_state.lives}")
    st.markdown(f"⏱️ **Time:** `{elapsed} sec`")

    # build HTML table grid with responsive tile sizing (CSS above handles mobile)
    table_html = "<table class='game-table' style='border-collapse: collapse;'>"
    for i in range(GRID_SIZE):
        table_html += "<tr>"
        for j in range(GRID_SIZE):
            table_html += "<td class='game-tile'>"
            # choose content
            content = ""
            # player
            if st.session_state.player_pos == [i,j]:
                if EXPECTED_SPRITES["player"].exists():
                    p = EXPECTED_SPRITES["player"].as_posix()
                    content = f"<img src='{p}' style='max-width:100%;height:auto;'/>"
                else:
                    content = "🙂"
            # unrevealed fog
            elif not st.session_state.revealed[i][j]:
                if EXPECTED_SPRITES["fog"].exists():
                    f = EXPECTED_SPRITES["fog"].as_posix()
                    content = f"<img src='{f}' style='max-width:100%;height:auto;'/>"
                else:
                    content = " "
            else:
                # revealed: check if object present
                obj = next((o for o in st.session_state.grid_objects if o["pos"] == [i,j]), None)
                if obj:
                    typ = obj["type"]
                    sprite_path = EXPECTED_SPRITES.get(typ)
                    if sprite_path and sprite_path.exists():
                        content = f"<img src='{sprite_path.as_posix()}' style='max-width:100%;height:auto;'/>"
                    else:
                        # fallback text icons
                        fallback = {"treasure":"💎","coin":"🪙","heart":"❤️","trap":"💀"}
                        content = fallback.get(typ, "?")
                else:
                    content = ""  # empty revealed
            # Wrap each tile in a clickable form that posts back via simple anchor hack:
            # We'll use a simple query param to indicate a tile click (so we can handle tile-based movement later if needed)
            # But for mobile/desktop controls we rely on arrow buttons (so this is only decorative)
            table_html += content
            table_html += "</td>"
        table_html += "</tr>"
    table_html += "</table>"

    st.components.v1.html(f"<div class='game-grid'>{table_html}</div>", height=(GRID_SIZE * 72))

# -------------------------
# Controls & info in right_col (desktop) or below (mobile)
# -------------------------
controls_container = right_col

with controls_container:
    if st.session_state.screen_mode == "desktop":
        st.markdown("<div class='desktop-controls'>", unsafe_allow_html=True)
        st.markdown("### Controls")
        # Desktop: place arrow buttons in 3x3 layout using columns
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("⭠", key="left_btn", help="Move left", on_click=None):
                st.session_state.move = "left"
        with c2:
            if st.button("⭡", key="up_btn", help="Move up"):
                st.session_state.move = "up"
        with c3:
            if st.button("⭢", key="right_btn", help="Move right"):
                st.session_state.move = "right"
        c4, c5, c6 = st.columns([1,1,1])
        with c4:
            st.write("")
        with c5:
            if st.button("⭣", key="down_btn", help="Move down"):
                st.session_state.move = "down"
        with c6:
            st.write("")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # Mobile: compact controls will be drawn below but CSS makes them sticky at bottom
        st.markdown("<div class='mobile-controls'>", unsafe_allow_html=True)
        # create 4 inline buttons
        # NOTE: When many streamlit elements are present, mobile sticky might overlap content.
        col_l, col_u, col_d, col_r = st.columns([1,1,1,1])
        with col_l:
            if st.button("⭠", key="m_left"):
                st.session_state.move = "left"
        with col_u:
            if st.button("⭡", key="m_up"):
                st.session_state.move = "up"
        with col_d:
            if st.button("⭣", key="m_down"):
                st.session_state.move = "down"
        with col_r:
            if st.button("⭢", key="m_right"):
                st.session_state.move = "right"
        st.markdown("</div>", unsafe_allow_html=True)

    # Extra info & Game Over / Save Score
    st.markdown("---")
    st.markdown("#### Game Info")
    st.markdown(f"- **Score:** {st.session_state.score}")
    st.markdown(f"- **Level:** {st.session_state.level}")
    st.markdown(f"- **Lives:** {st.session_state.lives}")
    st.markdown(f"- **Elapsed:** {elapsed} sec")

    # Save score form (always available)
    with st.form("save_score_form", clear_on_submit=False):
        name = st.text_input("Enter name to save score", value="")
        submitted = st.form_submit_button("Save Score")
        if submitted:
            if name.strip():
                new = {
                    "name": name.strip(),
                    "score": st.session_state.score,
                    "level": st.session_state.level,
                    "treasures_collected": sum(1 for o in st.session_state.grid_objects if o["type"] in ["treasure","coin","heart"]) ,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                highscores.append(new)
                highscores.sort(key=lambda x: x["score"], reverse=True)
                highscores[:] = highscores[:10]
                save_highscores(highscores)
                st.success("Saved to leaderboard!")
            else:
        
