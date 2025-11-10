import streamlit as st
import random
import time

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")

# ---------------------------------------------------
# CSS FIXES (Ninja visibility + Symmetric Buttons)
# ---------------------------------------------------
st.markdown("""
<style>
button[kind="secondary"] {
    border-radius: 12px !important;
    height: 48px !important;
    width: 90px !important;
    font-size: 24px !important;
}

.ninja {
    font-size: 38px !important;
    display: flex;
    justify-content: center;
}

.gridcell {
    font-size: 32px;
    text-align: center;
    padding: 6px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# INITIAL GAME SETUP
# ---------------------------------------------------
def init_game():
    size_map = {"Easy": 8, "Medium": 10, "Hard": 12}
    st.session_state.size = size_map[st.session_state.difficulty]

    size = st.session_state.size
    st.session_state.player = [size // 2, size // 2]
    st.session_state.coins = []
    st.session_state.bombs = []
    st.session_state.hearts = []
    st.session_state.score = 0
    st.session_state.lives = 3

    # Place treasure
    while True:
        tr = [random.randint(0, size - 1), random.randint(0, size - 1)]
        if tr != st.session_state.player:
            st.session_state.treasure = tr
            break

    # Place coins / bombs / hearts
    for _ in range(size // 2):
        place_random(st.session_state.coins)
    for _ in range(size // 3):
        place_random(st.session_state.bombs)
    for _ in range(size // 4):
        place_random(st.session_state.hearts)

    # fog
    st.session_state.revealed = [[False] * size for _ in range(size)]
    reveal_area()


def place_random(container):
    size = st.session_state.size
    while True:
        cell = [random.randint(0, size - 1), random.randint(0, size - 1)]
        if cell != st.session_state.player and \
           cell not in st.session_state.coins and \
           cell not in st.session_state.bombs and \
           cell not in st.session_state.hearts and \
           cell != st.session_state.treasure:
            container.append(cell)
            return


def reveal_area():
    size = st.session_state.size
    pr, pc = st.session_state.player

    st.session_state.revealed = [[False] * size for _ in range(size)]

    for r in range(pr - 1, pr + 2):
        for c in range(pc - 1, pc + 2):
            if 0 <= r < size and 0 <= c < size:
                st.session_state.revealed[r][c] = True


def move(dr, dc):
    size = st.session_state.size
    r, c = st.session_state.player
    nr, nc = r + dr, c + dc

    if 0 <= nr < size and 0 <= nc < size:
        st.session_state.player = [nr, nc]
        reveal_area()
        evaluate_tile()


def evaluate_tile():
    pos = st.session_state.player

    if pos in st.session_state.coins:
        st.session_state.score += 10
        st.session_state.coins.remove(pos)

    if pos in st.session_state.hearts:
        st.session_state.lives += 1
        st.session_state.hearts.remove(pos)

    if pos in st.session_state.bombs:
        st.session_state.lives -= 1
        st.session_state.bombs.remove(pos)

        if st.session_state.lives <= 0:
            st.error("💥 Game Over! No lives left.")
            time.sleep(1)
            init_game()
            st.rerun()

    if pos == st.session_state.treasure:
        st.success("💎 You found the Treasure!")
        st.balloons()
        time.sleep(1)
        init_game()
        st.rerun()


# ---------------------------------------------------
# SIDEBAR (UI CONTROL)
# ---------------------------------------------------
st.sidebar.title("🎮 Controls")

st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"], key="difficulty", on_change=init_game)

st.sidebar.write("### 🧿 Scoreboard")
st.sidebar.write(f"⭐ Score: **{st.session_state.get('score',0)}**")
st.sidebar.write(f"❤️ Lives: **{st.session_state.get('lives',3)}**")

st.sidebar.write("---")
st.sidebar.write("### 🕹 Movement")

ctrl = st.sidebar.container()
up = ctrl.button("⬆️")
col1, _, col2 = ctrl.columns([1, 0.3, 1])
left = col1.button("⬅️")
right = col2.button("➡️")
down = ctrl.button("⬇️")

if up: move(-1, 0)
if down: move(1, 0)
if left: move(0, -1)
if right: move(0, 1)

# ---------------------------------------------------
# MAIN GAME UI GRID
# ---------------------------------------------------
st.title("🗺️ Treasure Hunt")

if "player" not in st.session_state:
    init_game()

size = st.session_state.size

for r in range(size):
    cols = st.columns(size)
    for c in range(size):

        if [r, c] == st.session_state.player:
            cols[c].markdown("<div class='ninja'>🥷</div>", unsafe_allow_html=True)

        elif st.session_state.revealed[r][c]:
            if [r, c] == st.session_state.treasure:
                cols[c].markdown("<div class='gridcell'>💎</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state.coins:
                cols[c].markdown("<div class='gridcell'>📀</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state.bombs:
                cols[c].markdown("<div class='gridcell'>💣</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state.hearts:
                cols[c].markdown("<div class='gridcell'>❤️</div>", unsafe_allow_html=True)
            else:
                cols[c].markdown("<div class='gridcell'>⬜</div>", unsafe_allow_html=True)

        else:
            cols[c].markdown("<div class='gridcell'>❓</div>", unsafe_allow_html=True)
