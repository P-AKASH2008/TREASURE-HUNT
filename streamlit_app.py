import streamlit as st
import random

# ---------------------- SESSION STATE INIT ----------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.size = 10  # default grid size (Difficulty modifies this)
    st.session_state.player = [0, 0]
    st.session_state.score = 0
    st.session_state.lives = 3

def reset_game(grid_size):
    st.session_state.size = grid_size
    st.session_state.player = [0, 0]
    st.session_state.score = 0
    st.session_state.lives = 3

    # spawn objects
    st.session_state.treasure = random_cell()
    st.session_state.coins = random.sample(all_cells(), k=5)
    st.session_state.bombs = random.sample(all_cells(), k=4)
    st.session_state.hearts = random.sample(all_cells(), k=2)

def random_cell():
    size = st.session_state.size
    return [random.randint(0, size - 1), random.randint(0, size - 1)]

def all_cells():
    size = st.session_state.size
    return [[r, c] for r in range(size) for c in range(size)]

# ---------------------- MOVEMENT ----------------------
def move_player(direction):
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

    # --- interactions ---
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
        st.error("💥 GAME OVER! Out of lives.")
        reset_game(st.session_state.size)

    if [r, c] == st.session_state.treasure:
        st.success("💎 You found the treasure!")
        reset_game(st.session_state.size)


# ---------------------- UI SIDEBAR ----------------------
st.sidebar.title("🕹 Controls")

difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

if difficulty == "Easy":
    reset_game(8)
elif difficulty == "Medium":
    reset_game(10)
else:
    reset_game(12)

st.sidebar.write("### Movement")
col_btn1, col_btn2 = st.sidebar.columns(2)

if col_btn1.button("⬆ Up"):
    move_player("up")
if col_btn1.button("⬅ Left"):
    move_player("left")
if col_btn2.button("➡ Right"):
    move_player("right")
if col_btn2.button("⬇ Down"):
    move_player("down")

st.sidebar.write("---")
st.sidebar.write(f"**Score:** {st.session_state.score}")
st.sidebar.write(f"**Lives:** {st.session_state.lives}")

# ---------------------- GRID RENDER ----------------------
st.title("🏴‍☠️ Treasure Hunt")

size = st.session_state.size
pr, pc = st.session_state.player

for r in range(size):
    row = st.columns(size)
    for c in range(size):

        visible = (abs(r - pr) <= 1 and abs(c - pc) <= 1)

        cell = "❓"  # fog

        if visible:
            if [r, c] == [pr, pc]:
                cell = "🧛‍♂️"
            elif [r, c] == st.session_state.treasure:
                cell = "💎"
            elif [r, c] in st.session_state.coins:
                cell = "📀"
            elif [r, c] in st.session_state.hearts:
                cell = "❤️"
            elif [r, c] in st.session_state.bombs:
                cell = "💣"
            else:
                cell = "⬜"

        row[c].write(f"<h3 style='text-align:center'>{cell}</h3>", unsafe_allow_html=True)
