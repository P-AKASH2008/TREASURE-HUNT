import streamlit as st
import random
import json
import time
from pathlib import Path

st.set_page_config(page_title="Treasure Hunt Ninja", page_icon="🥷", layout="wide")

GRID = 6
MAX_LIVES = 3

HIGHSCORE_FILE = Path("highscores.json")

# -------------------------
# Load / Save highscores
# -------------------------
def load_scores():
    if HIGHSCORE_FILE.exists():
        try:
            return json.loads(HIGHSCORE_FILE.read_text())
        except:
            return []
    return []

def save_scores(data):
    HIGHSCORE_FILE.write_text(json.dumps(data, indent=4))


scores = load_scores()

# -------------------------
# Session defaults
# -------------------------
defaults = {
    "player": [0, 0],
    "revealed": [[False]*GRID for _ in range(GRID)],
    "objects": [],
    "lives": MAX_LIVES,
    "score": 0,
    "level": 1,
    "start": time.time(),
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

st.session_state.revealed[0][0] = True  # reveal start tile

# -------------------------
# Generate objects
# -------------------------
def generate_objects(level):
    objs = []

    obj_counts = {
        "treasure": 3 + level // 2,
        "coin": 3,
        "heart": 1,
        "bomb": 2 + level // 2,
    }

    for typ, count in obj_counts.items():
        for _ in range(count):
            while True:
                pos = [random.randint(0, GRID-1), random.randint(0, GRID-1)]
                if pos != st.session_state.player and pos not in [o["pos"] for o in objs]:
                    objs.append({"pos": pos, "type": typ})
                    break

    return objs


if not st.session_state["objects"]:
    st.session_state["objects"] = generate_objects(st.session_state["level"])


# -------------------------
# Move
# -------------------------
def move(dx, dy):
    x, y = st.session_state.player
    nx, ny = x + dx, y + dy

    if not (0 <= nx < GRID and 0 <= ny < GRID):
        return

    st.session_state.player = [nx, ny]
    st.session_state.revealed[nx][ny] = True

    for obj in st.session_state["objects"][:]:
        if obj["pos"] == [nx, ny]:
            t = obj["type"]

            if t == "treasure":
                st.session_state.score += 10
                st.success("💎 Treasure +10")
            elif t == "coin":
                st.session_state.score += 5
                st.info("🪙 Coin +5")
            elif t == "heart":
                st.session_state.lives = min(MAX_LIVES, st.session_state.lives + 1)
                st.success("❤️ +1 Life")
            elif t == "bomb":
                st.session_state.score -= 5
                st.session_state.lives -= 1
                st.error("💣 Bomb! -5 & -1 life")

            st.session_state["objects"].remove(obj)

    # level up when treasure exhausted
    if not any(o["type"] == "treasure" for o in st.session_state["objects"]):
        st.session_state.score += 20
        st.session_state.level += 1
        st.balloons()
        st.info(f"LEVEL UP 🚀 Level {st.session_state.level}")
        st.session_state["objects"] = generate_objects(st.session_state["level"])


# -------------------------
# CSS UI Styling
# -------------------------
st.markdown("""
<style>
body {background: #0D1B2A;}
.grid td {
    width: 60px; height: 60px; text-align: center;
    font-size: 32px; border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
}
.hidden {background:#1b263b; color:#415a77;}
.player {background:#4CC9F0;}
.treasure {background:#FEE440;}
.coin {background:#FF9F1C;}
.heart {background:#E63946; color:white;}
.bomb {background:#6A040F; color:white;}
.control-btn{
    width:70px;height:55px;font-size:28px;
    background:#4CC9F0;border-radius:12px;
    border:none;color:black;
}
</style>
""", unsafe_allow_html=True)


# -------------------------
# Layout: Grid + Controls
# -------------------------
col_grid, col_controls = st.columns([3, 1])

with col_grid:
    st.markdown(f"### 🥷 Ninja Treasure Hunt")
    st.markdown(f"**Level:** {st.session_state.level}  **Score:** {st.session_state.score}  **Lives:** {st.session_state.lives}")

    elapsed = int(time.time() - st.session_state.start)
    st.markdown(f"⏱ Time: `{elapsed}s`")

    icons = {"treasure": "💎", "coin": "🪙", "heart": "❤️", "bomb": "💣"}

    table = "<table class='grid'>"
    for i in range(GRID):
        table += "<tr>"
        for j in range(GRID):
            cell = "?"
            css = "hidden"

            if st.session_state.player == [i, j]:
                cell = "🥷"
                css = "player"
            elif st.session_state.revealed[i][j]:
                obj = next((o for o in st.session_state.objects if o["pos"] == [i, j]), None)
                if obj:
                    css = obj["type"]
                    cell = icons[obj["type"]]
                else:
                    cell = ""

            table += f"<td class='{css}'>{cell}</td>"
        table += "</tr>"
    table += "</table>"

    st.markdown(table, unsafe_allow_html=True)

# -------------------------
# Controls (Symmetric D-pad)
# -------------------------
with col_controls:
    st.markdown("### Move")

    up = st.button("⬆", key="up", help="Move up", use_container_width=True)

    c1, c2, c3 = st.columns([1, 1, 1])
    left = c1.button("⬅", key="left", help="Move left")
    right = c3.button("➡", key="right", help="Move right")

    down = st.button("⬇", key="down", help="Move down", use_container_width=True)

    if up: move(-1, 0)
    if down: move(1, 0)
    if left: move(0, -1)
    if right: move(0, 1)


# -------------------------
# GAME OVER / SAVE SCORE
# -------------------------
if st.session_state.lives <= 0:
    st.error("GAME OVER 💀")

    name = st.text_input("Enter your name:")
    if st.button("Save Score"):
        if name.strip():
            scores.append({"name": name, "score": st.session_state.score})
            scores.sort(key=lambda x: x["score"], reverse=True)
            scores[:] = scores[:10]
            save_scores(scores)
            st.success("Score Saved ✅")

    if st.button("Restart Game"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.experimental_rerun()


# -------------------------
# Leaderboard (sidebar)
# -------------------------
st.sidebar.title("🏆 Leaderboard")
if scores:
    for i, entry in enumerate(scores):
        st.sidebar.write(f"**{i+1}. {entry['name']} — {entry['score']} pts**")
else:
    st.sidebar.write("No scores yet.")

