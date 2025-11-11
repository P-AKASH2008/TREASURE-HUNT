# streamlit_app.py
import streamlit as st
import random
import time

# ---------------- Page settings ----------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")
st.set_option("client.showErrorDetails", True)

# ---------------- Session State Init ----------------
def init_state():
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
        "leaderboard": [],
        "awaiting_name": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

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

# ---------------- Game Init ----------------
def init_game(difficulty=None):
    if difficulty is None:
        difficulty = st.session_state["difficulty"]

    size_map = {"Easy": 8, "Medium": 10, "Hard": 12}
    size = size_map.get(difficulty, 10)
    st.session_state["grid_size"] = size

    start = [size // 2, size // 2]
    st.session_state["player"] = start.copy()
    st.session_state["start_pos"] = start.copy()

    st.session_state["score"] = 0
    st.session_state["moves"] = 0

    # ✅ Correct difficulty lives
    if difficulty == "Easy":
        st.session_state["lives"] = 3
    elif difficulty == "Medium":
        st.session_state["lives"] = 2
    else:
        st.session_state["lives"] = 1

    cells = all_cells(size)
    cells.remove(start)

    treasure = random.choice(cells)
    st.session_state["treasure"] = treasure
    cells.remove(treasure)

    # items (dense but balanced)
    coin_count = max(4, size // 2)
    bomb_count = max(3, size // 3)
    heart_count = max(1, size // 5)

    st.session_state["coins"] = sample_positions(size, [start, treasure], coin_count)
    excluded = [start, treasure] + st.session_state["coins"]
    st.session_state["bombs"] = sample_positions(size, excluded, bomb_count)
    excluded += st.session_state["bombs"]
    st.session_state["hearts"] = sample_positions(size, excluded, heart_count)

    st.session_state["max_moves"] = manhattan(start, treasure) + 5

    st.session_state["prev_difficulty"] = difficulty
    st.session_state["difficulty"] = difficulty
    st.session_state["game_initialized"] = True
    st.session_state["awaiting_name"] = False


# ---------------- Movement + Logic ----------------
def apply_move(direction):
    if st.session_state["awaiting_name"]:
        return

    size = st.session_state["grid_size"]
    r, c = st.session_state["player"]

    match direction:
        case "up":
            if r > 0: r -= 1
        case "down":
            if r < size - 1: r += 1
        case "left":
            if c > 0: c -= 1
        case "right":
            if c < size - 1: c += 1

    st.session_state["player"] = [r, c]
    st.session_state["moves"] += 1

    # coin collected
    if [r, c] in st.session_state["coins"]:
        st.session_state["score"] += 10
        st.session_state["coins"].remove([r, c])
        st.success("📀 +10 score")

    # extra life
    if [r, c] in st.session_state["hearts"]:
        st.session_state["lives"] += 1
        st.session_state["hearts"].remove([r, c])
        st.success("❤️ +1 life")

    # bomb hit
    if [r, c] in st.session_state["bombs"]:
        st.session_state["lives"] -= 1
        st.session_state["bombs"].remove([r, c])
        st.warning("💣 -1 life")

    # treasure found
    if [r, c] == st.session_state["treasure"]:
        st.session_state["score"] += 20
        st.success("💎 Treasure Found! +20 score")
        st.session_state["awaiting_name"] = True
        return

    # Out of moves check
    if st.session_state["moves"] > st.session_state["max_moves"]:
        st.error("⌛ Out of moves!")
        st.session_state["lives"] -= 1

    if st.session_state["lives"] <= 0:
        st.error("💀 Game Over!")
        st.session_state["awaiting_name"] = True


# ---------------- Sidebar ----------------
selected = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Medium", "Hard"],
    index=["Easy","Medium","Hard"].index(st.session_state["difficulty"])
)

if (selected != st.session_state["prev_difficulty"]) or (not st.session_state["game_initialized"]):
    init_game(selected)

st.sidebar.header("⚙️ Game Panel")
st.sidebar.markdown(f"**🏆 Score:** {st.session_state['score']}")
st.sidebar.markdown(f"**❤️ Lives:** {st.session_state['lives']}")
st.sidebar.markdown(f"**🚶 Moves:** {st.session_state['moves']} / {st.session_state['max_moves']}")

# ⬆⬇⬅➡ controls
st.sidebar.subheader("Controls")
c1, c2 = st.sidebar.columns(2)
c1.button("⬆️ Up", on_click=apply_move, args=("up",))
c2.button("➡️ Right", on_click=apply_move, args=("right",))
c3, c4 = st.sidebar.columns(2)
c3.button("⬇️ Down", on_click=apply_move, args=("down",))
c4.button("⬅️ Left", on_click=apply_move, args=("left",))

# Restart
if st.sidebar.button("🔄 Restart Game"):
    init_game(st.session_state["difficulty"])

# Leaderboard toggle
if st.sidebar.checkbox("🏆 View Leaderboard"):
    st.sidebar.markdown("### Top 10 Scores")
    if len(st.session_state["leaderboard"]) == 0:
        st.sidebar.write("No scores yet.")
    else:
        for i, entry in enumerate(st.session_state["leaderboard"], 1):
            st.sidebar.write(f"**{i}. {entry['name']}** — {entry['score']} pts  _({entry['time']})_")

# Instructions
st.sidebar.subheader("How to play")
st.sidebar.markdown(
"""
🧛‍♂️ Move in fog(?) covered map

🤺 Each set of moves costs 1 life

📀 +10 score  
❤️ +1 life  
💣 -1 life  
💎 Win if you reach the treasure

🚩 Save and Restart after game 
    ends
"""
)


# ---------------- GRID DISPLAY ----------------
def visible(r, c):
    pr, pc = st.session_state["player"]
    return abs(r - pr) <= 1 and abs(c - pc) <= 1

st.title("🧛‍♂️ Treasure Hunt — Vampire Heist")

size = st.session_state["grid_size"]
pr, pc = st.session_state["player"]

for r in range(size):
    cols = st.columns(size, gap="small")
    for c, col in enumerate(cols):
        if visible(r, c):
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
                col.markdown("<div style='text-align:center;background:#0b1220;border-radius:6px;padding:10px;'> </div>", unsafe_allow_html=True)
        else:
            col.markdown("<div style='text-align:center;color:#ffb4b4;font-size:20px'>❔</div>", unsafe_allow_html=True)


# ---------------- SAVE SCORE SCREEN ----------------
if st.session_state["awaiting_name"]:
    with st.sidebar.form("save_score_form"):
        st.sidebar.markdown("### 💀 Game Over — Save Score")
        name = st.text_input("Your Name:")
        submit = st.form_submit_button("Save Score")

    if submit and name.strip() != "":
        st.session_state["leaderboard"].append({
            "name": name,
            "score": st.session_state["score"],
            "time": time.strftime("%d-%m-%Y %H:%M:%S")
        })

        st.session_state["leaderboard"] = sorted(
            st.session_state["leaderboard"],
            key=lambda x: x["score"],
            reverse=True
        )[:10]

        init_game(st.session_state["difficulty"])
