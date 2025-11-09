# streamlit_app.py
# TreasureHunt - responsive Streamlit app
# - Use this file name exactly for deployment
# - Place sprites/ and sounds/ in same repo root
# - highscores.json will be created/updated automatically

import streamlit as st
import os
import json
import random
import time
from pathlib import Path
from datetime import datetime

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Treasure Hunt", page_icon="💎", layout="wide")

BASE_DIR = Path(__file__).parent
SPRITES_DIR = BASE_DIR / "sprites"
SOUNDS_DIR = BASE_DIR / "sounds"
HIGHSCORES_FILE = BASE_DIR / "highscores.json"

# -------------------------
# Expected assets (names must match)
# -------------------------
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
}

# -------------------------
# Load highscores safely
# -------------------------
def load_highscores():
    if HIGHSCORES_FILE.exists():
        try:
            return json.loads(HIGHSCORES_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_highscores(data):
    HIGHSCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
    HIGHSCORES_FILE.write_text(json.dumps(data, indent=4), encoding="utf-8")

highscores = load_highscores()

# -------------------------
# Game settings
# -------------------------
GRID_SIZE_DESKTOP = 6
GRID_SIZE_MOBILE = 5
TREASURE_COUNT = 3
COIN_COUNT = 2
HEART_COUNT = 1
TRAP_COUNT = 3
MAX_LIVES = 3

# -------------------------
# Responsive CSS & mobile sticky controls
# -------------------------
CSS = """
<style>
.game-table { border-collapse: collapse; margin: 0 auto; }
.game-table td { width:64px; height:64px; text-align:center; vertical-align:middle; border:1px solid rgba(0,0,0,0.06); }
.game-tile { display:flex; align-items:center; justify-content:center; }
.game-control { background-color:#0b7285; color:#fff; border:none; padding:12px 16px; margin:6px; border-radius:12px; font-size:18px; }
.game-control:active { transform: translateY(1px); box-shadow: 0 1px 0 rgba(0,0,0,0.12); }

/* Desktop tile image sizing */
.game-tile img { width:60px; height:60px; }

/* Mobile specific */
@media (max-width:799px) {
  .game-tile img { width:10vw !important; height:10vw !important; }
  .mobile-controls {
    position: fixed;
    left: 6px;
    right: 6px;
    bottom: 8px;
    display:flex;
    justify-content:center;
    align-items:center;
    z-index:9999;
    background: linear-gradient(180deg, rgba(255,255,255,0.0), rgba(255,255,255,0.02));
    padding:6px 4px;
    border-radius:12px;
  }
  .mobile-controls .game-control { padding:10px 12px; font-size:16px; margin:4px; border-radius:10px; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -------------------------
# Check for missing assets
# -------------------------
missing_sprites = [k for k,v in EXPECTED_SPRITES.items() if not v.exists()]
missing_sounds = [k for k,v in EXPECTED_SOUNDS.items() if not v.exists()]

if missing_sprites:
    st.warning("Missing sprite files: " + ", ".join(missing_sprites) + ". Put them in /sprites/ with exact names.")
if missing_sounds:
    st.info("Missing sound files (optional): " + ", ".join(missing_sounds) + " — place in /sounds/")

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
    st.session_state.grid_objects = []
if "revealed" not in st.session_state:
    st.session_state.revealed = []
if "move" not in st.session_state:
    st.session_state.move = None
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "screen_mode" not in st.session_state:
    st.session_state.screen_mode = "desktop"
if "grid_size" not in st.session_state:
    st.session_state.grid_size = GRID_SIZE_DESKTOP
if "sound_on" not in st.session_state:
    st.session_state.sound_on = True

# -------------------------
# Screen probe (put viewport width in query param once)
# -------------------------
if "screen_probe_done" not in st.session_state:
    probe_js = """
    <script>
    (function(){
      const w = window.innerWidth || document.documentElement.clientWidth;
      const params = new URLSearchParams(window.location.search);
      params.set('vw', String(w));
      const newUrl = window.location.pathname + '?' + params.toString();
      if (!window.location.search.includes('vw=')) {
         window.history.replaceState({}, '', newUrl);
      }
    })();
    </script>
    """
    st.components.v1.html(probe_js, height=0, key="probe")
    st.session_state.screen_probe_done = True

# Read query param to set mobile/desktop
try:
    qp = st.experimental_get_query_params()
    if "vw" in qp:
        vw = int(qp["vw"][0])
        if vw < 800:
            st.session_state.screen_mode = "mobile"
            st.session_state.grid_size = GRID_SIZE_MOBILE
        else:
            st.session_state.screen_mode = "desktop"
            st.session_state.grid_size = GRID_SIZE_DESKTOP
except Exception:
    pass

GRID_SIZE = st.session_state.grid_size

# -------------------------
# Ticking clock (stopwatch)
# We will force light refresh using an injected JS that updates query param 't' every second.
# -------------------------
tick_js = """
<script>
(function() {
  setInterval(function(){
    try {
      const params = new URLSearchParams(window.location.search);
      params.set('t', Math.floor(Date.now()/1000));
      const newurl = window.location.pathname + '?' + params.toString();
      window.history.replaceState({}, '', newurl);
    } catch(e) {}
  }, 1000);
})();
</script>
"""
st.components.v1.html(tick_js, height=0)

elapsed = int(time.time() - st.session_state.start_time)

# -------------------------
# Sound play helper
# -------------------------
def play_sound(name):
    p = EXPECTED_SOUNDS.get(name)
    if p and p.exists() and st.session_state.sound_on:
        try:
            with open(p, "rb") as f:
                st.audio(f.read(), format="audio/mp3")
        except Exception:
            pass

# -------------------------
# Object placement
# -------------------------
def regen_objects(level):
    objs = []
    def place(count, typ):
        for _ in range(count):
            tries = 0
            while True:
                tries += 1
                pos = [random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)]
                occupied = pos == st.session_state.player_pos or pos in [o["pos"] for o in objs]
                if not occupied:
                    objs.append({"type": typ, "pos": pos})
                    break
                if tries > 200:
                    break
    place(TREASURE_COUNT + level//2, "treasure")
    place(COIN_COUNT + level//3, "coin")
    place(HEART_COUNT, "heart")
    place(TRAP_COUNT + level//2, "trap")
    return objs

if not st.session_state.grid_objects:
    st.session_state.grid_objects = regen_objects(st.session_state.level)

if not st.session_state.revealed or len(st.session_state.revealed) != GRID_SIZE:
    st.session_state.revealed = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
    st.session_state.revealed[0][0] = True

# -------------------------
# Movement logic
# -------------------------
def process_move(dx, dy):
    x, y = st.session_state.player_pos
    nx, ny = x + dx, y + dy
    if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
        return
    st.session_state.player_pos = [nx, ny]
    st.session_state.revealed[nx][ny] = True

    # check objects
    for obj in st.session_state.grid_objects[:]:
        if obj["pos"] == [nx, ny]:
            typ = obj["type"]
            if typ == "treasure":
                st.session_state.score += 10
                play_sound("treasure")
                st.success("Treasure +10")
            elif typ == "coin":
                st.session_state.score += 5
                play_sound("treasure")
                st.info("Coin +5")
            elif typ == "heart":
                st.session_state.score += 15
                st.session_state.lives = min(MAX_LIVES, st.session_state.lives + 1)
                play_sound("treasure")
                st.success("Heart +15, +1 life")
            elif typ == "trap":
                st.session_state.score = max(0, st.session_state.score - 5)
                st.session_state.lives -= 1
                play_sound("trap")
                st.error("Hit a trap! -5 and lost a life")
            st.session_state.grid_objects.remove(obj)

    # level up condition
    treasures_left = [o for o in st.session_state.grid_objects if o["type"] == "treasure"]
    if not treasures_left:
        st.session_state.level += 1
        st.session_state.score += 20
        play_sound("levelup")
        st.balloons()
        st.info(f"Level up! Now level {st.session_state.level}")
        st.session_state.grid_objects = regen_objects(st.session_state.level)

# handle queued move (set by buttons)
if st.session_state.move:
    move_cmd = st.session_state.move
    if move_cmd == "up":
        process_move(-1, 0)
    elif move_cmd == "down":
        process_move(1, 0)
    elif move_cmd == "left":
        process_move(0, -1)
    elif move_cmd == "right":
        process_move(0, 1)
    else:
        pass
    st.session_state.move = None

# -------------------------
# UI layout
# -------------------------
# Sidebar leaderboard & controls
st.sidebar.title("Leaderboard (Top 10)")
if highscores:
    for i, e in enumerate(sorted(highscores, key=lambda x: x["score"], reverse=True)[:10]):
        st.sidebar.markdown(f"**{i+1}. {e['name']}** — {e['score']} pts | Lv {e.get('level',1)} | {e.get('treasures_collected',0)} items | {e.get('date','-')}")
else:
    st.sidebar.write("No highscores yet. Be the first!")

if st.sidebar.button("Toggle Sound"):
    st.session_state.sound_on = not st.session_state.sound_on
    st.sidebar.success("Sound ON" if st.session_state.sound_on else "Sound OFF")

if st.sidebar.button("Reset Game"):
    st.session_state.player_pos = [0,0]
    st.session_state.score = 0
    st.session_state.level = 1
    st.session_state.lives = MAX_LIVES
    st.session_state.grid_objects = regen_objects(1)
    st.session_state.revealed = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
    st.session_state.revealed[0][0] = True
    st.session_state.start_time = time.time()
    st.experimental_rerun()

# Header
st.markdown("<h2 style='text-align:center;margin-bottom:6px'>Treasure Hunt</h2>", unsafe_allow_html=True)

# Columns: desktop left grid and right controls, mobile stacked
if st.session_state.screen_mode == "desktop":
    left_col, right_col = st.columns([3,1])
else:
    left_col = st.container()
    right_col = st.container()

# Grid render (HTML table)
with left_col:
    st.markdown(f"**Level:** {st.session_state.level}  •  **Score:** {st.session_state.score}  •  **Lives:** {st.session_state.lives}")
    st.markdown(f"⏱ **Time:** `{elapsed} s`")
    table = "<table class='game-table'>"
    for i in range(GRID_SIZE):
        table += "<tr>"
        for j in range(GRID_SIZE):
            table += "<td class='game-tile'>"
            content = ""
            if st.session_state.player_pos == [i,j]:
                if EXPECTED_SPRITES["player"].exists():
                    content = f"<img src='{EXPECTED_SPRITES['player'].as_posix()}'/>"
                else:
                    content = "🙂"
            elif not st.session_state.revealed[i][j]:
                if EXPECTED_SPRITES["fog"].exists():
                    content = f"<img src='{EXPECTED_SPRITES['fog'].as_posix()}'/>"
                else:
                    content = ""
            else:
                obj = next((o for o in st.session_state.grid_objects if o["pos"] == [i,j]), None)
                if obj:
                    typ = obj["type"]
                    sp = EXPECTED_SPRITES.get(typ)
                    if sp and sp.exists():
                        content = f"<img src='{sp.as_posix()}'/>"
                    else:
                        fallback = {"treasure":"💎","coin":"🪙","heart":"❤️","trap":"💀"}
                        content = fallback.get(typ, "?")
                else:
                    content = ""
            table += content
            table += "</td>"
        table += "</tr>"
    table += "</table>"

    st.components.v1.html(f"<div class='game-grid'>{table}</div>", height=(GRID_SIZE * 72))

# Controls and info
with right_col:
    if st.session_state.screen_mode == "desktop":
        st.markdown("### Controls")
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("⭠", key="left_btn"):
                st.session_state.move = "left"
        with c2:
            if st.button("⭡", key="up_btn"):
                st.session_state.move = "up"
        with c3:
            if st.button("⭢", key="right_btn"):
                st.session_state.move = "right"
        c4, c5, c6 = st.columns([1,1,1])
        with c4:
            st.write("")
        with c5:
            if st.button("⭣", key="down_btn"):
                st.session_state.move = "down"
        with c6:
            st.write("")
    else:
        # mobile-sticky controls container (CSS makes it fixed at bottom)
        st.markdown("<div class='mobile-controls'>", unsafe_allow_html=True)
        mcols = st.columns([1,1,1,1])
        with mcols[0]:
            if st.button("⭠", key="m_left"):
                st.session_state.move = "left"
        with mcols[1]:
            if st.button("⭡", key="m_up"):
                st.session_state.move = "up"
        with mcols[2]:
            if st.button("⭣", key="m_down"):
                st.session_state.move = "down"
        with mcols[3]:
            if st.button("⭢", key="m_right"):
                st.session_state.move = "right"
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Game Info")
    st.write(f"- Score: {st.session_state.score}")
    st.write(f"- Level: {st.session_state.level}")
    st.write(f"- Lives: {st.session_state.lives}")
    st.write(f"- Elapsed: {elapsed} s")

    # Save score form
    with st.form("save_form"):
        pname = st.text_input("Name to save score:", value="")
        submitted = st.form_submit_button("Save Score")
        if submitted:
            if pname.strip():
                entry = {
                    "name": pname.strip(),
                    "score": st.session_state.score,
                    "level": st.session_state.level,
                    "treasures_collected": sum(1 for o in st.session_state.grid_objects if o["type"] in ["treasure","coin","heart"]),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                highscores.append(entry)
                highscores.sort(key=lambda x: x["score"], reverse=True)
                highscores[:] = highscores[:10]
                save_highscores(highscores)
                st.success("Saved to leaderboard!")
            else:
                st.error("Please enter a name.")

# Game over message
if st.session_state.lives <= 0:
    st.error("Game Over — you lost all lives. Use Reset Game in sidebar to restart.")

# Footer
st.markdown("<hr />", unsafe_allow_html=True)
st.markdown("<small>Tip: On mobile the grid auto-scales so controls remain visible. Add sprites and sounds to /sprites and /sounds folders.</small>", unsafe_allow_html=True)
