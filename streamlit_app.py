# app.py - Treasure Hunt (final verified)
import streamlit as st
import random
import json
import os
import time

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")

# -----------------------------
# ASSETS - make sure these files exist in sprites/
# -----------------------------
SPRITE_PATHS = {
    "player": "sprites/player.png",
    "treasure": "sprites/treasure.gif",
    "heart": "sprites/heart.gif",
    "trap": "sprites/trap.png",
    "fog": "sprites/fog.png",
}

HIGHSCORE_FILE = "highscores.json"

# -----------------------------
# SIDEBAR: Settings
# -----------------------------
st.sidebar.title("⚙️ Game Settings")

grid_choice = st.sidebar.selectbox("Grid Size", ["4×4", "8×8", "16×16", "32×32"], index=1)
GRID_SIZE = int(grid_choice.split("×")[0])

difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Normal", "Hard"], index=1)

sound_enabled = st.sidebar.checkbox("🔊 Sound (placeholder, no files)", value=False)

# Scale object counts by grid area (so bigger grids have proportionally more objects)
area = GRID_SIZE * GRID_SIZE
# Base counts (for 8x8 baseline)
BASE = {
    "TREASURES": 3,
    "TRAPS": 2,
    "HEARTS": 2,
    "MOVES": 25,
    "TIME": 60,
}

difficulty_multipliers = {
    "Easy": 0.9,
    "Normal": 1.0,
    "Hard": 1.2,
}

mult = difficulty_multipliers[difficulty]

# compute counts proportionally to area, but keep ints and reasonable caps
treasures = max(1, int(BASE["TREASURES"] * (area / 64) * mult))
traps = max(1, int(BASE["TRAPS"] * (area / 64) * mult))
hearts = max(0, int(BASE["HEARTS"] * (area / 64) * (1.0 if difficulty != "Hard" else 0.8)))
move_limit = max(5, int(BASE["MOVES"] * (64 / area) * (1.0 if difficulty == "Normal" else (1.2 if difficulty == "Easy" else 0.9))))
time_limit = max(15, int(BASE["TIME"] * (64 / area) * (1.0 if difficulty == "Normal" else (1.2 if difficulty == "Easy" else 0.85))))

# Put some of those into session defaults later as needed

# -----------------------------
# Leaderboard helpers
# -----------------------------
def load_highscores():
    if not os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump([], f)
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_highscore(name, score):
    highscores = load_highscores()
    highscores.append({"name": name, "score": score})
    highscores = sorted(highscores, key=lambda x: x["score"], reverse=True)[:10]
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(highscores, f, indent=2)

# -----------------------------
# Game init & helpers
# -----------------------------
def init_game():
    """Initialize or reset the game state in session_state."""
    st.session_state.grid_size = GRID_SIZE
    st.session_state.player_pos = [0, 0]  # temporarily; will set after placing objects
    st.session_state.score = 0
    st.session_state.level = 1
    st.session_state.moves_left = move_limit
    st.session_state.time_limit = time_limit
    st.session_state.start_time = time.time()
    st.session_state.total_paused_time = 0.0
    st.session_state.paused = False
    st.session_state.pause_start = None
    st.session_state.game_over = False

    # prepare grid and revealed set
    size = st.session_state.grid_size
    st.session_state.grid = [["" for _ in range(size)] for _ in range(size)]
    st.session_state.revealed = set()  # store tuples (r,c)
    # Place objects first
    place_objects()
    # Now pick a random empty cell (no treasure/trap/heart) for player start
    empty_cells = [(r, c) for r in range(size) for c in range(size) if st.session_state.grid[r][c] == ""]
    if not empty_cells:
        # fallback to (0,0)
        st.session_state.player_pos = [0, 0]
    else:
        st.session_state.player_pos = list(random.choice(empty_cells))

    # reveal starting surroundings (player + neighbors)
    reveal_surroundings(st.session_state.player_pos[0], st.session_state.player_pos[1])


def place_objects():
    """Place treasures, traps, hearts on the grid without overwriting existing ones."""
    size = st.session_state.grid_size
    grid = st.session_state.grid

    def rand_empty():
        attempts = 0
        while True:
            r, c = random.randint(0, size - 1), random.randint(0, size - 1)
            if grid[r][c] == "":
                return r, c
            attempts += 1
            if attempts > size * size * 4:
                # fail-safe
                for i in range(size):
                    for j in range(size):
                        if grid[i][j] == "":
                            return i, j

    # place counts determined earlier
    for _ in range(treasures):
        r, c = rand_empty()
        grid[r][c] = "treasure"
    for _ in range(traps):
        r, c = rand_empty()
        grid[r][c] = "trap"
    for _ in range(hearts):
        r, c = rand_empty()
        grid[r][c] = "heart"

def reveal_surroundings(r, c):
    """Reveal the (r,c) and its eight neighbors permanently."""
    size = st.session_state.grid_size
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size:
                st.session_state.revealed.add((nr, nc))

# -----------------------------
# Movement & cell interaction
# -----------------------------
def move_player(direction):
    if st.session_state.game_over or st.session_state.paused:
        # ignore moves while paused or after game over
        return

    r, c = st.session_state.player_pos
    size = st.session_state.grid_size

    if direction == "up" and r > 0:
        r -= 1
    elif direction == "down" and r < size - 1:
        r += 1
    elif direction == "left" and c > 0:
        c -= 1
    elif direction == "right" and c < size - 1:
        c += 1
    else:
        # invalid move (edge) - do nothing
        return

    st.session_state.player_pos = [r, c]
    st.session_state.moves_left = max(0, st.session_state.moves_left - 1)

    reveal_surroundings(r, c)
    process_cell(r, c)
    # Check game-over by moves
    if st.session_state.moves_left <= 0:
        st.session_state.game_over = True
        st.toast("🚨 Out of moves! Game over.")

def process_cell(r, c):
    cell = st.session_state.grid[r][c]
    if cell == "treasure":
        st.session_state.score += 10
        st.toast("💰 Treasure +10")
    elif cell == "trap":
        st.session_state.score = max(0, st.session_state.score - 5)
        st.toast("💥 Trap -5")
    elif cell == "heart":
        st.session_state.score += 3
        st.toast("❤️ Heart +3")

    # After processing clear the cell (collected/triggered)
    st.session_state.grid[r][c] = ""

# -----------------------------
# Pause / Resume / Restart
# -----------------------------
def toggle_pause():
    if st.session_state.game_over:
        return
    if not st.session_state.paused:
        # pause start
        st.session_state.paused = True
        st.session_state.pause_start = time.time()
    else:
        # resume: accumulate paused duration
        paused_for = time.time() - (st.session_state.pause_start or time.time())
        st.session_state.total_paused_time += paused_for
        st.session_state.pause_start = None
        st.session_state.paused = False

def restart_game():
    init_game()

# -----------------------------
# Drawing grid (fixed area, auto shrink)
# -----------------------------
def draw_grid():
    size = st.session_state.grid_size
    grid = st.session_state.grid
    pr, pc = st.session_state.player_pos

    # fixed square area in px (keeps layout compact)
    GRID_AREA = 520
    tile_size = max(8, int(GRID_AREA / size))  # minimum tile size to avoid 0
    # Create CSS grid with fixed cell sizes
    st.markdown(
        f"""
        <style>
            .game-grid {{
                display: grid;
                grid-template-columns: repeat({size}, {tile_size}px);
                grid-template-rows: repeat({size}, {tile_size}px);
                gap: 3px;
                margin-left: auto;
                margin-right: auto;
                width: {min(GRID_AREA, tile_size*size + (size-1)*3)}px;
                height: {min(GRID_AREA, tile_size*size + (size-1)*3)}px;
            }}
            .cell img {{
                width: {tile_size}px;
                height: {tile_size}px;
                object-fit: cover;
                border-radius: 4px;
                display: block;
            }}
            .status-row {{
                display:flex; gap:12px; align-items:center;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    html = "<div class='game-grid'>"
    for r in range(size):
        for c in range(size):
            pos = (r, c)
            # Show player if on that tile (player always visible on own tile)
            if pos == tuple(st.session_state.player_pos):
                img_src = SPRITE_PATHS["player"]
            else:
                # revealed tiles show their actual content (treasure/trap/heart or empty)
                if pos in st.session_state.revealed:
                    tile = grid[r][c]
                    img_src = SPRITE_PATHS[tile] if tile in SPRITE_PATHS else SPRITE_PATHS["fog"]
                else:
                    # not revealed -> fog
                    img_src = SPRITE_PATHS["fog"]

            # Use relative path in src — Streamlit will serve local files when running locally
            html += f"<div class='cell'><img src='{img_src}' alt='cell'></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# -----------------------------
# Ensure session_state keys exist
# -----------------------------
required_keys = [
    "grid_size", "player_pos", "grid", "revealed", "score",
    "level", "moves_left", "time_limit", "start_time", "total_paused_time",
    "paused", "pause_start", "game_over"
]
if any(k not in st.session_state for k in required_keys):
    init_game()

# Update dynamic object counts (store for restart visibility)
st.session_state.treasures = treasures
st.session_state.traps = traps
st.session_state.hearts = hearts
st.session_state.move_limit = move_limit
st.session_state.time_limit = time_limit

# -----------------------------
# Timer computation (pauses accounted)
# -----------------------------
if st.session_state.paused and st.session_state.pause_start is not None:
    elapsed = st.session_state.pause_start - st.session_state.start_time - st.session_state.total_paused_time
else:
    elapsed = time.time() - st.session_state.start_time - st.session_state.total_paused_time

time_left = max(0, int(st.session_state.time_limit - elapsed))
if time_left == 0 and not st.session_state.game_over:
    st.session_state.game_over = True
    st.toast("⏳ Time's up! Game over.")

# -----------------------------
# UI Layout - Left: Grid, Right: Controls
# -----------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.title("🏝️ Treasure Hunt")
    draw_grid()
    # small legend under grid
    st.markdown(
        "<div style='display:flex;gap:12px;align-items:center;margin-top:8px'>"
        f"<div>Player ↦ <img src='{SPRITE_PATHS['player']}' style='height:20px;vertical-align:middle'></div>"
        f"<div>Treasure ↦ <img src='{SPRITE_PATHS['treasure']}' style='height:20px;vertical-align:middle'></div>"
        f"<div>Trap ↦ <img src='{SPRITE_PATHS['trap']}' style='height:20px;vertical-align:middle'></div>"
        f"<div>Heart ↦ <img src='{SPRITE_PATHS['heart']}' style='height:20px;vertical-align:middle'></div>"
        "</div>",
        unsafe_allow_html=True,
    )

with col2:
    st.subheader("Controls")

    # Pause / Resume / Restart
    pause_label = "▶️ Resume" if st.session_state.paused else "⏸ Pause"
    if st.button(pause_label):
        toggle_pause()

    if st.button("🔁 Restart"):
        restart_game()

    st.write("---")
    # Movement buttons (ignore actions if paused/game over inside move_player)
    disabled_note = ""
    if st.session_state.game_over:
        st.warning("Game Over - restart to play again.")
    elif st.session_state.paused:
        st.info("Paused - resume to continue playing.")

    # Movement layout — Up / Left Right / Down
    st.button("⬆️ Up", on_click=move_player, args=("up",))
    c1, c2 = st.columns(2)
    c1.button("⬅️ Left", on_click=move_player, args=("left",))
    c2.button("➡️ Right", on_click=move_player, args=("right",))
    st.button("⬇️ Down", on_click=move_player, args=("down",))

    st.write("---")
    st.markdown("<div class='status-row'>", unsafe_allow_html=True)
    st.metric("🕒 Time Left", f"{time_left}s")
    st.metric("🎯 Moves Left", st.session_state.moves_left)
    st.metric("⭐ Score", st.session_state.score)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("---")
    # Save score UI
    name = st.text_input("Name to save score:")
    if st.button("💾 Save Highscore"):
        if name.strip():
            save_highscore(name.strip(), st.session_state.score)
            st.success("Saved to leaderboard.")
        else:
            st.warning("Enter a name before saving.")

# -----------------------------
# Sidebar: Leaderboard summary & quick info
# -----------------------------
st.sidebar.title("🏆 Leaderboard")
hs = load_highscores()
if hs:
    for i, entry in enumerate(hs, 1):
        st.sidebar.write(f"**{i}. {entry['name']}** — {entry['score']} pts")
else:
    st.sidebar.info("No highscores yet.")

st.sidebar.write("---")
st.sidebar.write(f"Grid: {st.session_state.grid_size}×{st.session_state.grid_size}")
st.sidebar.write(f"Difficulty: {difficulty}")
st.sidebar.write(f"Treasures: {st.session_state.treasures}, Traps: {st.session_state.traps}, Hearts: {st.session_state.hearts}")
st.sidebar.write("Visibility: current tile + 8 neighbors")
st.sidebar.write("Reveal: permanent once seen")

# -----------------------------
# End: helpful tips
# -----------------------------
st.write("---")
st.info("Tip: Player starts at a random safe tile (not on a treasure/trap/heart). Revealed tiles stay revealed permanently. Use Pause to freeze the timer.")

