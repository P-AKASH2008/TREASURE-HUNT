import streamlit as st
import random

st.set_page_config(page_title="Treasure Hunt", layout="wide")

# ========== Difficulty Reset ==========
new_diff = st.sidebar.selectbox("🎮 Difficulty", ["Easy", "Medium", "Hard"])

if new_diff != st.session_state.get("difficulty", None):
    st.session_state.clear()
    st.session_state.difficulty = new_diff

# ========== Game Setup ==========
if "grid" not in st.session_state:
    size = {"Easy": 6, "Medium": 8, "Hard": 10}[st.session_state.difficulty]
    st.session_state.rows = size
    st.session_state.cols = size
    st.session_state.player = [size // 2, size // 2]  # Start at center

    # Symbols
    st.session_state.ninja = "🥷"
    st.session_state.treasure = "💿"   # Golden DVD
    st.session_state.bomb = "💣"
    st.session_state.fog = "❓"

    # Grid elements
    st.session_state.grid = [["" for _ in range(size)] for _ in range(size)]
    st.session_state.revealed = [[False for _ in range(size)] for _ in range(size)]

    # Random bomb & treasure placement
    positions = [(r, c) for r in range(size) for c in range(size)]
    positions.remove(tuple(st.session_state.player))
    random.shuffle(positions)

    st.session_state.treasure_pos = positions.pop()
    st.session_state.bomb_pos = positions.pop()

    st.session_state.grid[st.session_state.treasure_pos[0]][st.session_state.treasure_pos[1]] = st.session_state.treasure
    st.session_state.grid[st.session_state.bomb_pos[0]][st.session_state.bomb_pos[1]] = st.session_state.bomb

    st.session_state.game_over = False


# ========== Reveal Area Around Player ==========
def reveal_around():
    r, c = st.session_state.player
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < st.session_state.rows and 0 <= nc < st.session_state.cols:
                st.session_state.revealed[nr][nc] = True


reveal_around()


# ========== Movement Function ==========
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
            st.error("💣 You hit a bomb!")


# ========== SIDEBAR CONTROLS ==========
st.sidebar.write("### 🕹 Controls")

up = st.sidebar.button("⬆️ Up")

c1, _, c3 = st.sidebar.columns([1, 0.2, 1])
left = c1.button("⬅️ Left")
right = c3.button("➡️ Right")

down = st.sidebar.button("⬇️ Down")

if up:
    move(-1, 0)
if down:
    move(1, 0)
if left:
    move(0, -1)
if right:
    move(0, 1)


# ========== GAME GRID ==========
st.title("🟪 Treasure Hunt")

for r in range(st.session_state.rows):
    cols = st.columns(st.session_state.cols)
    for c in range(st.session_state.cols):

        if [r, c] == st.session_state.player:
            cols[c].button(st.session_state.ninja, key=f"p-{r}-{c}")
        else:
            if st.session_state.revealed[r][c]:
                emoji = st.session_state.grid[r][c]
                cols[c].button(emoji if emoji != "" else " ", key=f"{r}-{c}")
            else:
                cols[c].button(st.session_state.fog, key=f"fog-{r}-{c}")
