# streamlit_app.py
import streamlit as st
import random
import json
import time
from pathlib import Path

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Treasure Hunt", page_icon="💎", layout="wide")
st.set_option("client.showErrorDetails", True)

# -------------------------
# Constants
# -------------------------
GRID = 6
MAX_LIVES = 3
HIGHSCORE_FILE = Path("highscores.json")

EMOJI = {
    "player": "👤",     # your chosen ninja-like shadow icon
    "treasure": "💎",
    "coin": "📀",       # golden disc (DVD)
    "bomb": "💣",
    "heart": "❤️",
    "fog": "❔",
    "empty": "⬜"
}

# -------------------------
# Difficulty settings
# -------------------------
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
difficulty_stats = {
    "Easy":   {"bombs": 2, "coins": 5, "hearts": 2},
    "Medium": {"bombs": 4, "coins": 3, "hearts": 1},
    "Hard":   {"bombs": 6, "coins": 2, "hearts": 0},
}
stats = difficulty_stats[difficulty]

# -------------------------
# Highscore load/save
# -------------------------
def load_scores():
    if HIGHSCORE_FILE.exists():
        try:
            return json.loads(HIGHSCORE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_scores(data):
    HIGHSCORE_FILE.write_text(json.dumps(data, indent=4), encoding="utf-8")

scores = load_scores()

# -------------------------
# Session State init
# -------------------------
if "player" not in st.session_state:
    st.session_state.player = [0, 0]
if "objects" not in st.session_state:
    st.session_state.objects = []
if "revealed" not in st.session_state:
    st.session_state.revealed = [[False] * GRID for _ in range(GRID)]
if "score" not in st.session_state:
    st.session_state.score = 0
if "lives" not in st.session_state:
    st.session_state.lives = MAX_LIVES
if "level" not in st.session_state:
    st.session_state.level = 1
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "pending_move" not in st.session_state:
    st.session_state.pending_move = None

# ensure start tile revealed
st.session_state.revealed[0][0] = True

# -------------------------
# Object generation
# -------------------------
def generate_objects(level):
    objs = []
    counts = {
        "treasure": 3,
        "coin": stats["coins"],
        "heart": stats["hearts"],
        "bomb": stats["bombs"] + max(0, level-1),
    }
    for typ, cnt in counts.items():
        for _ in range(cnt):
            tries = 0
            while True:
                tries += 1
                pos = [random.randint(0, GRID-1), random.randint(0, GRID-1)]
                if pos != st.session_state.player and pos not in [o["pos"] for o in objs]:
                    objs.append({"pos": pos, "type": typ})
                    break
                if tries > 300:
                    break
    return objs

# init objects once
if not st.session_state.objects:
    st.session_state.objects = generate_objects(st.session_state.level)

# -------------------------
# Fog reveal logic (Mode B: Hard reduced visibility)
# -------------------------
def reveal_fog(x, y):
    # always reveal current tile
    st.session_state.revealed[x][y] = True

    if difficulty == "Hard":
        # only cardinal directions + current tile
        deltas = [(0,0), (-1,0), (1,0), (0,-1), (0,1)]
    else:
        # reveal 8 neighbors + current tile
        deltas = [(dx, dy) for dx in (-1,0,1) for dy in (-1,0,1)]

    for dx, dy in deltas:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID and 0 <= ny < GRID:
            st.session_state.revealed[nx][ny] = True

# reveal initial around player
reveal_fog(*st.session_state.player)

# -------------------------
# Movement & game rules
# -------------------------
def move(dx, dy):
    x, y = st.session_state.player
    nx, ny = x + dx, y + dy
    if not (0 <= nx < GRID and 0 <= ny < GRID):
        return

    st.session_state.player = [nx, ny]
    reveal_fog(nx, ny)

    # check objects at new pos
    for obj in st.session_state.objects[:]:
        if obj["pos"] == [nx, ny]:
            typ = obj["type"]
            if typ == "treasure":
                st.session_state.score += 10
                st.success("💎 Treasure +10")
            elif typ == "coin":
                st.session_state.score += 5
                st.info("📀 Coin +5")
            elif typ == "heart":
                st.session_state.lives = min(MAX_LIVES, st.session_state.lives + 1)
                st.success("❤️ +1 Life")
            elif typ == "bomb":
                st.session_state.lives -= 1
                st.error("💣 Bomb! -1 life")
            st.session_state.objects.remove(obj)

    # level up if no treasure left
    if not any(o["type"] == "treasure" for o in st.session_state.objects):
        st.session_state.score += 20
        st.session_state.level += 1
        st.balloons()
        st.info(f"LEVEL UP ➤ {st.session_state.level}")
        st.session_state.objects = generate_objects(st.session_state.level)
        reveal_fog(*st.session_state.player)

# -------------------------
# Fix movement lag: execute pending_move at the top of rerun
# -------------------------
if st.session_state.pending_move:
    dx, dy = st.session_state.pending_move
    # clear before calling to avoid double-moves in rare cases
    st.session_state.pending_move = None
    move(dx, dy)

# -------------------------
# UI Styling (simple, responsive)
# -------------------------
st.markdown("""
<style>
/* background + grid styling */
body { background: linear-gradient(135deg,#0A2342,#0F4C75); }
.grid { border-collapse: collapse; margin: 8px auto; }
.grid td { width:64px; height:64px; text-align:center; vertical-align:middle; border-radius:10px; border:1px solid rgba(255,255,255,0.06); font-size:30px; }
.hidden { background: #0b1220; color: #cfd8e3; }
.player { background: #4CC9F0; color: #082032; }
.treasure { background: #FEE440; color: #111; }
.coin { background: #FFD27F; color: #111; }
.heart { background: #FF6B6B; color: #fff; }
.bomb { background: #6A040F; color: #fff; }

/* controls area */
.controls { display:flex; justify-content:center; align-items:center; gap:12px; margin-top:12px; }
.dpad { display:grid; grid-template-columns:64px 64px 64px; grid-template-rows:64px 64px 64px; gap:8px; justify-content:center; align-items:center; }
.btn { width:64px; height:64px; font-size:26px; border-radius:10px; border:none; background:#4CC9F0; color:#08121d; }
@media (max-width: 700px) {
  .grid td { width:11vw; height:11vw; font-size:6vw; }
  .btn { width:12vw; height:12vw; font-size:6vw; border-radius:8vw; }
  .dpad { gap:6px; grid-template-columns: 1fr 1fr 1fr; grid-auto-rows: auto; }
}
.topbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Top bar
# -------------------------
left, right = st.columns([2,1])
with left:
    st.markdown("<div class='topbar'>", unsafe_allow_html=True)
    st.markdown(f"### Treasure Hunt — Level {st.session_state.level}")
    st.markdown("</div>", unsafe_allow_html=True)
with right:
    elapsed = int(time.time() - st.session_state.start_time)
    st.markdown(f"⏱ **{elapsed}s**  •  ❤️ `{st.session_state.lives}`  •  ⭐ `{st.session_state.score}`")

# -------------------------
# Render grid using st.columns for consistent layout
# -------------------------
grid_html_rows = []
for i in range(GRID):
    cols = st.columns(GRID)
    for j, col in enumerate(cols):
        # hidden?
        if not st.session_state.revealed[i][j]:
            col.markdown(f"<div style='text-align:center'><span class='hidden'>{EMOJI['fog']}</span></div>", unsafe_allow_html=True)
            continue

        # player
        if st.session_state.player == [i, j]:
            col.markdown(f"<div style='text-align:center'><span class='player'>{EMOJI['player']}</span></div>", unsafe_allow_html=True)
            continue

        # object or empty
        obj = next((o for o in st.session_state.objects if o["pos"] == [i, j]), None)
        if obj:
            typ = obj["type"]
            css = typ
            ico = EMOJI.get(typ, EMOJI["empty"])
            col.markdown(f"<div style='text-align:center'><span class='{css}'>{ico}</span></div>", unsafe_allow_html=True)
        else:
            col.markdown(f"<div style='text-align:center'><span class=''>{EMOJI['empty']}</span></div>", unsafe_allow_html=True)

# -------------------------
# Controls (Symmetric D-pad layout A)
# -------------------------
st.markdown("<div class='controls'>", unsafe_allow_html=True)
# dpad grid:
st.markdown("<div class='dpad'>", unsafe_allow_html=True)

# Row 1: (blank) Up (blank)
st.markdown("<div></div>", unsafe_allow_html=True)
if st.button("⬆️", key="up_btn"):
    st.session_state.pending_move = (-1, 0)
st.markdown("<div></div>", unsafe_allow_html=True)

# Row 2: Left (center placeholder) Right
if st.button("⬅️", key="left_btn"):
    st.session_state.pending_move = (0, -1)
st.markdown("<div style='display:flex;justify-content:center;align-items:center; font-weight:700;'>", unsafe_allow_html=True)
st.markdown(f"<div style='font-size:20px'>{EMOJI['player']}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
if st.button("➡️", key="right_btn"):
    st.session_state.pending_move = (0, 1)

# Row 3: (blank) Down (blank)
st.markdown("<div></div>", unsafe_allow_html=True)
if st.button("⬇️", key="down_btn"):
    st.session_state.pending_move = (1, 0)
st.markdown("<div></div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Save score / restart UI
# -------------------------
st.markdown("---")
if st.session_state.lives <= 0:
    st.error("💀 GAME OVER")
    name = st.text_input("Enter name to save score")
    if st.button("Save Score"):
        if name.strip():
            scs = load_scores()
            scs.append({"name": name.strip(), "score": st.session_state.score, "level": st.session_state.level, "time": elapsed})
            scs = sorted(scs, key=lambda x: x["score"], reverse=True)[:10]
            save_scores(scs)
            st.success("Saved!")
    if st.button("Restart"):
        # reset session-state keys in-place
        st.session_state.player = [0, 0]
        st.session_state.objects = generate_objects(1)
        st.session_state.revealed = [[False] * GRID for _ in range(GRID)]
        st.session_state.revealed[0][0] = True
        st.session_state.score = 0
        st.session_state.lives = MAX_LIVES
        st.session_state.level = 1
        st.session_state.start_time = time.time()
        st.experimental_rerun()

# -------------------------
# Sidebar: Leaderboard & Reset
# -------------------------
st.sidebar.title("Leaderboard 🏆")
scs = load_scores()
if scs:
    for idx, e in enumerate(scs, start=1):
        st.sidebar.write(f"**{idx}. {e['name']}** — {e['score']} pts (Lv {e.get('level',1)})")
else:
    st.sidebar.write("No scores yet.")

if st.sidebar.button("Reset Game"):
    st.session_state.player = [0, 0]
    st.session_state.objects = generate_objects(1)
    st.session_state.revealed = [[False] * GRID for _ in range(GRID)]
    st.session_state.revealed[0][0] = True
    st.session_state.score = 0
    st.session_state.lives = MAX_LIVES
    st.session_state.level = 1
    st.session_state.start_time = time.time()
    st.experimental_rerun()
