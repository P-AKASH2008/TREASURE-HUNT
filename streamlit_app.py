# streamlit_app.py  (NO SCROLL NEEDED FOR CONTROLS)
import streamlit as st
import random, json, time
from pathlib import Path

st.set_page_config(page_title="Treasure Hunt", page_icon="💎", layout="wide")

GRID = 6
MAX_LIVES = 3
HIGHSCORE_FILE = Path("highscores.json")

EMOJI = {
    "player": "🧍‍♂️",   # your ninja can be replaced with your PNG later
    "treasure": "💎",
    "coin": "📀",
    "bomb": "💣",
    "heart": "❤️",
    "fog": "❔",
    "empty": "⬜"
}

# ---------------- STATE ----------------
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
if "pending" not in st.session_state:
    st.session_state.pending = None
if "start" not in st.session_state:
    st.session_state.start = time.time()

st.session_state.revealed[0][0] = True


# ---------------- OBJECT GEN ----------------
def gen_objs():
    objs = []
    for t, c in {"treasure":3, "coin":4, "heart":1, "bomb":3}.items():
        for _ in range(c):
            while True:
                pos = [random.randint(0, GRID-1), random.randint(0, GRID-1)]
                if pos != [0,0] and pos not in [o["pos"] for o in objs]:
                    objs.append({"pos": pos, "type": t})
                    break
    return objs

if not st.session_state.objects:
    st.session_state.objects = gen_objs()


# ---------------- FOG LOGIC ----------------
def reveal(x,y):
    st.session_state.revealed[x][y] = True
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            nx, ny = x+dx, y+dy
            if 0<=nx<GRID and 0<=ny<GRID:
                st.session_state.revealed[nx][ny] = True


# ---------------- MOVE ----------------
def move(dx,dy):
    x,y = st.session_state.player
    nx, ny = x+dx, y+dy
    if not (0<=nx<GRID and 0<=ny<GRID):
        return

    st.session_state.player = [nx,ny]
    reveal(nx,ny)

    for o in st.session_state.objects[:]:
        if o["pos"] == [nx,ny]:
            if o["type"]=="treasure":
                st.session_state.score += 10
            elif o["type"]=="coin":
                st.session_state.score += 5
            elif o["type"]=="heart":
                st.session_state.lives = min(MAX_LIVES, st.session_state.lives+1)
            elif o["type"]=="bomb":
                st.session_state.lives -= 1
            st.session_state.objects.remove(o)


# execute pending move on rerun
if st.session_state.pending:
    dx,dy = st.session_state.pending
    st.session_state.pending = None
    move(dx,dy)


# ---------------- CSS — FIX BOTTOM CONTROLLER ----------------
st.markdown("""
<style>
body { margin:0; padding:0; overflow-x:hidden; }

.controller {
  position: fixed;
  bottom: 15px;
  left: 50%;
  transform: translateX(-50%);
  display: grid;
  grid-template-columns: 60px 60px 60px;
  gap: 6px;
  z-index: 100;
}

.ctrl-btn {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  font-size: 26px;
  border: none;
  background: #00B4FF;
}
@media (max-width: 600px) {
  .ctrl-btn { width: 17vw; height: 17vw; font-size: 9vw; }
}
</style>
""", unsafe_allow_html=True)


# ---------------- HEADER ----------------
left, right = st.columns([2,1])
with left:
    st.markdown(f"### Treasure Hunt — Level {st.session_state.level}")
with right:
    st.markdown(f"⏱ {int(time.time()-st.session_state.start)}s • ❤️ `{st.session_state.lives}` • ⭐ `{st.session_state.score}`")


# ---------------- GRID ----------------
for r in range(GRID):
    row = st.columns(GRID)
    for c,col in enumerate(row):
        if [r,c] == st.session_state.player:
            col.markdown(f"<h3 style='text-align:center'>{EMOJI['player']}</h3>", unsafe_allow_html=True)
            continue

        if not st.session_state.revealed[r][c]:
            col.markdown(f"<h3 style='text-align:center'>{EMOJI['fog']}</h3>", unsafe_allow_html=True)
            continue

        o = next((o for o in st.session_state.objects if o["pos"]==[r,c]), None)
        icon = EMOJI[o["type"]] if o else EMOJI["empty"]
        col.markdown(f"<h3 style='text-align:center'>{icon}</h3>", unsafe_allow_html=True)


# ---------------- FIXED CONTROLLER (SYMMETRIC) ----------------
st.markdown("""
<div class="controller">
    <div></div>
    <form action="?up" method="post"><button class="ctrl-btn">⬆️</button></form>
    <div></div>
    <form action="?left" method="post"><button class="ctrl-btn">⬅️</button></form>
    <div></div>
    <form action="?right" method="post"><button class="ctrl-btn">➡️</button></form>
    <div></div>
    <form action="?down" method="post"><button class="ctrl-btn">⬇️</button></form>
    <div></div>
</div>
""", unsafe_allow_html=True)


# capture direction
qs = st.query_params
if "up" in qs: st.session_state.pending = (-1,0)
if "down" in qs: st.session_state.pending = (1,0)
if "left" in qs: st.session_state.pending = (0,-1)
if "right" in qs: st.session_state.pending = (0,1)
