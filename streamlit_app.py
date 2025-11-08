# app.py - Treasure Hunt FINAL (timer per difficulty; Hard auto-random grid)
import streamlit as st
import random
import json
import os
import time
import base64
import mimetypes

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")

# -------------------------
# Sprite paths (local folder 'sprites/')
# If a file is missing, a small placeholder SVG will be used.
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
# Helper: convert file to data URI (so <img src=> works reliably)
# -------------------------
def file_to_data_uri(path):
    if not os.path.exists(path):
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64'>"
            "<rect width='100%' height='100%' fill='#e0e0e0'/>"
            "<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-size='10' fill='#777'>missing</text>"
            "</svg>"
        )
        b = svg.encode("utf-8")
        return "data:image/svg+xml;base64," + base64.b64encode(b).decode()
    ctype, _ = mimetypes.guess_type(path)
    if ctype is None:
        ctype = "application/octet-stream"
    with open(path, "rb") as f:
        data = f.read()
    return f"data:{ctype};base64," + base64.b64encode(data).decode()

SPRITES = {k: file_to_data_uri(v) for k, v in SPRITE_FILES.items()}

# -------------------------
# Sidebar: Settings
# -------------------------
st.sidebar.title("⚙️ Game Settings")

difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Normal", "Hard"], index=1)

# Rows & Cols selection enabled only for Easy/Normal. For Hard, grid is chosen automatically.
user_rows = st.sidebar.selectbox("Rows (only for Easy/Normal)", [4, 6, 8, 12, 16], index=2)
user_cols = st.sidebar.selectbox("Cols (only for Easy/Normal)", [4, 6, 8, 12, 16, 24, 32], index=2)

# Hard mode picks grid randomly from this list:
HARD_GRID_CHOICES = [(8, 12), (12, 16), (16, 24), (16, 32)]

sound_enabled = st.sidebar.checkbox("🔊 Sound (placeholder)", value=False)

# -------------------------
# Difficulty-based timer (confirmed)
# Easy = 180s, Normal = 300s, Hard = 420s
# -------------------------
TIME_BY_DIFFICULTY = {"Easy": 180, "Normal": 300, "Hard": 420}

# -------------------------
# Scaling base values (baseline around 8x8 => area 64)
# -------------------------
BASE = {"TREASURES": 3, "TRAPS": 2, "HEARTS": 2, "MOVES": 25}

DIFF_MULT = {"Easy": 0.9, "Normal": 1.0, "Hard": 1.25}[difficulty]

# -------------------------
# Leaderboard utilities
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
# Visibility radius (B3)
# Chebyshev radius 2 => 5x5
# -------------------------
VIS_RADIUS = 2

# -------------------------
# Game initialization
# -------------------------
def choose_grid_for_mode():
    """Return (rows, cols). For Hard, pick random from HARD_GRID_CHOICES; else use user selection."""
    if difficulty == "Hard":
        return random.choice(HARD_GRID_CHOICES)
    return (user_rows, user_cols)

def init_game():
    """Initialize a fresh game in session_state."""
    rows, cols = choose_grid_for_mode()
    st.session_state.rows = rows
    st.session_state.cols = cols

    # prepare grid and session values
    st.session_state.grid = [["" for _ in range(cols)] for _ in range(rows)]
    st.session_state.revealed = set()  # set of (r,c) permanently revealed
    st.session_state.score = 0
    st.session_state.level = 1

    # scale objects by area (baseline 8x8 = 64)
    area = rows * cols
    st.session_state.treasures = max(1, int(BASE["TREASURES"] * (area / 64) * DIFF_MULT))
    st.session_state.traps = max(1, int(BASE["TRAPS"] * (area / 64) * DIFF_MULT))
    st.session_state.hearts = max(0, int(BASE["HEARTS"] * (area / 64) * (0.9 if difficulty == "Hard" else 1.0)))

    # moves: scale inversely by area (bigger area -> relatively fewer moves per tile)
    st.session_state.move_limit = max(5, int(BASE["MOVES"] * (64 / max(1, area)) * (1.15 if difficulty == "Easy" else (0.9 if difficulty == "Hard" else 1.0))))
    st.session_state.moves_left = st.session_state.move_limit

    # timer
    st.session_state.time_limit = TIME_BY_DIFFICULTY[difficulty]
    st.session_state.start_time = time.time()
    st.session_state.total_paused = 0.0
    st.session_state.paused = False
    st.session_state.pause_start = None

    st.session_state.game_over = False

    # populate objects then pick start pos
    place_objects()
    # pick a random empty cell for the player (safe start)
    empty = [(r, c) for r in range(rows) for c in range(cols) if st.session_state.grid[r][c] == ""]
    if empty:
        st.session_state.player_pos = list(random.choice(empty))
    else:
        st.session_state.player_pos = [0, 0]

    # reveal starting surroundings
    reveal_radius(st.session_state.player_pos[0], st.session_state.player_pos[1], VIS_RADIUS)

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

# -------------------------
# Movement & cell processing
# -------------------------
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

# -------------------------
# Pause / Resume / Restart
# -------------------------
def toggle_pause():
    if st.session_state.game_over:
        return
    if not st.session_state.paused:
        st.session_state.paused = True
        st.session_state.pause_start = time.time()
    else:
        # resume
        paused_for = time.time() - (st.session_state.pause_start or time.time())
        st.session_state.total_paused += paused_for
        st.session_state.pause_start = None
        st.session_state.paused = False

def restart_game():
    init_game()

# -------------------------
# Draw grid (fixed area)
# -------------------------
def draw_grid():
    rows = st.session_state.rows
    cols = st.session_state.cols
    grid = st.session_state.grid
    pr, pc = st.session_state.player_pos

    GRID_AREA = 520  # px square area
    max_dim = max(rows, cols)
    tile_size = max(8, int(GRID_AREA / max_dim))
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
# Ensure session state keys exist (init if missing)
# -------------------------
required_keys = [
    "rows", "cols", "grid", "revealed", "player_pos",
    "score", "moves_left", "time_limit", "start_time",
    "total_paused", "paused", "pause_start", "game_over",
    "treasures", "traps", "hearts", "move_limit"
]
if any(k not in st.session_state for k in required_keys):
    init_game()

# If difficulty switched to Hard (auto grid) or user changed selection, re-init accordingly
# For Hard: always re-init to pick a fresh random grid choice
if difficulty == "Hard":
    # If previous difficulty wasn't Hard or grid dims don't match Hard-picked dims, re-init.
    if ("_last_difficulty" not in st.session_state) or st.session_state.get("_last_difficulty") != "Hard":
        init_game()
else:
    # Non-Hard: if user changed rows/cols compared to current session size, re-init
    if st.session_state.rows != user_rows or st.session_state.cols != user_cols:
        init_game()

st.session_state["_last_difficulty"] = difficulty

# Update dynamic session values (so side info is correct)
st.session_state.time_limit = TIME_BY_DIFFICULTY[difficulty]

# -------------------------
# Timer accounting (pauses included). When timer reaches 0 => Game Over (confirmed)
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
# UI Layout: left grid, right controls
# -------------------------
col_left, col_right = st.columns([3, 1])

with col_left:
    st.title("🏝️ Treasure Hunt")
    # show chosen grid size (for Hard, show the randomly chosen one)
    st.caption(f"Grid: {st.session_state.rows}×{st.session_state.cols} — Difficulty: {difficulty}")
    draw_grid()
    # small legend
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
# Sidebar: leaderboard & summary
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
st.sidebar.write(f"Treasures: {st.session_state.treasures} | Traps: {st.session_state.traps} | Hearts: {st.session_state.hearts}")
st.sidebar.write(f"Moves: {st.session_state.move_limit}")
st.sidebar.write(f"Timer: {st.session_state.time_limit}s (Easy=180s, Normal=300s, Hard=420s)")
st.sidebar.write("Visibility: Chebyshev radius 2 (5×5). Revealed permanently.")
st.sidebar.write("Pause: hides tiles except your current tile; timer frozen while paused.")

st.write("---")
st.info("Tip: In Hard mode the grid size is chosen randomly from preset large sizes. Player always spawns on a random empty tile (not on treasures/traps/hearts).")
