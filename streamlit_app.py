# streamlit_app.py
import streamlit as st
import random
import time

# ---------------- Page config ----------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")
st.set_option("client.showErrorDetails", True)

# ---------------- Styling ----------------
st.markdown(
    """
    <style>
    /* make control buttons consistent and visible */
    .ctrl-btn > button {
        width: 80px !important;
        height: 60px !important;
        font-size: 26px !important;
        border-radius: 12px !important;
        background: #0ea5a4 !important;
        color: #02111a !important;
    }
    /* small secondary layout for bottom controls */
    .ctrl-row { display:flex; justify-content:center; gap:28px; margin-top:8px; margin-bottom:6px; }
    .status { text-align:center; font-size:16px; margin-top:6px; }

    /* grid cell dark tile to match BG */
    .tile {
        width: 44px;
        height: 44px;
        display:flex;
        align-items:center;
        justify-content:center;
        border-radius:8px;
        background: #0b1220; /* dark tile */
        color: #e6edf3;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03);
        font-size:22px;
    }
    .fog {
        width: 44px;
        height: 44px;
        display:flex;
        align-items:center;
        justify-content:center;
        border-radius:8px;
        background: transparent;
        color: #e97171;
        font-size:20px;
    }
    .player {
        width: 44px;
        height: 44px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:26px;
    }

    @media (max-width:700px) {
      .tile { width:10vw; height:10vw; font-size:6vw; border-radius:6vw; }
      .fog { width:10vw; height:10vw; font-size:6vw; border-radius:6vw; }
      .player { width:10vw; height:10vw; font-size:7vw; }
      .ctrl-btn > button { width:18vw !important; height:14vw !important; font-size:7vw !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- Safe init ----------------
def ensure_state():
    defaults = {
        "difficulty": "Medium",
        "game_initialized": False,
        "size": None,
        "player": None,
        "score": 0,
        "lives": 3,
        "treasure": None,
        "coins": [],
        "bombs": [],
        "hearts": [],
        "moves_made": 0,
        "moves_allowed": None,
        "start_pos": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

ensure_state()

# ---------------- Helpers ----------------
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def all_cells(size):
    return [[r, c] for r in range(size) for c in range(size)]

# ---------------- Game reset/init ----------------
def init_game(difficulty=None):
    if difficulty is None:
        difficulty = st.session_state.difficulty

    size_map = {"Easy": 8, "Medium": 10, "Hard": 12}
    size = size_map.get(difficulty, 10)
    st.session_state.size = size

    # player starts near center (center-ish)
    start = [size // 2, size // 2]
    st.session_state.player = start.copy()
    st.session_state.start_pos = start.copy()

    # reset stats
    st.session_state.score = 0
    st.session_state.lives = 3
    st.session_state.moves_made = 0

    # place treasure first
    cells = all_cells(size)
    cells.remove(start)
    treasure = random.choice(cells)
    st.session_state.treasure = treasure
    cells.remove(treasure)

    # sample counts scaled but not huge
    coins_count = max(4, size // 2)
    bombs_count = max(3, size // 3)
    hearts_count = max(1, size // 5)

    st.session_state.coins = random.sample(cells, min(coins_count, len(cells)))
    # remove chosen
    for p in st.session_state.coins:
        if p in cells: cells.remove(p)

    st.session_state.bombs = random.sample(cells, min(bombs_count, len(cells)))
    for p in st.session_state.bombs:
        if p in cells: cells.remove(p)

    st.session_state.hearts = random.sample(cells, min(hearts_count, len(cells)))

    # moves allowed = manhattan(start, treasure) + 5
    st.session_state.moves_allowed = manhattan(st.session_state.start_pos, st.session_state.treasure) + 5

    st.session_state.game_initialized = True
    st.session_state.difficulty = difficulty

# initialize on first run or on difficulty change
selected = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=["Easy","Medium","Hard"].index(st.session_state.difficulty))
if (not st.session_state.game_initialized) or (selected != st.session_state.difficulty):
    init_game(selected)

# ---------------- Visibility (fog 3x3) ----------------
def is_visible(r, c):
    pr, pc = st.session_state.player
    return abs(r - pr) <= 1 and abs(c - pc) <= 1

# ---------------- Movement logic ----------------
def apply_move(direction):
    size = st.session_state.size
    r, c = st.session_state.player

    if direction == "up" and r > 0:
        r -= 1
    elif direction == "down" and r < size - 1:
        r += 1
    elif direction == "left" and c > 0:
        c -= 1
    elif direction == "right" and c < size - 1:
        c += 1
    else:
        return  # invalid/out-of-bounds -> no change

    st.session_state.player = [r, c]
    st.session_state.moves_made += 1

    # interactions
    if [r, c] in st.session_state.coins:
        st.session_state.score += 10
        st.session_state.coins.remove([r, c])
        st.info("📀 +10")

    if [r, c] in st.session_state.hearts:
        st.session_state.lives += 1
        st.session_state.hearts.remove([r, c])
        st.success("❤️ +1 life")

    if [r, c] in st.session_state.bombs:
        st.session_state.lives -= 1
        st.session_state.bombs.remove([r, c])
        st.warning("💣 -1 life")
        if st.session_state.lives <= 0:
            st.error("💥 Game Over — out of lives.")
            time.sleep(0.8)
            init_game(st.session_state.difficulty)
            return

    if [r, c] == st.session_state.treasure:
        st.success("💎 You found the treasure!")
        st.session_state.score += 20
        time.sleep(0.8)
        init_game(st.session_state.difficulty)
        return

    # check move limit
    if st.session_state.moves_made > st.session_state.moves_allowed:
        st.error("⌛ Out of moves! You failed to reach the treasure in time.")
        time.sleep(0.8)
        init_game(st.session_state.difficulty)
        return

# ---------------- Top bar: stats ----------------
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🧛‍♂️ Treasure Hunt — Vampire Heist")
with col2:
    st.markdown(f"**Score:** {st.session_state.score}  ")
    st.markdown(f"**Lives:** {st.session_state.lives}  ")
    st.markdown(f"**Moves:** {st.session_state.moves_made}/{st.session_state.moves_allowed}")

# ---------------- Grid rendering ----------------
size = st.session_state.size
pr, pc = st.session_state.player

for r in range(size):
    cols = st.columns(size, gap="small")
    for c, col in enumerate(cols):
        if is_visible(r, c):
            # visible tile
            if [r, c] == [pr, pc]:
                col.markdown("<div class='player'>🧛‍♂️</div>", unsafe_allow_html=True)
            elif [r, c] == st.session_state.treasure:
                col.markdown("<div class='tile'>💎</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state.coins:
                col.markdown("<div class='tile'>📀</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state.hearts:
                col.markdown("<div class='tile'>❤️</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state.bombs:
                col.markdown("<div class='tile'>💣</div>", unsafe_allow_html=True)
            else:
                # dark tile matching BG
                col.markdown("<div class='tile'></div>", unsafe_allow_html=True)
        else:
            # fog
            col.markdown("<div class='fog'>❓</div>", unsafe_allow_html=True)

# ---------------- Controls layout (PURE Python) ----------------
st.markdown("<br>", unsafe_allow_html=True)

# Layout A but modified so Left is under Right as requested:
# top row -> Up (left column) | Right (right column)
# bottom row -> Down (left column) | Left (right column)  -> this places Left under Right
top_left, top_right = st.columns([1, 1])
with top_left:
    if st.button("⬆️", key="btn_up"):
        apply_move("up")
with top_right:
    if st.button("➡️", key="btn_right"):
        apply_move("right")

bottom_left, bottom_right = st.columns([1, 1])
with bottom_left:
    if st.button("⬇️", key="btn_down"):
        apply_move("down")
with bottom_right:
    if st.button("⬅️", key="btn_left"):
        apply_move("left")

# controls info & restart
st.markdown("<div class='status'>", unsafe_allow_html=True)
st.markdown(f"Moves allowed: **{st.session_state.moves_allowed}** — Moves made: **{st.session_state.moves_made}**")
if st.button("🔄 Restart", key="btn_restart"):
    init_game(st.session_state.difficulty)
st.markdown("</div>", unsafe_allow_html=True)
