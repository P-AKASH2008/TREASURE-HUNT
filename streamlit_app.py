import streamlit as st
import random
import json
from pathlib import Path
import time

# ==============================
# Page config
# ==============================
st.set_page_config(page_title="Treasure Hunt", layout="wide")

# ==============================
# Constants
# ==============================
MAX_LIVES = 3
GRID = 6  # same grid on all difficulty levels

HIGHSCORE_FILE = Path("highscores.json")

EMOJI = {
    "player": "👤",
    "treasure": "💎",
    "coin": "📀",     # ✅ changed coin emoji to golden disc
    "bomb": "💣",
    "heart": "❤️",
    "fog": "❔",       # cleaner than ?
}

# ==============================
# Leaderboard file handling
# ==============================
def load_scores():
    if HIGHSCORE_FILE.exists():
        try:
            return json.loads(HIGHSCORE_FILE.read_text())
        except:
            return []
    return []


def save_scores(data):
    HIGHSCORE_FILE.write_text(json.dumps(data, indent=4))


# ==============================
# Difficulty settings
# ==============================
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

difficulty_stats = {
    "Easy":   {"bombs": 2, "coins": 5, "hearts": 2},
    "Medium": {"bombs": 4, "coins": 3, "hearts": 1},
    "Hard":   {"bombs": 6, "coins": 2, "hearts": 0},
}

stats = difficulty_stats[difficulty]


# ==============================
# Session State Initialization
# ==============================
if "player" not in st.session_state:
    st.session_state.player = [0, 0]
if "objects" not in st.session_state:
    st.session_state.objects = []
if "revealed" not in st.session_state:
    st.session_state.revealed = [[False]*GRID for _ in range(GRID)]
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


# ==============================
# Object generator
# ==============================
def generate_objects(level):
    objs = []
    obj_counts = {
        "treasure": 3,
        "coin": stats["coins"],
        "heart": stats["hearts"],
        "bomb": stats["bombs"] + level,
    }

    for typ, count in obj_counts.items():
        for _ in range(count):
            while True:
                pos = [random.randint(0, GRID - 1), random.randint(0, GRID - 1)]
                if pos != st.session_state.player and pos not in [o["pos"] for o in objs]:
                    objs.append({"pos": pos, "type": typ})
                    break
    return objs


# init objects only once
if len(st.session_state.objects) == 0:
    st.session_state.objects = generate_objects(st.session_state.level)
    st.session_state.revealed[0][0] = True


# ==============================
# Fog reveal logic (MODE B)
# ==============================
def reveal_fog(x, y):
    st.session_state.revealed[x][y] = True

    if difficulty == "Hard":
        deltas = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # + shape
    else:
        deltas = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1), (1, 0), (1, 1),
        ]

    for dx, dy in deltas:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID and 0 <= ny < GRID:
            st.session_state.revealed[nx][ny] = True


# ==============================
# Movement & Game Logic
# ==============================
def move(dx, dy):
    x, y = st.session_state.player
    nx, ny = x + dx, y + dy
    if not (0 <= nx < GRID and 0 <= ny < GRID):
        return

    st.session_state.player = [nx, ny]
    reveal_fog(nx, ny)

    for obj in st.session_state.objects[:]:
        if obj["pos"] == [nx, ny]:
            t = obj["type"]
            if t == "treasure":
                st.session_state.score += 10
            elif t == "coin":
                st.session_state.score += 5
            elif t == "heart":
                st.session_state.lives = min(MAX_LIVES, st.session_state.lives + 1)
            elif t == "bomb":
                st.session_state.lives -= 1

            st.session_state.objects.remove(obj)

    if not any(o["type"] == "treasure" for o in st.session_state.objects):
        st.session_state.score += 20
        st.session_state.level += 1
        st.session_state.objects = generate_objects(st.session_state.level)


# ✅ movement FIX (run pending move instantly)
if st.session_state.pending_move:
    dx, dy = st.session_state.pending_move
    move(dx, dy)
    st.session_state.pending_move = None


# ==============================
# UI TOP BAR
# ==============================
left, right = st.columns([2, 1])
with left:
    elapsed = int(time.time() - st.session_state.start_time)
    st.markdown(f"### ⏱ Time: **{elapsed}s**")

with right:
    st.markdown(f"### ❤️ Lives: `{st.session_state.lives}` | ⭐ Score: `{st.session_state.score}`")


# ==============================
# Grid Display
# ==============================
for i in range(GRID):
    row = st.columns(GRID)
    for j in range(GRID):
        if not st.session_state.revealed[i][j]:
            row[j].markdown(f"<h2 style='text-align:center'>{EMOJI['fog']}</h2>", unsafe_allow_html=True)
            continue

        if st.session_state.player == [i, j]:
            row[j].markdown(f"<h2 style='text-align:center'>{EMOJI['player']}</h2>", unsafe_allow_html=True)
        else:
            obj = next((o for o in st.session_state.objects if o["pos"] == [i, j]), None)
            if obj:
                row[j].markdown(f"<h2 style='text-align:center'>{EMOJI[obj['type']]}</h2>", unsafe_allow_html=True)
            else:
                row[j].markdown("<h2 style='text-align:center'>⬜</h2>", unsafe_allow_html=True)


# ==============================
# Controls — Always visible (no scrolling)
# ==============================
st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 1])

with c2:
    if st.button("⬆️"):
        st.session_state.pending_move = (-1, 0)

with c1:
    if st.button("⬅️"):
        st.session_state.pending_move = (0, -1)

with c3:
    if st.button("➡️"):
        st.session_state.pending_move = (0, 1)

with c2:
    if st.button("⬇️"):
        st.session_state.pending_move = (1, 0)


# ==============================
# GAME OVER & Leaderboard
# ==============================
if st.session_state.lives <= 0:
    scores = load_scores()

    scores.append({"score": st.session_state.score, "time": elapsed})
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    save_scores(scores)

    st.error("### 💀 GAME OVER 💀")
    st.write("Top Scores:")
    for idx, s in enumerate(scores, start=1):
        st.write(f"**{idx}. Score:** `{s['score']}` — {s['time']}s")

    st.button("Restart", on_click=lambda: st.session_state.clear())
