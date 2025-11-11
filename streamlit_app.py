# streamlit_app.py
import streamlit as st
import random
import time

st.set_page_config(page_title="Treasure Hunt", layout="wide")

# ============ STYLE (compact + centered + square tiles) ============
st.markdown("""
<style>
.game-grid {
    max-width: 520px;        /* ✅ keeps grid smaller */
    margin-left: auto;
    margin-right: auto;      /* ✅ centers grid */
}
.tile {
    aspect-ratio: 1 / 1;     /* ✅ perfect square */
    width: 100%;
    background-color: #0b1220;  /* ✅ match background */
    border-radius: 6px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 26px;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# SAFE SESSION INIT
# ======================================================
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.difficulty = "Medium"
    st.session_state.score = 0
    st.session_state.lives = 2
    st.session_state.moves = 0
    st.session_state.max_moves = 0
    st.session_state.grid_size = 0
    st.session_state.player = [0, 0]
    st.session_state.treasure = [0, 0]
    st.session_state.coins = []
    st.session_state.bombs = []
    st.session_state.hearts = []


# Helpers
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def all_cells(n): return [[r, c] for r in range(n) for c in range(n)]

def sample(n, avoid, count):
    pool = [p for p in all_cells(n) if p not in avoid]
    return random.sample(pool, min(count, len(pool)))


# ======================================================
# GAME INITIALIZATION
# ======================================================
def init_game(diff=None):
    if diff:
        st.session_state.difficulty = diff

    diff = st.session_state.difficulty

    # ✅ Grid size
    grid_map = {"Easy": 8, "Medium": 10, "Hard": 12}
    st.session_state.grid_size = grid_map.get(diff, 10)

    # ✅ Lives based on difficulty
    lives_map = {"Easy": 3, "Medium": 2, "Hard": 1}
    st.session_state.lives = lives_map.get(diff, 2)

    size = st.session_state.grid_size
    center = [size // 2, size // 2]
    st.session_state.player = center.copy()

    # reset main stats
    st.session_state.score = 0
    st.session_state.moves = 0

    # Place treasure
    cells = all_cells(size)
    cells.remove(center)
    treasure = random.choice(cells)
    st.session_state.treasure = treasure

    # Item densities (compact & rich)
    coins = max(6, size // 2)
    bombs = max(4, size // 3)
    hearts = max(1, size // 6)

    # place items
    st.session_state.coins = sample(size, [center, treasure], coins)

    avoid = [center, treasure] + st.session_state.coins
    st.session_state.bombs = sample(size, avoid, bombs)

    avoid += st.session_state.bombs
    st.session_state.hearts = sample(size, avoid, hearts)

    # move limit = shortest path + 5
    st.session_state.max_moves = manhattan(center, treasure) + 5

    st.session_state.initialized = True


# FIRST LOAD
if not st.session_state.initialized:
    init_game(st.session_state.difficulty)


# ======================================================
# MOVEMENT
# ======================================================
def move(dir):
    size = st.session_state.grid_size
    r, c = st.session_state.player

    if dir == "up" and r > 0: r -= 1
    elif dir == "down" and r < size - 1: r += 1
    elif dir == "left" and c > 0: c -= 1
    elif dir == "right" and c < size - 1: c += 1
    else: return

    st.session_state.player = [r, c]
    st.session_state.moves += 1

    # coin
    if [r, c] in st.session_state.coins:
        st.session_state.score += 10
        st.session_state.coins.remove([r, c])
        st.success("📀 +10 coins")

    # heart
    if [r, c] in st.session_state.hearts:
        st.session_state.lives += 1
        st.session_state.hearts.remove([r, c])
        st.success("❤️ +1 life")

    # bomb
    if [r, c] in st.session_state.bombs:
        st.session_state.lives -= 1
        st.session_state.bombs.remove([r, c])
        st.error("💣 -1 life")

    # treasure
    if [r, c] == st.session_state.treasure:
        st.session_state.score += 20
        st.success("💎 Treasure found! +20 score")
        time.sleep(0.7)
        init_game(st.session_state.difficulty)
        return

    # Moves finished?
    if st.session_state.moves >= st.session_state.max_moves:
        st.session_state.lives -= 1
        st.error("⌛ Out of moves -1 life")
        time.sleep(0.7)

        if st.session_state.lives <= 0:
            st.error("💀 Game Over")
            init_game(st.session_state.difficulty)
        else:
            init_game(st.session_state.difficulty)


# ======================================================
# SIDEBAR PANEL
# ======================================================
with st.sidebar:
    st.title("⚙ Game Panel")

    diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"],
                        index=["Easy","Medium","Hard"].index(st.session_state.difficulty),
                        on_change=lambda: init_game(diff))

    st.subheader("Stats")
    st.write(f"🏆 Score: **{st.session_state.score}**")
    st.write(f"❤️ Lives: **{st.session_state.lives}**")
    st.write(f"🚶 Moves: **{st.session_state.moves}/{st.session_state.max_moves}**")

    st.subheader("Controls")
    u, r = st.columns(2)
    with u: st.button("⬆ Up", on_click=move, args=("up",))
    with r: st.button("➡ Right", on_click=move, args=("right",))

    d, l = st.columns(2)
    with d: st.button("⬇ Down", on_click=move, args=("down",))
    with l: st.button("⬅ Left", on_click=move, args=("left",))

    st.button("🔄 Restart", on_click=lambda: init_game(st.session_state.difficulty))

    st.markdown("---")
    st.subheader("How to play")
    st.write("""
- Move 🧛‍♂️ to find 💎.
- Only nearby tiles are revealed (`fog` ❔).
- 📀 = +10 score  
- ❤️ = +1 life  
- 💣 = -1 life  
- You must reach treasure before moves finish.
""")


# ======================================================
# GRID RENDERING
# ======================================================
st.title("🧛 Treasure Hunt")
size = st.session_state.grid_size
pr, pc = st.session_state.player

st.markdown('<div class="game-grid">', unsafe_allow_html=True)

for r in range(size):
    cols = st.columns(size, gap="small")
    for c, col in enumerate(cols):

        visible = abs(pr - r) <= 1 and abs(pc - c) <= 1
        content = "❔"  # fog default

        if visible:
            if [r, c] == [pr, pc]:      content = "🧛‍♂️"
            elif [r, c] == st.session_state.treasure: content = "💎"
            elif [r, c] in st.session_state.coins:    content = "📀"
            elif [r, c] in st.session_state.hearts:   content = "❤️"
            elif [r, c] in st.session_state.bombs:    content = "💣"
            else:                                     content = ""

        col.markdown(f"<div class='tile'>{content}</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
