import streamlit as st
import random
import time

# --------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")
st.set_option("client.showErrorDetails", True)

# --------------------------------------------------------
# CSS (perfect square tile + smaller size)
# --------------------------------------------------------
st.markdown("""
<style>
.square-tile {
    aspect-ratio: 1 / 1;
    width: 100%;
    background-color: #0b1220;
    border-radius: 6px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 22px;    /* ✅ smaller tiles */
    padding: 3px;       /* ✅ reduces tile height */
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------
# SESSION INITIALIZATION
# --------------------------------------------------------
def init_defaults():
    defaults = {
        "difficulty": "Medium",
        "prev_difficulty": None,
        "game_initialized": False,
        "grid_size": None,
        "player": None,
        "start_pos": None,
        "treasure": None,
        "coins": [],
        "bombs": [],
        "hearts": [],
        "score": 0,
        "lives": 3,
        "moves": 0,
        "max_moves": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_defaults()


# --------------------------------------------------------
# HELPERS
# --------------------------------------------------------
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def all_cells(n):
    return [[r, c] for r in range(n) for c in range(n)]

def sample_positions(n, exclude, count):
    pool = [p for p in all_cells(n) if p not in exclude]
    return random.sample(pool, min(count, len(pool)))


# --------------------------------------------------------
# NEW GAME / RESTART
# --------------------------------------------------------
def init_game(new_diff=None):
    difficulty = new_diff or st.session_state["difficulty"]

    size_map = {"Easy": 8, "Medium": 10, "Hard": 12}
    size = size_map[difficulty]
    st.session_state["grid_size"] = size

    st.session_state["score"] = 0
    st.session_state["lives"] = 3
    st.session_state["moves"] = 0

    start = [size // 2, size // 2]
    st.session_state["player"] = start.copy()
    st.session_state["start_pos"] = start.copy()

    treasure = random.choice(all_cells(size))
    while treasure == start:
        treasure = random.choice(all_cells(size))
    st.session_state["treasure"] = treasure

    excluded = [start, treasure]

    st.session_state["coins"] = sample_positions(size, excluded, max(4, size // 2))
    excluded += st.session_state["coins"]

    st.session_state["bombs"] = sample_positions(size, excluded, max(3, size // 3))
    excluded += st.session_state["bombs"]

    st.session_state["hearts"] = sample_positions(size, excluded, max(1, size // 5))

    st.session_state["max_moves"] = manhattan(start, treasure) + 5

    st.session_state["difficulty"] = difficulty
    st.session_state["prev_difficulty"] = difficulty
    st.session_state["game_initialized"] = True


# Initialize only once or when difficulty changes
diff = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
if not st.session_state["game_initialized"] or diff != st.session_state["prev_difficulty"]:
    init_game(diff)


# --------------------------------------------------------
# FOG LOGIC
# --------------------------------------------------------
def visible(r, c):
    pr, pc = st.session_state["player"]
    return abs(r - pr) <= 1 and abs(c - pc) <= 1


# --------------------------------------------------------
# MOVEMENT / ITEM PICKUP
# --------------------------------------------------------
def apply_move(direction):
    size = st.session_state["grid_size"]
    r, c = st.session_state["player"]

    match direction:
        case "up":    r -= 1 if r > 0 else 0
        case "down":  r += 1 if r < size - 1 else 0
        case "left":  c -= 1 if c > 0 else 0
        case "right": c += 1 if c < size - 1 else 0

    st.session_state["player"] = [r, c]
    st.session_state["moves"] += 1

    # coin
    if [r, c] in st.session_state["coins"]:
        st.session_state["coins"].remove([r, c])
        st.session_state["score"] += 10
        st.success("📀 +10 coins")

    # heart
    if [r, c] in st.session_state["hearts"]:
        st.session_state["hearts"].remove([r, c])
        st.session_state["lives"] += 1
        st.success("❤️ +1 life")

    # bomb
    if [r, c] in st.session_state["bombs"]:
        st.session_state["bombs"].remove([r, c])
        st.session_state["lives"] -= 1
        st.warning("💣 Boom -1 life")

    # treasure
    if [r, c] == st.session_state["treasure"]:
        st.session_state["score"] += 20
        st.success("💎 Treasure found +20")
        time.sleep(0.6)
        init_game(st.session_state["difficulty"])
        return

    # out of moves
    if st.session_state["moves"] > st.session_state["max_moves"]:
        st.session_state["lives"] -= 1
        st.warning("⌛ Out of moves! -1 life")
        time.sleep(0.6)
        init_game(st.session_state["difficulty"])
        return

    # game over
    if st.session_state["lives"] <= 0:
        st.error("💀 GAME OVER")
        time.sleep(0.6)
        init_game(st.session_state["difficulty"])


# --------------------------------------------------------
# SIDEBAR UI (same as before + instructions added)
# --------------------------------------------------------
with st.sidebar:
    st.header("🎮 Game Panel")

    st.write(f"🏆 **Score:** {st.session_state['score']}")
    st.write(f"❤️ **Lives:** {st.session_state['lives']}")
    st.write(f"🚶 **Moves:** {st.session_state['moves']} / {st.session_state['max_moves']}")

    st.markdown("---")
    st.subheader("Controls")

    c1, c2 = st.columns(2)
    with c1:
        st.button("⬆️", on_click=apply_move, args=("up",))
    with c2:
        st.button("➡️", on_click=apply_move, args=("right",))

    c3, c4 = st.columns(2)
    with c3:
        st.button("⬇️", on_click=apply_move, args=("down",))
    with c4:
        st.button("⬅️", on_click=apply_move, args=("left",))

    st.markdown("---")
    st.subheader("Instructions")
    st.caption("🧛 Move to reveal tiles")
    st.caption("📀 = +10 score")
    st.caption("❤️ = +1 life")
    st.caption("💣 = -1 life")
    st.caption("💎 = Level Complete")

    if st.button("🔄 Restart Game"):
        init_game(st.session_state["difficulty"])


# --------------------------------------------------------
# GRID DRAWING (unchanged, only smaller tiles)
# --------------------------------------------------------
st.title("🧛 Treasure Hunt — Vampire Heist")

size = st.session_state["grid_size"]
pr, pc = st.session_state["player"]

for r in range(size):
    cols = st.columns(size, gap="small")
    for c, col in enumerate(cols):

        if visible(r, c):
            if [r, c] == [pr, pc]:
                col.markdown("<div class='square-tile'>🧛‍♂️</div>", unsafe_allow_html=True)
            elif [r, c] == st.session_state["treasure"]:
                col.markdown("<div class='square-tile'>💎</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["coins"]:
                col.markdown("<div class='square-tile'>📀</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["hearts"]:
                col.markdown("<div class='square-tile'>❤️</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["bombs"]:
                col.markdown("<div class='square-tile'>💣</div>", unsafe_allow_html=True)
            else:
                col.markdown("<div class='square-tile'></div>", unsafe_allow_html=True)
        else:
            col.markdown("<div class='square-tile'>❔</div>", unsafe_allow_html=True)
