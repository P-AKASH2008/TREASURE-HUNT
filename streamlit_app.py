import streamlit as st
import random

# ---------------------- SESSION STATE INIT ----------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.size = 10
    st.session_state.player = [0, 0]
    st.session_state.score = 0
    st.session_state.lives = 3
    st.session_state.game_loaded = False  # prevents rerun reset

def reset_game(grid_size):
    st.session_state.size = grid_size
    st.session_state.player = [0, 0]
    st.session_state.score = 0
    st.session_state.lives = 3
    st.session_state.treasure = random_cell()
    st.session_state.coins = random.sample(all_cells(), k=6)
    st.session_state.bombs = random.sample(all_cells(), k=4)
    st.session_state.hearts = random.sample(all_cells(), k=2)

def random_cell():
    size = st.session_state.size
    return [random.randint(0, size - 1), random.randint(0, size - 1)]

def all_cells():
    size = st.session_state.size
    return [[r, c] for r in range(size) for c in range(size)]

# ---------------------- MOVEMENT ----------------------
def move(direction):
    r, c = st.session_state.player
    size = st.session_state.size

    if direction == "up" and r > 0:
        r -= 1
    elif direction == "down" and r < size - 1:
        r += 1
    elif direction == "left" and c > 0:
        c -= 1
    elif direction == "right" and c < size - 1:
        c += 1

    st.session_state.player = [r, c]

    # Actions
    if [r, c] in st.session_state.coins:
        st.session_state.score += 10
        st.session_state.coins.remove([r, c])

    if [r, c] in st.session_state.hearts:
        st.session_state.lives += 1
        st.session_state.hearts.remove([r, c])

    if [r, c] in st.session_state.bombs:
        st.session_state.lives -= 1
        st.session_state.bombs.remove([r, c])

    if st.session_state.lives <= 0:
        st.error("💥 GAME OVER! Lives exhausted.")
        st.session_state.game_loaded = False

    if [r, c] == st.session_state.treasure:
        st.success("💎 You found the treasure!")
        st.session_state.game_loaded = False

# ---------------------- SIDEBAR UI ----------------------
st.sidebar.title("🥷 Controls")

difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"], key="diff")

# Only reset when difficulty is manually changed
if not st.session_state.game_loaded:
    st.session_state.game_loaded = True
    if difficulty == "Easy":
        reset_game(8)
    elif difficulty == "Medium":
        reset_game(10)
    else:
        reset_game(12)

# Movement controls (symmetrical layout)
st.sidebar.write("### Movement")
col_up = st.sidebar.columns([1, 1, 1])
col_mid = st.sidebar.columns([1, 1, 1])

if col_up[1].button("⬆", key="btn_up"):
    move("up")
if col_mid[0].button("⬅", key="btn_left"):
    move("left")
if col_mid[2].button("➡", key="btn_right"):
    move("right")
if st.sidebar.button("⬇", key="btn_down"):
    move("down")

st.sidebar.write("---")
st.sidebar.write(f"⭐ **Score:** {st.session_state.score}")
st.sidebar.write(f"❤️ **Lives:** {st.session_state.lives}")

# ---------------------- GRID DISPLAY ----------------------
st.title("🏴‍☠️ Treasure Hunt")

size = st.session_state.size
pr, pc = st.session_state.player

for r in range(size):
    cols = st.columns(size)
    for c in range(size):

        visible = abs(r - pr) <= 1 and abs(c - pc) <= 1

        cell = "❓"
        if visible:
            if [r, c] == [pr, pc]:
                cell = "🧛‍♂️"
            elif [r, c] == st.session_state.treasure:
                cell = "💎"
            elif [r, c] in st.session_state.coins:
                cell = "📀"
            elif [r, c] in st.session_state.bombs:
                cell = "💣"
            elif [r, c] in st.session_state.hearts:
                cell = "❤️"
            else:
                cell = "⬜"

        cols[c].markdown(f"<div style='text-align:center;font-size:26px'>{cell}</div>", unsafe_allow_html=True)
