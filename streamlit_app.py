import streamlit as st
import random

st.set_page_config(page_title="Treasure Hunt", layout="wide")

# ===========================
# DIFFICULTY DROPDOWN
# ===========================
new_diff = st.sidebar.selectbox("🎮 Difficulty", ["Easy", "Medium", "Hard"])
if new_diff != st.session_state.get("difficulty", None):
    st.session_state.clear()
    st.session_state.difficulty = new_diff


# ===========================
# GAME SETUP
# ===========================
if "grid" not in st.session_state:
    size = {"Easy": 6, "Medium": 8, "Hard": 10}[st.session_state.difficulty]

    st.session_state.rows = size
    st.session_state.cols = size

    st.session_state.player = [size // 2, size // 2]  # start at center

    st.session_state.ninja = "🥷"
    st.session_state.treasure = "💿"
    st.session_state.bomb = "💣"
    st.session_state.fog = "❓"

    # create empty grid
    st.session_state.grid = [["" for _ in range(size)] for _ in range(size)]

    # place treasure and bomb randomly
    cells = [(r, c) for r in range(size) for c in range(size)]
    random.shuffle(cells)

    st.session_state.treasure_pos = cells.pop()
    st.session_state.bomb_pos = cells.pop()

    tr, tc = st.session_state.treasure_pos
    br, bc = st.session_state.bomb_pos
    st.session_state.grid[tr][tc] = st.session_state.treasure
    st.session_state.grid[br][bc] = st.session_state.bomb

    st.session_state.game_over = False


# ===========================
# MOVEMENT FUNCTION
# ===========================
def move(dr, dc):
    if st.session_state.game_over:
        return

    r, c = st.session_state.player
    nr, nc = r + dr, c + dc

    # bounds check
    if 0 <= nr < st.session_state.rows and 0 <= nc < st.session_state.cols:
        st.session_state.player = [nr, nc]

        if (nr, nc) == st.session_state.treasure_pos:
            st.session_state.game_over = True
            st.success("🎉 You found the treasure!")

        elif (nr, nc) == st.session_state.bomb_pos:
            st.session_state.game_over = True
            st.error("💣 Boom! You stepped on a bomb!")


# ===========================
# SIDEBAR CONTROLS (D-PAD)
# ===========================
st.sidebar.write("## 🕹 Controls")

ctrl = st.sidebar.container()

#     ⬆️
# ⬅️     ➡️
#     ⬇️
up = ctrl.button("⬆️ Up", use_container_width=True)

left_col, mid_gap, right_col = ctrl.columns([1, 0.3, 1])
left = left_col.button("⬅️ Left", use_container_width=True)
right = right_col.button("➡️ Right", use_container_width=True)
down = ctrl.button("⬇️ Down", use_container_width=True)

if up: move(-1, 0)
if down: move(1, 0)
if left: move(0, -1)
if right: move(0, 1)


# ===========================
# GAME DISPLAY — FOG LOGIC
# ===========================
st.title("Treasure Hunt")

game = st.container()

pr, pc = st.session_state.player

for r in range(st.session_state.rows):
    cols = game.columns(st.session_state.cols, gap="small")
    for c in range(st.session_state.cols):

        # 🔥 only reveal 8 surrounding blocks of the ninja
        if abs(r - pr) <= 1 and abs(c - pc) <= 1:
            cell = st.session_state.grid[r][c]

            if [r, c] == st.session_state.player:
                cols[c].button(st.session_state.ninja, key=f"p-{r}-{c}")
            else:
                cols[c].button(cell if cell != "" else " ", key=f"{r}-{c}")

        else:
            cols[c].button(st.session_state.fog, key=f"fog-{r}-{c}")
