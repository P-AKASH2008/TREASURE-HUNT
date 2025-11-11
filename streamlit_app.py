# streamlit_app.py
import streamlit as st
import random
import time

# ---------------- Page config ----------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")
st.set_option("client.showErrorDetails", True)

# ---------------- Safe initialization ----------------
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
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_defaults()

# ---------------- Helper ----------------
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def all_cells(n):
    return [[r, c] for r in range(n) for c in range(n)]

def sample_positions(n, exclude, count):
    pool = [p for p in all_cells(n) if p not in exclude]
    return random.sample(pool, min(count, len(pool)))

# ---------------- RESET / NEW GAME ----------------
def init_game(difficulty=None):
    """Creates a completely *new* game (called by restart OR difficulty change)."""
    if difficulty is None:
        difficulty = st.session_state["difficulty"]

    size_map = {"Easy": 8, "Medium": 10, "Hard": 12}
    size = size_map[difficulty]
    st.session_state["grid_size"] = size

    # FULL RESET
    st.session_state["score"] = 0
    st.session_state["lives"] = 3
    st.session_state["moves"] = 0

    # player start = center-ish
    start = [size // 2, size // 2]
    st.session_state["player"] = start.copy()
    st.session_state["start_pos"] = start.copy()

    # place treasure
    treasure = random.choice(all_cells(size))
    while treasure == start:
        treasure = random.choice(all_cells(size))
    st.session_state["treasure"] = treasure

    # coins / bombs / hearts
    excluded = [start, treasure]
    st.session_state["coins"] = sample_positions(size, excluded, max(4, size // 2))
    excluded += st.session_state["coins"]
    st.session_state["bombs"] = sample_positions(size, excluded, max(3, size // 3))
    excluded += st.session_state["bombs"]
    st.session_state["hearts"] = sample_positions(size, excluded, max(1, size // 5))

    # move limit formula
    st.session_state["max_moves"] = manhattan(start, treasure) + 5

    st.session_state["prev_difficulty"] = difficulty
    st.session_state["difficulty"] = difficulty
    st.session_state["game_initialized"] = True


# init once OR on difficulty change
diff = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
if not st.session_state["game_initialized"] or diff != st.session_state["prev_difficulty"]:
    init_game(diff)


# ---------------- Fog visibility ----------------
def visible(r, c):
    pr, pc = st.session_state["player"]
    return abs(r - pr) <= 1 and abs(c - pc) <= 1


# ---------------- Move logic ----------------
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

    # Coin pickup
    if [r, c] in st.session_state["coins"]:
        st.session_state["coins"].remove([r, c])
        st.session_state["score"] += 10
        st.success("📀 +10 coins")

    # Heart pickup
    if [r, c] in st.session_state["hearts"]:
        st.session_state["hearts"].remove([r, c])
        st.session_state["lives"] += 1
        st.success("❤️ +1 life")

    # Bomb
    if [r, c] in st.session_state["bombs"]:
        st.session_state["bombs"].remove([r, c])
        st.session_state["lives"] -= 1
        st.warning("💣 Boom -1 life")

    # Treasure
    if [r, c] == st.session_state["treasure"]:
        st.session_state["score"] += 20
        st.success("💎 Treasure found! +20")
        time.sleep(0.6)
        init_game(st.session_state["difficulty"])
        return

    # Out of moves
    if st.session_state["moves"] > st.session_state["max_moves"]:
        st.warning("⌛ Out of moves! -1 life")
        st.session_state["lives"] -= 1
        time.sleep(0.6)
        init_game(st.session_state["difficulty"])
        return

    # out of lives
    if st.session_state["lives"] <= 0:
        st.error("💀 GAME OVER — restarting")
        time.sleep(0.6)
        init_game(st.session_state["difficulty"])


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙ Game Panel")

    st.write(f"🏆 **Score:** {st.session_state['score']}")
    st.write(f"❤️ **Lives:** {st.session_state['lives']}")
    st.write(f"🚶 **Moves:** {st.session_state['moves']} / {st.session_state['max_moves']}")

    st.markdown("---")
    st.subheader("Controls")

    c1, c2 = st.columns(2)
    with c1:
        st.button("⬆️ Up", on_click=apply_move, args=("up",))
    with c2:
        st.button("➡️ Right", on_click=apply_move, args=("right",))

    c3, c4 = st.columns(2)
    with c3:
        st.button("⬇️ Down", on_click=apply_move, args=("down",))
    with c4:
        st.button("⬅️ Left", on_click=apply_move, args=("left",))

    st.markdown("---")

    if st.button("🔄 Restart"):
        init_game(st.session_state["difficulty"])

    st.markdown("---")
    st.caption(
        "🧛 Move to find 💎.\n"
        "📀 = +10 | ❤️ = +1 life | 💣 = -1 life\n"
    )


# ---------------- MAIN UI ----------------
st.title("🧛 Treasure Hunt — Vampire Heist")

size = st.session_state["grid_size"]
pr, pc = st.session_state["player"]

for r in range(size):
    row = st.columns(size, gap="small")
    for c, col in enumerate(row):

        # Visible area = emoji
        if visible(r, c):
            if [r, c] == [pr, pc]:
                col.markdown("<div style='text-align:center;font-size:30px'>🧛‍♂️</div>", unsafe_allow_html=True)
            elif [r, c] == st.session_state["treasure"]:
                col.markdown("<div style='text-align:center;font-size:28px'>💎</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["coins"]:
                col.markdown("<div style='text-align:center;font-size:26px'>📀</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["hearts"]:
                col.markdown("<div style='text-align:center;font-size:26px'>❤️</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["bombs"]:
                col.markdown("<div style='text-align:center;font-size:26px'>💣</div>", unsafe_allow_html=True)
            else:
                # ✅ Empty tile now matches background color
                col.markdown(
                    "<div style='background-color:#0b1220;border-radius:6px;padding:14px;'></div>",
                    unsafe_allow_html=True
                )
        else:
            col.markdown("<div style='text-align:center;font-size:20px;color:#b4b4ff'>❔</div>", unsafe_allow_html=True)
