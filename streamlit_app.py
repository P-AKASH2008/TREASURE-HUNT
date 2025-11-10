import streamlit as st
import random
import time
import json
from pathlib import Path

# ------------------------------------------------------
# CONFIG
# ------------------------------------------------------
st.set_page_config(page_title="Treasure Hunt", page_icon="💎", layout="wide")

GRID = 6
MAX_LIVES = 3
HIGHSCORE_FILE = Path("highscores.json")

# ------------------------------------------------------
# HIGH SCORE MANAGEMENT
# ------------------------------------------------------
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

# ------------------------------------------------------
# SESSION STATE INIT
# ------------------------------------------------------
defaults = {
    "player": [0, 0],
    "revealed": [[False]*GRID for _ in range(GRID)],
    "objects": [],
    "lives": MAX_LIVES,
    "score": 0,
    "level": 1,
    "move": None,
    "start": time.time(),
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.session_state["revealed"][0][0] = True  # reveal start tile

# ------------------------------------------------------
# GENERATE OBJECTS (NO PNG/GIF, ONLY COLORS)
# ------------------------------------------------------
def generate(level):
    objs = []
    obj_counts = {
        "treasure": 3 + level // 2,
        "coin": 2 + level // 3,
        "heart": 1,
        "bomb": 3 + level // 2,
    }

    def place(obj_type, count):
        for _ in range(count):
            while True:
                pos = [random.randint(0, GRID-1), random.randint(0, GRID-1)]
                if pos != st.session_state.player and pos not in [o["pos"] for o in objs]:
                    objs.append({"pos": pos, "type": obj_type})
                    break

    for t, c in obj_counts.items():
        place(t, c)
    return objs


if not st.session_state["objects"]:
    st.session_state["objects"] = generate(st.session_state["level"])


# ------------------------------------------------------
# MOVEMENT
# ------------------------------------------------------
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

    # Level up
    if not any(o["type"] == "treasure" for o in st.session_state["objects"]):
        st.session_state.score += 20
        st.session_state.level += 1
        st.balloons()
        st.info(f"LEVEL UP 🚀 Now Level {st.session_state.level}")
        st.session_state["objects"] = generate(st.session_state["level"])


# ------------------------------------------------------
# UI THEME (AMAZING LOOK)
# ------------------------------------------------------
UI = """
<style>
body {background: linear-gradient(135deg,#0A2342,#0F4C75);}
.grid {border-collapse: collapse;margin:auto;}
.grid td{
    width:60px;height:60px;text-align:center;
    border:1px solid rgba(255,255,255,0.08);
    font-size:28px;font-weight:600;border-radius:10px;
    transition:0.2s;
}
.hidden {background:#13141f;}
.player {background:#4CC9F0; color:black;}
.treasure {background:#FEE440;color:black;}
.coin {background:#FF9F1C;color:black;}
.heart {background:#FF595E;color:white;}
.bomb {background:#6A040F;color:white;}
.controls button{
    width:80px;height:60px;font-size:32px;
    border-radius:12px;background:#4CC9F0;border:none;color:black;
}
#mobile-controls{position:fixed;bottom:15px;width:100%;text-align:center;}
</style>
"""
st.markdown(UI, unsafe_allow_html=True)

# ------------------------------------------------------
# MAIN LAYOUT
# ------------------------------------------------------
c1, c2 = st.columns([3, 1])

with c1:
    st.markdown(f"### Level: {st.session_state.level} Score: {st.session_state.score} Lives: {st.session_state.lives}")

    elapsed = int(time.time() - st.session_state.start)
    st.markdown(f"⏱ Time: `{elapsed}s`")

    table = "<table class='grid'>"
    for i in range(GRID):
        table += "<tr>"
        for j in range(GRID):
            cell = ""
            css = "hidden"

            if st.session_state.player == [i, j]:
                cell = "🙂"
                css = "player"
            elif st.session_state.revealed[i][j]:
                obj = next((o for o in st.session_state.objects if o["pos"] == [i, j]), None)
                if obj:
                    css = obj["type"]
                    icons = {"treasure": "💎", "coin": "🪙", "heart": "❤️", "bomb": "💣"}
                    cell = icons[obj["type"]]

            table += f"<td class='{css}'>{cell}</td>"
        table += "</tr>"
    table += "</table>"

    st.markdown(table, unsafe_allow_html=True)

# ------------------------------------------------------
# CONTROLS (desktop side, mobile bottom)
# ------------------------------------------------------
with c2:
    st.subheader("Controls")
    if st.button("⬆"):
        move(-1, 0)
    left, right = st.columns(2)
    with left:
        if st.button("⬅"):
            move(0, -1)
    with right:
        if st.button("➡"):
            move(0, 1)
    if st.button("⬇"):
        move(1, 0)

# Mobile controls
st.markdown("""
<div id="mobile-controls">
    <div class='controls'>
        <button onclick="fetch('?move=up')">⬆</button><br>
        <button onclick="fetch('?move=left')">⬅</button>
        <button onclick="fetch('?move=right')">➡</button><br>
        <button onclick="fetch('?move=down')">⬇</button>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------
# GAME OVER
# ------------------------------------------------------
if st.session_state.lives <= 0:
    st.error("GAME OVER 💀")

    name = st.text_input("Enter your name for leaderboard:")
    if st.button("Save score"):
        if name.strip():
            scores.append({"name": name, "score": st.session_state.score})
            scores.sort(key=lambda x: x["score"], reverse=True)
            scores[:] = scores[:10]
            save_scores(scores)
            st.success("Score saved ✅")

    if st.button("Restart"):
        for k in defaults:
            st.session_state[k] = defaults[k]
        st.experimental_rerun()


# ------------------------------------------------------
# SHOW LEADERBOARD
# ------------------------------------------------------
st.sidebar.title("Leaderboard 🏆")
if scores:
    for i, entry in enumerate(scores):
        st.sidebar.write(f"**{i+1}. {entry['name']}** — {entry['score']} pts")
else:
    st.sidebar.write("No scores yet.")
