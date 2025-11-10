# streamlit_app.py
import streamlit as st
import random
import time

# ---------------- Page config ----------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")
st.set_option("client.showErrorDetails", True)

# ---------------- CSS (buttons + ninja size) ----------------
st.markdown(
    """
<style>
/* Make sidebar buttons consistent */
button[kind="secondary"] {
    border-radius: 12px !important;
    height: 48px !important;
    width: 92px !important;
    font-size: 22px !important;
}

/* Ninja / grid cell styling */
.ninja { font-size: 38px !important; text-align:center; }
.gridcell { font-size: 32px; text-align:center; padding:6px; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Helper: safe session defaults ----------------
def ensure_defaults():
    # difficulty default
    if "difficulty" not in st.session_state:
        st.session_state.difficulty = "Medium"

    # flag to indicate initial setup performed
    if "initialized" not in st.session_state or not st.session_state.initialized:
        st.session_state.initialized = True
        init_game()  # will set size, player, items, score, lives, etc.

# ---------------- Game init and helpers ----------------
def init_game():
    """Initialize or reset the game according to chosen difficulty."""
    size_map = {"Easy": 8, "Medium": 10, "Hard": 12}
    size = size_map.get(st.session_state.get("difficulty", "Medium"), 10)
    st.session_state.size = size

    # player at center
    st.session_state.player = [size // 2, size // 2]

    # clear / initialize lists and stats
    st.session_state.coins = []
    st.session_state.bombs = []
    st.session_state.hearts = []
    st.session_state.score = 0
    st.session_state.lives = 3

    # place treasure in a random location not equal to player
    while True:
        tr = [random.randint(0, size - 1), random.randint(0, size - 1)]
        if tr != st.session_state.player:
            st.session_state.treasure = tr
            break

    # helper to place random unique items
    def place_random(container, count):
        attempts = 0
        while len(container) < count and attempts < 2000:
            attempts += 1
            pos = [random.randint(0, size - 1), random.randint(0, size - 1)]
            if pos == st.session_state.player:
                continue
            # don't overlap any existing items or treasure
            if pos in st.session_state.coins or pos in st.session_state.bombs or pos in st.session_state.hearts:
                continue
            if pos == st.session_state.treasure:
                continue
            container.append(pos)

    # counts scale with size
    place_random(st.session_state.coins, max(3, size // 2))
    place_random(st.session_state.bombs, max(3, size // 3))
    place_random(st.session_state.hearts, max(1, size // 4))

    # fog: we'll compute visible tiles each render; store no persistent revealed grid
    st.session_state.last_action_time = time.time()

def reveal_mask():
    """Return a function that tests whether (r,c) should be visible (3x3 around player)."""
    pr, pc = st.session_state.player
    def is_visible(r, c):
        return abs(r - pr) <= 1 and abs(c - pc) <= 1
    return is_visible

def evaluate_current_tile():
    """Apply effects for items at the player's position."""
    pos = st.session_state.player

    # coins
    if pos in st.session_state.coins:
        st.session_state.score += 10
        st.session_state.coins.remove(pos)
        st.toast("📀 +10")

    # hearts
    if pos in st.session_state.hearts:
        st.session_state.lives = min(10, st.session_state.lives + 1)
        st.session_state.hearts.remove(pos)
        st.toast("❤️ +1 life")

    # bombs
    if pos in st.session_state.bombs:
        st.session_state.lives -= 1
        st.session_state.bombs.remove(pos)
        st.toast("💣 -1 life")
        if st.session_state.lives <= 0:
            st.error("💥 Game Over - you lost all lives")
            # reset the game after small pause
            time.sleep(0.8)
            init_game()
            return

    # treasure
    if pos == st.session_state.treasure:
        st.success("💎 You found the treasure! +20 points")
        st.session_state.score += 20
        time.sleep(0.8)
        init_game()
        return

# ---------------- Movement ----------------
def move(dr, dc):
    size = st.session_state.size
    r, c = st.session_state.player
    nr, nc = r + dr, c + dc
    if 0 <= nr < size and 0 <= nc < size:
        st.session_state.player = [nr, nc]
        st.session_state.last_action_time = time.time()
        evaluate_current_tile()

# ---------------- Ensure defaults and init ----------------
ensure_defaults()

# ---------------- Sidebar elements ----------------
st.sidebar.title("🎮 Treasure Hunt Controls")

# Difficulty selector — when changed, reset game
prev_diff = st.session_state.difficulty
new_diff = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=["Easy","Medium","Hard"].index(prev_diff))
if new_diff != prev_diff:
    st.session_state.difficulty = new_diff
    init_game()

# Score & lives
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Score:** {st.session_state.get('score',0)}  \n**Lives:** {st.session_state.get('lives',3)}")
st.sidebar.markdown("---")
st.sidebar.write("### Movement")

# Symmetric controls layout in sidebar
ctrl = st.sidebar.container()
up = ctrl.button("⬆️", use_container_width=True)
c1, c_gap, c2 = ctrl.columns([1, 0.2, 1])
left = c1.button("⬅️", use_container_width=True)
right = c2.button("➡️", use_container_width=True)
down = ctrl.button("⬇️", use_container_width=True)

# Execute movement immediately
if up:
    move(-1, 0)
if down:
    move(1, 0)
if left:
    move(0, -1)
if right:
    move(0, 1)

# ---------------- Main UI ----------------
st.title("🗺️ Treasure Hunt")

size = st.session_state.size
is_visible = reveal_mask()

# Render grid using columns (keeps layout stable)
for r in range(size):
    cols = st.columns(size, gap="small")
    for c, col in enumerate(cols):
        if is_visible(r, c):
            # player
            if st.session_state.player == [r, c]:
                # Render ninja as HTML to avoid font fallback issues
                col.markdown("<div class='ninja'>🥷</div>", unsafe_allow_html=True)
            else:
                # items if present
                if [r, c] == st.session_state.treasure:
                    col.markdown("<div class='gridcell'>💎</div>", unsafe_allow_html=True)
                elif [r, c] in st.session_state.coins:
                    col.markdown("<div class='gridcell'>📀</div>", unsafe_allow_html=True)
                elif [r, c] in st.session_state.hearts:
                    col.markdown("<div class='gridcell'>❤️</div>", unsafe_allow_html=True)
                elif [r, c] in st.session_state.bombs:
                    col.markdown("<div class='gridcell'>💣</div>", unsafe_allow_html=True)
                else:
                    col.markdown("<div class='gridcell'>⬜</div>", unsafe_allow_html=True)
        else:
            # covered by fog
            col.markdown("<div class='gridcell'>❓</div>", unsafe_allow_html=True)

# ---------------- End of file ----------------
