# streamlit_app.py
import streamlit as st
import random
import time

# ---------------- Page config ----------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")
st.set_option("client.showErrorDetails", True)

# ---------------- Safe initialization of session state (must run before UI) ----------------
def init_session_defaults():
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

init_session_defaults()

# ---------------- Helpers ----------------
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def all_cells(n):
    return [[r, c] for r in range(n) for c in range(n)]

def sample_positions(n, exclude, count):
    pool = [p for p in all_cells(n) if p not in exclude]
    if count >= len(pool):
        return pool.copy()
    return random.sample(pool, count)

# ---------------- Game initialization / reset ----------------
def init_game(difficulty=None):
    """Initialize or reset the game according to difficulty."""
    if difficulty is None:
        difficulty = st.session_state["difficulty"]

    size_map = {"Easy": 8, "Medium": 10, "Hard": 12}
    size = size_map.get(difficulty, 10)
    st.session_state["grid_size"] = size

    # Player start near center
    start = [size // 2, size // 2]
    st.session_state["player"] = start.copy()
    st.session_state["start_pos"] = start.copy()

    # reset stats
    st.session_state["score"] = 0
    st.session_state["lives"] = 3
    st.session_state["moves"] = 0

    # place treasure
    cells = all_cells(size)
    if start in cells:
        cells.remove(start)
    treasure = random.choice(cells)
    st.session_state["treasure"] = treasure
    cells.remove(treasure)

    # item counts scaled with size (denser but not overwhelming)
    coins_count = max(4, size // 2)
    bombs_count = max(3, size // 3)
    hearts_count = max(1, size // 5)

    st.session_state["coins"] = sample_positions(size, [start, treasure], coins_count)
    # ensure coins excluded when placing bombs/hearts
    excluded = [start, treasure] + st.session_state["coins"]
    st.session_state["bombs"] = sample_positions(size, excluded, bombs_count)
    excluded += st.session_state["bombs"]
    st.session_state["hearts"] = sample_positions(size, excluded, hearts_count)

    # moves allowed = Manhattan(start, treasure) + 5
    st.session_state["max_moves"] = manhattan(start, treasure) + 5

    st.session_state["difficulty"] = difficulty
    st.session_state["prev_difficulty"] = difficulty
    st.session_state["game_initialized"] = True

# Initialize first time or when difficulty changes
selected_diff = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=["Easy","Medium","Hard"].index(st.session_state.get("difficulty", "Medium")))
# If user changed difficulty or game not initialized, init
if (not st.session_state["game_initialized"]) or (selected_diff != st.session_state.get("prev_difficulty")):
    st.session_state["difficulty"] = selected_diff
    init_game(selected_diff)

# ---------------- Visibility (fog) ----------------
def is_visible(r, c):
    pr, pc = st.session_state["player"]
    return abs(r - pr) <= 1 and abs(c - pc) <= 1

# ---------------- Interaction logic (move/callback) ----------------
def apply_move(direction: str):
    """Move player and handle interactions. This function is called by button callbacks."""
    size = st.session_state["grid_size"]
    r, c = st.session_state["player"]

    if direction == "up" and r > 0:
        r -= 1
    elif direction == "down" and r < size - 1:
        r += 1
    elif direction == "left" and c > 0:
        c -= 1
    elif direction == "right" and c < size - 1:
        c += 1
    else:
        # out-of-bounds or no change: do nothing
        return

    st.session_state["player"] = [r, c]
    st.session_state["moves"] += 1

    # coin
    if [r, c] in st.session_state["coins"]:
        st.session_state["score"] += 10
        st.session_state["coins"].remove([r, c])
        st.success("📀 +10 coins")

    # heart
    if [r, c] in st.session_state["hearts"]:
        st.session_state["lives"] += 1
        st.session_state["hearts"].remove([r, c])
        st.success("❤️ +1 life")

    # bomb
    if [r, c] in st.session_state["bombs"]:
        st.session_state["lives"] -= 1
        st.session_state["bombs"].remove([r, c])
        st.warning("💣 -1 life")
        if st.session_state["lives"] <= 0:
            st.error("💥 Game Over — you lost all lives")
            time.sleep(0.8)
            init_game(st.session_state["difficulty"])
            return

    # treasure
    if [r, c] == st.session_state["treasure"]:
        st.success("💎 You found the treasure! +20 points")
        st.session_state["score"] += 20
        time.sleep(0.8)
        init_game(st.session_state["difficulty"])
        return

    # move limit check
    if st.session_state["moves"] > st.session_state["max_moves"]:
        st.error("⌛ Out of moves! You lose one life.")
        st.session_state["lives"] -= 1
        time.sleep(0.7)
        if st.session_state["lives"] <= 0:
            st.error("💀 Game Over — lives exhausted, resetting score.")
            st.session_state["score"] = 0
            st.session_state["lives"] = 3
        init_game(st.session_state["difficulty"])
        return

# ---------------- Sidebar: Stats, Controls, Restart, Instructions ----------------
with st.sidebar:
    st.header("⚙️ Game Panel")

    st.markdown(f"**🏆 Score:** {st.session_state['score']}")
    st.markdown(f"**❤️ Lives:** {st.session_state['lives']}")
    st.markdown(f"**🚶 Moves:** {st.session_state['moves']} / {st.session_state['max_moves']}")

    st.markdown("---")
    st.subheader("Controls")
    # Layout A: top row (Up | Right), bottom row (Down | Left) with Left under Right (as requested)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.button("⬆️ Up", key="btn_up", on_click=apply_move, args=("up",))
    with c2:
        st.button("➡️ Right", key="btn_right", on_click=apply_move, args=("right",))

    c3, c4 = st.columns([1, 1])
    with c3:
        st.button("⬇️ Down", key="btn_down", on_click=apply_move, args=("down",))
    with c4:
        st.button("⬅️ Left", key="btn_left", on_click=apply_move, args=("left",))

    st.markdown("---")
    if st.button("🔄 Restart Game", key="btn_restart"):
        init_game(st.session_state["difficulty"])

    st.markdown("---")
    st.subheader("How to play")
    st.markdown(
        """
- Move the **🧛‍♂️ Vampire** to find the hidden **💎 Treasure**.  
- Only the **3×3 area** around you is visible — everything else is covered by fog (`❔`).  
- Collect **coins** (📀) for +10 score, **hearts** (❤️) to gain a life, avoid **bombs** (💣).  
- You must reach treasure within **allowed moves** (Manhattan distance + 5). Running out of moves costs a life.  
- Restart resets the board but keeps the selected difficulty.
"""
    )

# ---------------- Main UI: Title + Grid ----------------
st.title("🧛‍♂️ Treasure Hunt — Vampire Heist")
size = st.session_state["grid_size"]
pr, pc = st.session_state["player"]

# render grid row by row
for r in range(size):
    cols = st.columns(size, gap="small")
    for c, col in enumerate(cols):
        if is_visible(r, c):
            # visible tile
            if [r, c] == [pr, pc]:
                col.markdown("<div style='text-align:center;font-size:30px'>🧛‍♂️</div>", unsafe_allow_html=True)
            elif [r, c] == st.session_state["treasure"]:
                col.markdown("<div style='text-align:center;font-size:26px'>💎</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["coins"]:
                col.markdown("<div style='text-align:center;font-size:26px'>📀</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["hearts"]:
                col.markdown("<div style='text-align:center;font-size:26px'>❤️</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["bombs"]:
                col.markdown("<div style='text-align:center;font-size:26px'>💣</div>", unsafe_allow_html=True)
            else:
                # dark tile to match background
                col.markdown("<div style='text-align:center;background:#0b1220;border-radius:6px;padding:10px;color:#dbeafe;'>⬜</div>", unsafe_allow_html=True)
        else:
            # fog
            col.markdown("<div style='text-align:center;color:#ffb4b4;font-size:20px'>❔</div>", unsafe_allow_html=True)
