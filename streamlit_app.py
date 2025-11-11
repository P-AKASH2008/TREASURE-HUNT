# streamlit_app.py
import streamlit as st
import random
import time
import base64

# ---------------- Page config ----------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")
st.set_option("client.showErrorDetails", True)

# ---------------- Initialize Session State ----------------
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
        "sound_enabled": False,        # NEW 🔊
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_defaults()

# ---------------- Load Sounds ----------------
def play_sound(file):
    """Play sound only when sound toggle is ON."""
    if st.session_state["sound_enabled"]:
        with open(f"sounds/{file}", "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/wav", autoplay=True)

def play_bgm():
    if st.session_state["sound_enabled"]:
        with open("sounds/bgm.wav", "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/wav", autoplay=True)

# ---------------- Helpers ----------------
def manhattan(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])
def all_cells(n): return [[r, c] for r in range(n) for c in range(n)]
def sample_positions(n, exclude, count):
    pool = [p for p in all_cells(n) if p not in exclude]
    if count >= len(pool): return pool.copy()
    return random.sample(pool, count)

# ---------------- Game initialization / reset ----------------
def init_game(difficulty=None):
    if difficulty is None:
        difficulty = st.session_state["difficulty"]

    size_map = {"Easy": 8, "Medium": 10, "Hard": 12}
    size = size_map.get(difficulty, 10)
    st.session_state["grid_size"] = size

    # player start at center
    start = [size // 2, size // 2]
    st.session_state["player"] = start.copy()
    st.session_state["start_pos"] = start.copy()

    # difficulty lives
    lives_map = {"Easy": 3, "Medium": 2, "Hard": 1}
    st.session_state["lives"] = lives_map[difficulty]

    st.session_state["score"] = 0
    st.session_state["moves"] = 0

    cells = all_cells(size)
    cells.remove(start)

    treasure = random.choice(cells)
    st.session_state["treasure"] = treasure
    cells.remove(treasure)

    # Generate items
    coins_count = max(4, size // 2)
    bombs_count = max(3, size // 3)
    hearts_count = max(1, size // 5)

    st.session_state["coins"] = sample_positions(size, [start, treasure], coins_count)
    excluded = [start, treasure] + st.session_state["coins"]
    st.session_state["bombs"] = sample_positions(size, excluded, bombs_count)
    excluded += st.session_state["bombs"]
    st.session_state["hearts"] = sample_positions(size, excluded, hearts_count)

    st.session_state["max_moves"] = manhattan(start, treasure) + 5
    st.session_state["prev_difficulty"] = difficulty
    st.session_state["game_initialized"] = True

# Initialize game
diff = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"],
                            index=["Easy","Medium","Hard"].index(st.session_state["difficulty"]))

if not st.session_state["game_initialized"] or diff != st.session_state["prev_difficulty"]:
    st.session_state["difficulty"] = diff
    init_game(diff)

# ---------------- Fog Visibility ----------------
def is_visible(r, c):
    pr, pc = st.session_state["player"]
    return abs(r - pr) <= 1 and abs(c - pc) <= 1

# ---------------- Player Movement ----------------
def apply_move(direction):
    play_sound("move.wav")  # 🎵 Move SFX

    size = st.session_state["grid_size"]
    r, c = st.session_state["player"]

    if direction == "up" and r > 0: r -= 1
    elif direction == "down" and r < size - 1: r += 1
    elif direction == "left" and c > 0: c -= 1
    elif direction == "right" and c < size - 1: c += 1
    else: return

    st.session_state["player"] = [r, c]
    st.session_state["moves"] += 1

    # coin
    if [r, c] in st.session_state["coins"]:
        st.session_state["score"] += 10
        st.session_state["coins"].remove([r, c])
        play_sound("coin.wav")

    # heart
    if [r, c] in st.session_state["hearts"]:
        st.session_state["lives"] += 1
        st.session_state["hearts"].remove([r, c])
        play_sound("heart.wav")

    # bomb
    if [r, c] in st.session_state["bombs"]:
        st.session_state["lives"] -= 1
        st.session_state["bombs"].remove([r, c])
        play_sound("bomb.wav")

        if st.session_state["lives"] <= 0:
            time.sleep(0.6)
            init_game(st.session_state["difficulty"])
            return

    # treasure
    if [r, c] == st.session_state["treasure"]:
        st.session_state["score"] += 20
        play_sound("treasure.wav")
        time.sleep(0.6)
        init_game(st.session_state["difficulty"])
        return

# ---------------- Sidebar (Score + Controls) ----------------
with st.sidebar:
    st.header("⚙️ Game Panel")
    st.markdown(f"🏆 **Score:** {st.session_state['score']}")
    st.markdown(f"❤️ **Lives:** {st.session_state['lives']}")
    st.markdown(f"🚶 **Moves:** {st.session_state['moves']} / {st.session_state['max_moves']}")

    # 🔊 Toggle sound
    st.session_state["sound_enabled"] = st.checkbox("🔊 Sound ON/OFF", value=False)

    st.markdown("---")
    st.subheader("Controls")
    c1, c2 = st.columns(2)
    with c1: st.button("⬆️", key="up", on_click=apply_move, args=("up",))
    with c2: st.button("➡️", key="right", on_click=apply_move, args=("right",))
    c3, c4 = st.columns(2)
    with c3: st.button("⬇️", key="down", on_click=apply_move, args=("down",))
    with c4: st.button("⬅️", key="left", on_click=apply_move, args=("left",))

    st.markdown("---")
    if st.button("🔄 Restart"):
        init_game(st.session_state["difficulty"])

# ---------------- Main UI (Grid Render) ----------------
st.title("🧛‍♂️ Treasure Hunt — Vampire Heist")

play_bgm()

size = st.session_state["grid_size"]
pr, pc = st.session_state["player"]

for r in range(size):
    cols = st.columns(size, gap="small")
    for c, col in enumerate(cols):

        if is_visible(r, c):
            if [r, c] == [pr, pc]:
                col.markdown("<div style='text-align:center;font-size:28px'>🧛‍♂️</div>", unsafe_allow_html=True)
            elif [r, c] == st.session_state["treasure"]:
                col.markdown("<div style='text-align:center;font-size:26px'>💎</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["coins"]:
                col.markdown("<div style='text-align:center;font-size:26px'>📀</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["hearts"]:
                col.markdown("<div style='text-align:center;font-size:26px'>❤️</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["bombs"]:
                col.markdown("<div style='text-align:center;font-size:26px'>💣</div>", unsafe_allow_html=True)
            else:
                col.markdown(
                    "<div style='text-align:center;background:#0b1220;border-radius:6px;padding:8px;color:#0b1220;'>⬛</div>",
                    unsafe_allow_html=True
                )
        else:
            col.markdown("<div style='text-align:center;font-size:22px'>❔</div>", unsafe_allow_html=True)
