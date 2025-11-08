# app.py - Treasure Hunt (Option C: auto-scale tiles, no scrolling)
import streamlit as st
import random
import json
import os
import time
import base64
import mimetypes

# -------------------------
# Basic page config
# -------------------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")

# -------------------------
# Sprite files (local folder 'sprites/')
# If missing, a small SVG placeholder will be used.
# -------------------------
SPRITE_FILES = {
    "player": "sprites/player.png",
    "treasure": "sprites/treasure.gif",
    "heart": "sprites/heart.gif",
    "trap": "sprites/trap.png",
    "fog": "sprites/fog.png",
}

HIGHSCORE_FILE = "highscores.json"

# -------------------------
# Helper to load file -> data URI
# -------------------------
def file_to_data_uri(path):
    if not os.path.exists(path):
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64'>"
            "<rect width='100%' height='100%' fill='#ddd'/>"
            "<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-size='10' fill='#666'>missing</text>"
            "</svg>"
        )
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    ctype, _ = mimetypes.guess_type(path)
    if ctype is None:
        ctype = "application/octet-stream"
    with open(path, "rb") as f:
        data = f.read()
    return f"data:{ctype};base64," + base64.b64encode(data).decode()

SPRITES = {k: file_to_data_uri(v) for k, v in SPRITE_FILES.items()}

# -------------------------
# Sidebar: user settings
# -------------------------
st.sidebar.title("⚙️ Game Settings")

difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Normal", "Hard"], index=1)

# If Hard, grid choice will be random; otherwise user can choose rows/cols
user_rows = st.sidebar.selectbox("Rows (Easy/Normal)", [4, 6, 8, 12, 16], index=2)
user_cols = st.sidebar.selectbox("Cols (Easy/Normal)", [4, 6, 8, 12, 16, 24, 32], index=2)

HARD_GRID_CHOICES = [(8, 12), (12, 16), (16, 24), (16, 32)]

sound_enabled = st.sidebar.checkbox("🔊 Sound (placeholder)", value=False)

# Timer per difficulty
TIME_BY_DIFFICULTY = {"Easy": 180, "Normal": 300, "Hard": 420}

# Base counts
BASE = {"TREASURES": 3, "TRAPS": 2, "HEARTS": 2, "MOVES": 25}
DIFF_MULT = {"Easy": 0.9, "Normal": 1.0, "Hard": 1.25}[difficulty]

# Visibility radius (Chebyshev)
VIS_RADIUS = 2

# -------------------------
# Leaderboard helpers
# -------------------------
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
    hs = load_highscores()
    hs.append({"name": name, "score": score})
    hs = sorted(hs, key=lambda x: x["score"], reverse=True)[:10]
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(hs, f, indent=2)

# -------------------------
# Game functions
# -------------------------
def choose_grid():
    if difficulty == "Hard":
        return random.choice(HARD_GRID_CHOICES)
    return (user_rows, user_cols)

def init_game(force=False):
    """
    Initialize session state. If force True, reinit even if keys exist.
    """
    # If already initialized and not forced, do nothing
    if not force and "initialized" in st.session_state:
        return

    rows, cols = choose_grid()
    st.session_state.rows = rows
    st.session_state.cols = cols
    st.session_state.grid = [["" for _ in range(cols)] for _ in range(rows)]
    st.session_state.revealed = set()
    st.session_state.score = 0
    st.session_state.level = 1
    st.session_state.treasures = max(1, int(BASE["TREASURES"] * ((rows*cols) / 64) * DIFF_MULT))
    st.session_state.traps = max(1, int(BASE["TRAPS"] * ((rows*cols) / 64) * DIFF_MULT))
    st.session_state.hearts = max(0, int(BASE["HEARTS"] * ((rows*cols) / 64) * (0.9 if difficulty == "Hard" else 1.0)))
    st.session_state.move_limit = max(5, int(BASE["MOVES"] * (64 / max(1, rows*cols)) * (1.15 if difficulty == "Easy" else (0.9 if difficulty == "Hard" else 1.0))))
    st.session_state.moves_left = st.session_state.move_limit
    st.session_state.time_limit = TIME_BY_DIFFICULTY[difficulty]
    st.session_state.start_time = time.time()
    st.session_state.total_paused = 0.0
    st.session_state.paused = False
    st.session_state.pause_start = None
    st.session_state.game_over = False

    # place objects then choose start position
    place_objects()
    empty = [(r, c) for r in range(rows) for c in range(cols) if st.session_state.grid[r][c] == ""]
    st.session_state.player_pos = list(random.choice(empty)) if empty else [0, 0]
    reveal_radius(st.session_state.player_pos[0], st.session_state.player_pos[1], VIS_RADIUS)
    st.session_state.initialized = True
    # store current config snapshot to detect changes (no infinite re-init)
    st.session_state._config_snapshot = {"difficulty": difficulty, "rows": rows, "cols": cols}

def place_objects():
    rows = st.session_state.rows
    cols = st.session_state.cols
    grid = st.session_state.grid

    def rand_empty():
        attempts = 0
        while True:
            r = random.randint(0, rows - 1)
            c = random.randint(0, cols - 1)
            if grid[r][c] == "":
                return r, c
            attempts += 1
            if attempts > rows * cols * 3:
                for i in range(rows):
                    for j in range(cols):
                        if grid[i][j] == "":
                            return i, j

    for _ in range(st.session_state.treasures):
        r, c = rand_empty()
        grid[r][c] = "treasure"
    for _ in range(st.session_state.traps):
        r, c = rand_empty()
        grid[r][c] = "trap"
    for _ in range(st.session_state.hearts):
        r, c = rand_empty()
        grid[r][c] = "heart"

def reveal_radius(r, c, radius):
    rows = st.session_state.rows
    cols = st.session_state.cols
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                st.session_state.revealed.add((nr, nc))

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
    st.session_state.grid[r][c] = ""

def move_player(direction):
    if st.session_state.game_over or st.session_state.paused:
        return
    r, c = st.session_state.player_pos
    rows = st.session_state.rows
    cols = st.session_state.cols

    if direction == "up" and r > 0:
        r -= 1
    elif direction == "down" and r < rows - 1:
        r += 1
    elif direction == "left" and c > 0:
        c -= 1
    elif direction == "right" and c < cols - 1:
        c += 1
    else:
        return

    st.session_state.player_pos = [r, c]
    st.session_state.moves_left = max(0, st.session_state.moves_left - 1)
    reveal_radius(r, c, VIS_RADIUS)
    process_cell(r, c)

    if st.session_state.moves_left <= 0:
        st.session_state.game_over = True
        st.toast("🚨 Out of moves! Game over.")

def toggle_pause():
    if st.session_state.game_over:
        return
    if not st.session_state.paused:
        st.session_state.paused = True
        st.session_state.pause_start = time.time()
    else:
        paused_for = time.time() - (st.session_state.pause_start or time.time())
        st.session_state.total_paused += paused_for
        st.session_state.pause_start = None
        st.session_state.paused = False

def restart_game():
    # force re-init to pick new random grid in Hard, etc.
    init_game(force=True)

# -------------------------
# Grid drawing (Option C auto-scaling)
# Use CSS grid and data URIs to avoid heavy Streamlit columns calls
# -------------------------
def compute_tile_size(rows, cols, max_area_px=520):
    """Return tile_size px based on largest dimension (Option C mapping)."""
    max_dim = max(rows, cols)
    # mapping (C strategy): chunky for small grids, compact for large
    if max_dim <= 4:
        return min(140, int(max_area_px / max_dim))
    if max_dim <= 8:
        return min(100, int(max_area_px / max_dim))
    if max_dim <= 12:
        return min(72, int(max_area_px / max_dim))
    if max_dim <= 16:
        return min(48, int(max_area_px / max_dim))
    if max_dim <= 24:
        return min(34, int(max_area_px / max_dim))
    return max(16, int(max_area_px / max_dim))

def draw_grid():
    rows = st.session_state.rows
    cols = st.session_state.cols
    grid = st.session_state.grid
    pr, pc = st.session_state.player_pos

    tile_size = compute_tile_size(rows, cols, max_area_px=520)
    container_w = tile_size * cols + (cols - 1) * 3
    container_h = tile_size * rows + (rows - 1) * 3

    st.markdown(
        f"""
        <style>
            .game-grid {{
                display: grid;
                grid-template-columns: repeat({cols}, {tile_size}px);
                grid-template-rows: repeat({rows}, {tile_size}px);
                gap: 3px;
                margin-left: auto;
                margin-right: auto;
                width: {container_w}px;
                height: {container_h}px;
                overflow: hidden;
            }}
            .cell img {{
                width: {tile_size}px;
                height: {tile_size}px;
                object-fit: cover;
                display:block;
                border-radius: 4px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    html = "<div class='game-grid'>"
    for r in range(rows):
        for c in range(cols):
            pos = (r, c)
            # If paused (C1) hide except player's tile
            if st.session_state.paused and pos != tuple(st.session_state.player_pos):
                img_uri = SPRITES["fog"]
            else:
                if pos == tuple(st.session_state.player_pos):
                    img_uri = SPRITES["player"]
                else:
                    if pos in st.session_state.revealed:
                        tile = grid[r][c]
                        img_uri = SPRITES.get(tile, SPRITES["fog"])
                    else:
                        img_uri = SPRITES["fog"]
            html += f"<div class='cell'><img src='{img_uri}' alt='cell'/></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# -------------------------
# Initialization: only when needed to avoid rerun loops
# -------------------------
# If not yet initialized, init
if "initialized" not in st.session_state:
    init_game()

# If config changed (difficulty or user selection for non-Hard), re-init once
current_snapshot = {"difficulty": difficulty}
if difficulty != "Hard":
    current_snapshot.update({"rows": user_rows, "cols": user_cols})
else:
    # Hard: snapshot does not include rows/cols (they're chosen randomly each new init)
    current_snapshot.update({"rows": st.session_state.rows, "cols": st.session_state.cols})

if st.session_state.get("_config_snapshot") != current_snapshot:
    # If user changed difficulty or dimensions, reinit (force)
    init_game(force=True)

st.session_state["_config_snapshot"] = current_snapshot

# Update time limit in session (in case difficulty changed)
st.session_state.time_limit = TIME_BY_DIFFICULTY[difficulty]

# -------------------------
# Timer accounting (pauses included). When time_left == 0 => Game Over
# -------------------------
if st.session_state.paused and st.session_state.pause_start is not None:
    elapsed = st.session_state.pause_start - st.session_state.start_time - st.session_state.total_paused
else:
    elapsed = time.time() - st.session_state.start_time - st.session_state.total_paused

time_left = max(0, int(st.session_state.time_limit - elapsed))
if time_left == 0 and not st.session_state.game_over:
    st.session_state.game_over = True
    st.toast("⏳ Time's up! Game over.")

# -------------------------
# UI layout
# -------------------------
col_left, col_right = st.columns([3, 1])

with col_left:
    st.title("🏝️ Treasure Hunt")
    st.caption(f"Grid: {st.session_state.rows}×{st.session_state.cols}  •  Difficulty: {difficulty}")
    draw_grid()
    # legend under grid
    st.markdown(
        "<div style='display:flex;gap:10px;align-items:center;margin-top:8px'>"
        f"<div>Player <img src='{SPRITES['player']}' style='height:20px;vertical-align:middle'></div>"
        f"<div>Treasure <img src='{SPRITES['treasure']}' style='height:20px;vertical-align:middle'></div>"
        f"<div>Trap <img src='{SPRITES['trap']}' style='height:20px;vertical-align:middle'></div>"
        f"<div>Heart <img src='{SPRITES['heart']}' style='height:20px;vertical-align:middle'></div>"
        "</div>",
        unsafe_allow_html=True,
    )

with col_right:
    st.subheader("Controls")
    pause_label = "▶️ Resume" if st.session_state.paused else "⏸ Pause"
    if st.button(pause_label):
        toggle_pause()
    if st.button("🔁 Restart"):
        restart_game()

    st.write("---")
    if st.session_state.game_over:
        st.warning("Game Over — press Restart to play again.")
    elif st.session_state.paused:
        st.info("Paused — only current tile visible; timer frozen.")

    st.button("⬆️ Up", on_click=move_player, args=("up",))
    c1, c2 = st.columns(2)
    c1.button("⬅️ Left", on_click=move_player, args=("left",))
    c2.button("➡️ Right", on_click=move_player, args=("right",))
    st.button("⬇️ Down", on_click=move_player, args=("down",))

    st.write("---")
    st.metric("🕒 Time Left", f"{time_left}s")
    st.metric("🎯 Moves Left", st.session_state.moves_left)
    st.metric("⭐ Score", st.session_state.score)

    st.write("---")
    name = st.text_input("Enter name to save score:")
    if st.button("💾 Save Highscore"):
        if name.strip():
            save_highscore(name.strip(), st.session_state.score)
            st.success("Saved to leaderboard.")
        else:
            st.warning("Enter a name before saving.")

# -------------------------
# Sidebar summary & leaderboard
# -------------------------
st.sidebar.title("🏆 Leaderboard")
hs = load_highscores()
if hs:
    for i, e in enumerate(hs, 1):
        st.sidebar.write(f"**{i}. {e['name']}** — {e['score']} pts")
else:
    st.sidebar.info("No highscores yet.")

st.sidebar.write("---")
st.sidebar.write(f"Mode: {difficulty}")
st.sidebar.write(f"Grid: {st.session_state.rows}×{st.session_state.cols}")
st.sidebar.write(f"Treasures: {st.session_state.treasures}  Traps: {st.session_state.traps}  Hearts: {st.session_state.hearts}")
st.sidebar.write(f"Moves: {st.session_state.move_limit}")
st.sidebar.write(f"Timer: {st.session_state.time_limit}s (Easy=180s, Normal=300s, Hard=420s)")
st.sidebar.write("Visibility: Chebyshev radius 2 (5×5) — permanently revealed")
st.sidebar.write("Pause: hides tiles except your current tile; timer frozen while paused")

st.write("---")
st.info("Tip: Player spawns on a random safe tile (not on treasure/trap/heart). Use Restart to reshuffle grid (Hard picks a random large grid).")
