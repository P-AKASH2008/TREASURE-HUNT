import streamlit as st
import random

st.set_page_config(page_title="Treasure Hunt", layout="wide")

# ----------- DIFFICULTY CHANGE -----------
new_diff = st.sidebar.selectbox("🎮 Difficulty", ["Easy", "Medium", "Hard"])
if new_diff != st.session_state.get("difficulty", None):
    st.session_state.clear()
    st.session_state.difficulty = new_diff

# ----------- GAME SETUP -----------
if "grid" not in st.session_state:
    size = {"Easy": 6, "Medium": 8, "Hard": 10}[st.session_state.difficulty]

    st.session_state.rows = size
    st.session_state.cols = size
    st.session_state.player = [size // 2, size // 2]

    st.session_state.ninja = "🥷"
    st.session_state.treasure = "💿"
    st.session_state.bomb = "💣"
    st.session_state.fog = "❓"

    st.session_state.grid = [["" for _ in range(size)] for _ in range(size)]
    st.session_state.revealed = [[False for _ in range(size)] for _ in range(size)]

    # random bomb + treasure
    choices = [(r, c) for r in range(size) for c in range(size)]
    choices.remove(tuple(st.session_state.player))
    random.shuffle(choices)

    st.session_state.treasure_pos = choices.pop()
    st.session_state.bomb_pos = choices.pop()

    st.session_state.grid[st.session_state.treasure_pos[0]][st.session_state.treasure_pos[1]] = st.session_state.treasure
    st.session_state.grid[st.session_state.bomb_pos[0]][st.session_state.bomb_pos[1]] = st.session_state.bomb

    st.session_state.game_over = False


# ----------- REVEAL AROUND PLAYER -----------
def reveal_around():
    r, c = st.session_state.player
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < st.session_state.rows and 0 <= nc < st.session_state.cols:
                st.session_state.revealed[nr][nc] = True


reveal_around()


# ----------- MOVEMENT FUNCTION -----------
def move(dr, dc):
    if st.session_state.game_over:
        return

    r, c = st.session_state.player
    nr, nc = r + dr, c + dc

    if 0 <= nr < st.session_state.rows and 0 <= nc < st.session_state.cols:
        st.session_state.player = [nr, nc]
        reveal_around()

        if (nr, nc) == st.session_state.treasure_pos:
            st.session_state.game_over = True
            st.success("🎉 You found the treasure!")

        elif (nr, nc) == st.session_state.bomb_pos:
            st.session_state.game_over = True
            st.error("💣 You stepped on a bomb!")


# ----------- SIDEBAR CONTROLLERS (FIXED SIZE) -----------
st.sidebar.write("## 🕹 Controls")

ctrl = st.sidebar.container()

# layout:
#      [ Up ]
# [ Left ][ Right ]
#      [ Down ]

ctrl_up = ctrl.button("⬆️ Up", use_container_width=True)

left_col, space, right_col = ctrl.columns([1, 0.2, 1])
ctrl_left = left_col.button("⬅️ Left", use_container_width=True)
ctrl_right = right_col.button("➡️ Right", use_container_width=True)

ctrl_down = ctrl.button("⬇️ Down", use_container_width=True)

if ctrl_up: move(-1, 0)
if ctrl_down: move(1, 0)
if ctrl_left: move(0, -1)
if ctrl_right: move(0, 1)


# ----------- GAME DISPLAY -----------
st.title("Treasure Hunt")

game_holder = st.container()
for r in range(st.session_state.rows):
    cols = game_holder.columns(st.session_state.cols, gap="small")
    for c in range(st.session_state.cols):
        if [r, c] == st.session_state.player:
            cols[c].button(st.session_state.ninja, key=f"p-{r}-{c}")
        else:
            if st.session_state.revealed[r][c]:
                cols[c].button(st.session_state.grid[r][c], key=f"{r}-{c}")
            else:
                cols[c].button(st.session_state.fog, key=f"fog-{r}-{c}")
