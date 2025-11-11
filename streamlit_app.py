# streamlit_app.py
import streamlit as st
import random
import time
import json
from datetime import datetime
from pathlib import Path

# ---------------- Page config ----------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")
st.set_option("client.showErrorDetails", True)

# ---------------- Leaderboard file ----------------
LEADERBOARD_PATH = Path("leaderboard.json")

def load_leaderboard():
    if not LEADERBOARD_PATH.exists():
        return []
    try:
        with LEADERBOARD_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []

def save_leaderboard(records):
    # keep top 10 sorted descending by score
    records_sorted = sorted(records, key=lambda x: x.get("score", 0), reverse=True)[:10]
    with LEADERBOARD_PATH.open("w", encoding="utf-8") as f:
        json.dump(records_sorted, f, indent=2, ensure_ascii=False)

# ---------------- Tile CSS (compact centered squares) ----------------
st.markdown("""
<style>
.game-grid {
    max-width: 520px;
    margin-left: auto;
    margin-right: auto;
}
.tile {
    aspect-ratio: 1 / 1;
    width: 100%;
    background-color: #0b1220;
    border-radius: 6px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 26px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Safe session defaults ----------------
def init_session_defaults():
    defaults = {
        "initialized": False,
        "difficulty": "Medium",
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
        "max_moves": 0,
        "show_leaderboard": False,
        "pending_gameover": None,  # will be dict when game ends: {"reason": "win"/"lose", "score": n, "difficulty": d}
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

# ---------------- Game init/reset ----------------
def init_game(difficulty=None):
    """Initialize a brand new game (resets score, lives, moves, items)."""
    if difficulty is None:
        difficulty = st.session_state["difficulty"]

    size_map = {"Easy": 8, "Medium": 10, "Hard": 12}
    size = size_map.get(difficulty, 10)
    st.session_state["grid_size"] = size

    # Lives mapping per difficulty
    lives_map = {"Easy": 3, "Medium": 2, "Hard": 1}
    st.session_state["lives"] = lives_map.get(difficulty, 2)

    # Reset stats fully
    st.session_state["score"] = 0
    st.session_state["moves"] = 0

    # Start position (center-ish)
    start = [size // 2, size // 2]
    st.session_state["player"] = start.copy()
    st.session_state["start_pos"] = start.copy()

    # Place treasure not on start
    cells = all_cells(size)
    if start in cells:
        cells.remove(start)
    treasure = random.choice(cells)
    st.session_state["treasure"] = treasure
    cells.remove(treasure)

    # Item counts (denser, compact)
    coins_count = max(6, size // 2)
    bombs_count = max(4, size // 3)
    hearts_count = max(1, size // 6)

    st.session_state["coins"] = sample_positions(size, [start, treasure], coins_count)
    excluded = [start, treasure] + st.session_state["coins"]
    st.session_state["bombs"] = sample_positions(size, excluded, bombs_count)
    excluded += st.session_state["bombs"]
    st.session_state["hearts"] = sample_positions(size, excluded, hearts_count)

    st.session_state["max_moves"] = manhattan(start, treasure) + 5

    st.session_state["difficulty"] = difficulty
    st.session_state["initialized"] = True
    st.session_state["pending_gameover"] = None  # clear any pending

# Initialize first time or when difficulty changed
# Use selectbox and when selection differs, init_game is called
sidebar_diff = st.sidebar.selectbox(
    "Difficulty", ["Easy", "Medium", "Hard"],
    index=["Easy", "Medium", "Hard"].index(st.session_state.get("difficulty", "Medium"))
)
if sidebar_diff != st.session_state.get("difficulty") or not st.session_state["initialized"]:
    init_game(sidebar_diff)

# ---------------- Fog visibility ----------------
def is_visible(r, c):
    pr, pc = st.session_state["player"]
    return abs(r - pr) <= 1 and abs(c - pc) <= 1

# ---------------- Leaderboard functions ----------------
def record_score_and_prompt(score, cause, difficulty):
    """Prepare a pending gameover to trigger modal for name input on next render."""
    st.session_state["pending_gameover"] = {"score": score, "cause": cause, "difficulty": difficulty}

def save_record(name, score, difficulty):
    recs = load_leaderboard()
    recs.append({
        "name": name.strip() or "Anonymous",
        "score": int(score),
        "difficulty": difficulty,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    # keep top 10
    recs_sorted = sorted(recs, key=lambda x: x["score"], reverse=True)[:10]
    save_leaderboard(recs_sorted)

# ---------------- Interaction / movement ----------------
def apply_move(direction: str):
    size = st.session_state["grid_size"]
    r, c = st.session_state["player"]

    new_r, new_c = r, c
    if direction == "up" and r > 0:
        new_r -= 1
    elif direction == "down" and r < size - 1:
        new_r += 1
    elif direction == "left" and c > 0:
        new_c -= 1
    elif direction == "right" and c < size - 1:
        new_c += 1
    else:
        return  # out of bounds or no movement

    st.session_state["player"] = [new_r, new_c]
    st.session_state["moves"] += 1

    # coin
    if [new_r, new_c] in st.session_state["coins"]:
        st.session_state["score"] += 10
        st.session_state["coins"].remove([new_r, new_c])
        st.success("📀 +10 coins")

    # heart
    if [new_r, new_c] in st.session_state["hearts"]:
        st.session_state["lives"] += 1
        st.session_state["hearts"].remove([new_r, new_c])
        st.success("❤️ +1 life")

    # bomb
    if [new_r, new_c] in st.session_state["bombs"]:
        st.session_state["lives"] -= 1
        st.session_state["bombs"].remove([new_r, new_c])
        st.warning("💣 -1 life")
        # if lives exhausted -> game over
        if st.session_state["lives"] <= 0:
            record_score_and_prompt(st.session_state["score"], "lives_exhausted", st.session_state["difficulty"])
            return

    # treasure
    if [new_r, new_c] == st.session_state["treasure"]:
        st.session_state["score"] += 20
        st.success("💎 Found the treasure! +20")
        record_score_and_prompt(st.session_state["score"], "treasure", st.session_state["difficulty"])
        return

    # move limit check
    if st.session_state["moves"] > st.session_state["max_moves"]:
        st.session_state["lives"] -= 1
        st.warning("⌛ Out of moves! -1 life")
        if st.session_state["lives"] <= 0:
            record_score_and_prompt(st.session_state["score"], "moves_exhausted", st.session_state["difficulty"])
            return
        else:
            # not total gameover — re-init a new round on same difficulty
            init_game(st.session_state["difficulty"])
            return

# ---------------- Sidebar (stats, controls, leaderboard toggle) ----------------
with st.sidebar:
    st.header("⚙️ Game Panel")

    st.markdown(f"**🏆 Score:** {st.session_state['score']}")
    st.markdown(f"**❤️ Lives:** {st.session_state['lives']}")
    st.markdown(f"**🚶 Moves:** {st.session_state['moves']} / {st.session_state['max_moves']}")

    st.markdown("---")
    st.subheader("Controls")
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
    # Restart that fully restarts fresh game
    if st.button("🔄 Restart Game", key="btn_restart"):
        init_game(st.session_state["difficulty"])

    st.markdown("---")
    show_lb = st.checkbox("Show Leaderboard", value=st.session_state.get("show_leaderboard", False))
    st.session_state["show_leaderboard"] = show_lb

    st.markdown("---")
    st.subheader("How to play")
    st.markdown(
        """
- Move the **🧛‍♂️ Vampire** to find the **💎 Treasure**.  
- Only the **3×3 area** around you is visible (fog `❔`).  
- Collect **coins** (📀) for +10 score, **hearts** (❤️) to gain a life, avoid **bombs** (💣).  
- You must reach treasure within **allowed moves** (Manhattan distance + 5). Running out of moves costs a life.  
- When the game ends you can save your name to the leaderboard (top 10).
"""
    )

    # Show leaderboard if toggled
    if st.session_state.get("show_leaderboard"):
        st.markdown("---")
        st.subheader("🏆 Leaderboard (Top 10)")
        records = load_leaderboard()
        if not records:
            st.write("No records yet — play and save your score!")
        else:
            # show table
            import pandas as pd
            df = pd.DataFrame(records)
            # reorder columns if present
            cols = ["name", "score", "difficulty", "datetime"]
            cols = [c for c in cols if c in df.columns]
            st.table(df[cols])

# ---------------- Main UI: title + grid ----------------
st.title("🧛‍♂️ Treasure Hunt — Vampire Heist")

size = st.session_state["grid_size"]
pr, pc = st.session_state["player"]

st.markdown('<div class="game-grid">', unsafe_allow_html=True)
for r in range(size):
    cols = st.columns(size, gap="small")
    for c, col in enumerate(cols):
        if is_visible(r, c):
            # visible tile content
            if [r, c] == [pr, pc]:
                col.markdown("<div class='tile'>🧛‍♂️</div>", unsafe_allow_html=True)
            elif [r, c] == st.session_state["treasure"]:
                col.markdown("<div class='tile'>💎</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["coins"]:
                col.markdown("<div class='tile'>📀</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["hearts"]:
                col.markdown("<div class='tile'>❤️</div>", unsafe_allow_html=True)
            elif [r, c] in st.session_state["bombs"]:
                col.markdown("<div class='tile'>💣</div>", unsafe_allow_html=True)
            else:
                # empty visible tile — background-matching tile
                col.markdown("<div class='tile'></div>", unsafe_allow_html=True)
        else:
            # fog
            col.markdown("<div class='tile'>❔</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Pending gameover modal handling ----------------
# If a gameover is pending (set in apply_move), show modal to save name / show result
pending = st.session_state.get("pending_gameover")
if pending:
    # Show a modal dialog asking for name and giving save option
    with st.modal("Game Over — Save your score"):
        reason = pending.get("cause", "end")
        score_val = pending.get("score", 0)
        difficulty_val = pending.get("difficulty", st.session_state.get("difficulty", "Medium"))

        if reason == "treasure":
            st.success(f"You found the treasure! Score: {score_val}")
        else:
            st.error(f"Game ended ({reason}). Score: {score_val}")

        name_input = st.text_input("Enter your name to save your score:", value="")
        col_ok, col_skip = st.columns([1,1])
        with col_ok:
            if st.button("Save and Continue"):
                save_record(name_input or "Anonymous", score_val, difficulty_val)
                # clear pending and restart fresh game
                st.session_state["pending_gameover"] = None
                init_game(st.session_state["difficulty"])
                st.experimental_rerun()
        with col_skip:
            if st.button("Skip"):
                st.session_state["pending_gameover"] = None
                init_game(st.session_state["difficulty"])
                st.experimental_rerun()

# ---------------- End of file ----------------
