# app.py - Final verified Treasure Hunt (A2, B3, C1)
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
# Sprite filenames (in sprites/)
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
# Helpers: Data URI for local images (so <img src=...> works reliably)
# -------------------------
def file_to_data_uri(path):
    """Return a data URI for the file at path. If missing, return a small placeholder SVG data URI."""
    if not os.path.exists(path):
        # placeholder SVG (small colored square)
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64'>"
            "<rect width='100%' height='100%' fill='#cccccc'/>"
            "<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-size='10' fill='#666'>missing</text>"
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

# Precompute data URIs for sprites (safe if run multiple times)
SPRITES = {k: file_to_data_uri(v) for k, v in SPRITE_FILES.items()}

# -------------------------
# Sidebar settings
# -------------------------
st.sidebar.title("⚙️ Game Settings")

# Non-square allowed: let user pick rows × cols
rows = st.sidebar.selectbox("Rows", [4, 6, 8, 12, 16], index=2)
cols = st.sidebar.selectbox("Cols", [4, 6, 8, 12, 16, 24, 32], index=2)

# Difficulty & sound placeholder
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Normal", "Hard"], index=1)
sound_enabled = st.sidebar.checkbox("🔊 Sound (placeholder)", value=False)

# Base counts & scaling by area
area = rows * cols
BASE = {"TREASURES": 3, "TRAPS": 2, "HEARTS": 2, "MOVES": 25, "TIME": 60}
diff_mult = {"Easy": 0.9, "Normal": 1.0, "Hard": 1.25}[difficulty]

# Scale objects with area but bound them reasonably
treasures = max(1, int(BASE["TREASURES"] * (area / 64) * diff_mult))
traps = max(1, int(BASE["TRAPS"] * (area / 64) * diff_mult))
hearts = max(0, int(BASE["HEARTS"] * (area / 64) * (0.9 if difficulty == "Hard" else 1.0)))

# Moves/time: bigger grids get fewer moves per tile but scaled sensibly
move_limit = max(5, int(BASE["MOVES"] * (64 / max(1, area)) * (1.15 if difficulty == "Easy" else (0.9 if difficulty == "Hard" else 1.0))))
time_limit = max(15, int(BASE["TIME"] * (64 / max(1, area)) * (1.2 if difficulty == "Easy" else (0.85 if difficulty == "Hard" else 1.0))))

# -------------------------
# Leaderboard functions
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
# Game init & helpers
# -------------------------
VIS_RADIUS = 2  # B3: Chebyshev radius 2 => 5x5 area

def init_game():
    """Initialize the session state values for a new game."""
    st.session_state.rows = rows
    st.session_state.cols = cols
    st.session_state.grid = [["" for _ in range(st.session_state.cols)] for _ in range(st.session_state.rows)]
    st.session_state.revealed = set()  # permanently revealed cells (r,c)
    st.session_state.score = 0
    st.session_state.level = 1
    st.session_state.moves_left = move_limit
    st.session_state.time_limit = time_limit
    st.session_state.start_time = time.time()
    st.session_state.total_paused = 0.0
    st.session_state.paused = False
    st.session_state.pause_start = None
    st.session_state.game_over = False
    st.session_state.treasures = treasures
    st.session_state.traps = traps
    st.session_state.hearts = hearts

    # Place objects
    place_objects()
    # Choose a random safe start cell (empty)
    empty = [(r, c) for r in range(st.session_state.rows) for c in range(st.session_state.cols) if st.session_state.grid[r][c] == ""]
    if not empty:
        st.session_state.player_pos = [0, 0]
    else:
        st.session_state.player_pos = list(random.choice(empty))
    # Reveal starting area
    reveal_radius(st.session_state.player_pos[0], st.session_state.player_pos[1], VIS_RADIUS)

def place_objects():
    """Place treasures, traps, hearts randomly without overwriting."""
    rcount = st.session_state.rows
    ccount = st.session_state.cols
    grid = st.session_state.grid

    def rand_empty():
        attempts = 0
        while True:
            rr = random.randint(0, rcount - 1)
            cc = random.randint(0, ccount - 1)
            if grid[rr][cc] == "":
                return rr, cc
            attempts += 1
            if attempts > rcount * ccount * 3:
                # fallback: first empty
                for i in range(rcount):
                    for j in range(ccount):
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
    """Reveal the square area within Chebyshev radius."""
    rows_ = st.session_state.rows
    cols_ = st.session_state.cols
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows_ and 0 <= nc < cols_:
                st.session_state.revealed.add((nr, nc))

# -------------------------
# Movement & interaction
# -------------------------
def process_cell(r, c):
    grid = st.session_state.grid
    cell = grid[r][c]
    if cell == "treasure":
        st.session_state.score += 10
        st.toast("💰 Treasure +10")
    elif cell == "trap":
        st.session_state.score = max(0, st.session_state.score - 5)
        st.toast("💥 Trap -5")
    elif cell == "heart":
        st.session_state.score += 3
        st.toast("❤️ Heart +3")
    # clear the cell once processed
    grid[r][c] = ""

def move_player(direction):
    if st.session_state.game_over or st.session_state.paused:
        return
    r, c = st.session_state.player_pos
    rows_ = st.session_state.rows
    cols_ = st.session_state.cols

    if direction == "up" and r > 0:
        r -= 1
    elif direction == "down" and r < rows_ - 1:
        r += 1
    elif direction == "left" and c > 0:
        c -= 1
    elif direction == "right" and c < cols_ - 1:
        c += 1
    else:
        return  # invalid move (edge)

    st.session_state.player_pos = [r, c]
    st.session_state.moves_left = max(0, st.session_state.moves_left - 1)
    # reveal radius VIS_RADIUS
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
# Draw grid (fixed area, no scrolling)
# -------------------------
def draw_grid():
    rows_ = st.session_state.rows
    cols_ = st.session_state.cols
    grid = st.session_state.grid
    pr, pc = st.session_state.player_pos

    GRID_AREA = 520  # px - fixed square area (main grid container)
    # tile_size based on the larger of rows/cols so both dimensions fit
    max_dim = max(rows_, cols_)
    tile_size = max(8, int(GRID_AREA / max_dim))  # minimum tile size to avoid 0
    container_width = tile_size * cols_ + (cols_ - 1) * 3
    container_height = tile_size * rows_ + (rows_ - 1) * 3

    # CSS
    st.markdown(
        f"""
        <style>
            .game-grid {{
                display: grid;
                grid-template-columns: repeat({cols_}, {tile_size}px);
                grid-template-rows: repeat({rows_}, {tile_size}px);
                gap: 3px;
                margin-left: auto;
                margin-right: auto;
                width: {container_width}px;
                height: {container_height}px;
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
    for r in range(rows_):
        for c in range(cols_):
            pos = (r, c)
            # If paused (C1) -> hide everything except current tile
            if st.session_state.paused and pos != tuple(st.session_state.player_pos):
                img_uri = SPRITES["fog"]
            else:
                # If pos is player -> always show player sprite
                if pos == tuple(st.session_state.player_pos):
                    img_uri = SPRITES["player"]
                else:
                    # Only show actual content if permanently revealed; else fog
                    if pos in st.session_state.revealed:
                        tile = grid[r][c]
                        img_uri = SPRITES.get(tile, SPRITES["fog"])
                    else:
                        img_uri = SPRITES["fog"]
            html += f"<div class='cell'><img src='{img_uri}' alt='cell'/></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# -------------------------
# Ensure session state keys exist (init if not)
# -------------------------
required = [
    "rows", "cols", "grid", "revealed", "player_pos",
    "score", "moves_left", "time_limit", "start_time",
    "total_paused", "paused", "pause_start", "game_over",
    "treasures", "traps", "hearts"
]
if any(k not in st.session_state for k in required):
    init_game()

# If user changed sidebar rows/cols/difficulty between runs, detect mismatch and re-init
if st.session_state.rows != rows or st.session_state.cols != cols:
    init_game()

# Update dynamic counts into session state (useful for restart/side info)
st.session_state.treasures = treasures
st.session_state.traps = traps
st.session_state.hearts = hearts
st.session_state.move_limit = move_limit
st.session_state.time_limit = time_limit

# -------------------------
# Timer accounting (pauses considered)
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
# Layout: left grid, right controls
# -------------------------
col_left, col_right = st.columns([3, 1])

with col_left:
    st.title("🏝️ Treasure Hunt")
    draw_grid()
    # legend
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
    # Pause/Resume
    pause_label = "▶️ Resume" if st.session_state.paused else "⏸ Pause"
    if st.button(pause_label):
        toggle_pause()

    if st.button("🔁 Restart"):
        restart_game()

    st.write("---")
    # Movement buttons
    if st.session_state.game_over:
        st.warning("Game Over — press Restart to play again.")
    elif st.session_state.paused:
        st.info("Paused — press Resume to continue.")

    # Buttons still rendered but actions ignored by move_player when paused/game-over
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
# Sidebar: Leaderboard & info
# -------------------------
st.sidebar.title("🏆 Leaderboard")
hs = load_highscores()
if hs:
    for i, e in enumerate(hs, 1):
        st.sidebar.write(f"**{i}. {e['name']}** — {e['score']} pts")
else:
    st.sidebar.info("No highscores yet.")

st.sidebar.write("---")
st.sidebar.write(f"Grid: {st.session_state.rows}×{st.session_state.cols}")
st.sidebar.write(f"Difficulty: {difficulty}")
st.sidebar.write(f"Treasures: {st.session_state.treasures} — Traps: {st.session_state.traps} — Hearts: {st.session_state.hearts}")
st.sidebar.write("Visibility: Chebyshev radius 2 (5×5) - permanent once revealed")
st.sidebar.write("Pause behavior: All tiles hidden except player's tile")

# -------------------------
# Tips
# -------------------------
st.write("---")
st.info("Tip: Player starts on a random empty tile (not on treasure/trap/heart). Revealed tiles stay revealed permanently. While paused, only your current tile is visible.")
