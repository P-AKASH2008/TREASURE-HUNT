import streamlit as st
import random
import json
import os
import time

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Treasure Hunt",
    layout="wide",
)

# ----------------------------
# ASSETS / SPRITES
# ----------------------------
SPRITE_PATHS = {
    "player": "sprites/player.png",
    "treasure": "sprites/treasure.gif",
    "heart": "sprites/heart.gif",
    "trap": "sprites/trap.png",
    "fog": "sprites/fog.png",
}

HIGHSCORE_FILE = "highscores.json"

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.title("⚙️ Settings")

grid_size_choice = st.sidebar.selectbox(
    "Grid Size",
    ("4×4", "8×8", "16×16"),
    index=1
)

GRID_SIZE = int(grid_size_choice.split("×")[0])  # convert "8×8" -> 8

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ("Easy", "Normal", "Hard")
)

sound_enabled = st.sidebar.toggle("🔊 Sound Effects", value=False)

# ----------------------------
# DIFFICULTY SETTINGS
# ----------------------------
difficulty_config = {
    "Easy":  {"TREASURES": 4, "TRAPS": 1, "HEARTS": 3, "MOVES": 35, "TIME": 90},
    "Normal":{"TREASURES": 3, "TRAPS": 2, "HEARTS": 2, "MOVES": 25, "TIME": 60},
    "Hard":  {"TREASURES": 2, "TRAPS": 4, "HEARTS": 1, "MOVES": 20, "TIME": 45},
}
config = difficulty_config[difficulty]

# ----------------------------
# HIGHSCORE FUNCTIONS
# ----------------------------
def load_highscores():
    if not os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump([], f)
    with open(HIGHSCORE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_highscore(name, score):
    highscores = load_highscores()
    highscores.append({"name": name, "score": score})
    highscores = sorted(highscores, key=lambda x: x["score"], reverse=True)[:10]
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(highscores, f, indent=2)

# ----------------------------
# INIT GAME
# ----------------------------
def init_game():
    st.session_state.player_pos = [0, 0]
    st.session_state.score = 0
    st.session_state.level = 1

    st.session_state.moves_left = config["MOVES"]
    st.session_state.time_limit = config["TIME"]
    st.session_state.start_time = time.time()

    st.session_state.grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    st.session_state.revealed = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
    st.session_state.revealed[0][0] = True
    st.session_state.game_over = False

    place_objects()

def place_objects():
    grid = st.session_state.grid

    def random_empty_cell():
        while True:
            r, c = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if grid[r][c] == "" and [r, c] != st.session_state.player_pos:
                return r, c

    for _ in range(config["TREASURES"]):
        r, c = random_empty_cell()
        grid[r][c] = "treasure"

    for _ in range(config["TRAPS"]):
        r, c = random_empty_cell()
        grid[r][c] = "trap"

    for _ in range(config["HEARTS"]):
        r, c = random_empty_cell()
        grid[r][c] = "heart"

# ----------------------------
# MOVE + GAME LOGIC
# ----------------------------
def reveal_cells(r, c):
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                st.session_state.revealed[nr][nc] = True

def move_player(direction):
    if st.session_state.game_over:
        return

    r, c = st.session_state.player_pos
    if direction == "up" and r > 0: r -= 1
    elif direction == "down" and r < GRID_SIZE - 1: r += 1
    elif direction == "left" and c > 0: c -= 1
    elif direction == "right" and c < GRID_SIZE - 1: c += 1

    st.session_state.player_pos = [r, c]
    reveal_cells(r, c)
    st.session_state.moves_left -= 1

    check_cell(r, c)

def check_cell(r, c):
    cell = st.session_state.grid[r][c]

    if cell == "treasure":
        st.session_state.score += 10
        st.session_state.grid[r][c] = ""
        st.toast("💰 You found a treasure!")

    elif cell == "trap":
        st.session_state.score -= 5
        st.session_state.grid[r][c] = ""
        st.toast("💥 Trap!")

    elif cell == "heart":
        st.session_state.score += 3
        st.session_state.grid[r][c] = ""
        st.toast("❤️ Health Bonus!")

    if st.session_state.moves_left <= 0:
        st.session_state.game_over = True
        st.error("🚨 You're out of moves!")

# ----------------------------
# DRAW GRID
# ----------------------------
def draw_grid():
    grid = st.session_state.grid
    revealed = st.session_state.revealed
    pr, pc = st.session_state.player_pos

    for r in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE, gap="small")
        for c in range(GRID_SIZE):
            if [r, c] == [pr, pc]:
                cols[c].image(SPRITE_PATHS["player"], use_container_width=True)
            elif revealed[r][c]:
                if grid[r][c] == "treasure":
                    cols[c].image(SPRITE_PATHS["treasure"])
                elif grid[r][c] == "trap":
                    cols[c].image(SPRITE_PATHS["trap"])
                elif grid[r][c] == "heart":
                    cols[c].image(SPRITE_PATHS["heart"])
                else:
                    cols[c].image(SPRITE_PATHS["fog"])
            else:
                cols[c].image(SPRITE_PATHS["fog"])

# ----------------------------
# START GAME IF NOT INIT
# ----------------------------
if "grid" not in st.session_state:
    init_game()

# ----------------------------
# TIMER CHECK
# ----------------------------
elapsed = int(time.time() - st.session_state.start_time)
time_left = config["TIME"] - elapsed

if time_left <= 0 and not st.session_state.game_over:
    st.session_state.game_over = True
    st.error("⏳ Time's up!")

# ----------------------------
# UI LAYOUT
# ----------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.title("🏝️ Treasure Hunt")
    draw_grid()

with col2:
    st.subheader("Controls")

    if not st.session_state.game_over:
        st.button("⬆️", on_click=move_player, args=("up",), use_container_width=True)
        c1, c2 = st.columns(2)
        c1.button("⬅️", on_click=move_player, args=("left",), use_container_width=True)
        c2.button("➡️", on_click=move_player, args=("right",), use_container_width=True)
        st.button("⬇️", on_click=move_player, args=("down",), use_container_width=True)
    else:
        st.warning("Game Over. Refresh to play again.")

    st.metric("🕒 Time Left", f"{max(0, time_left)}s")
    st.metric("🎯 Moves Left", st.session_state.moves_left)
    st.metric("⭐ Score", st.session_state.score)

# ----------------------------
# SAVE HIGHSCORE
# ----------------------------
st.divider()
name = st.text_input("Enter name to save your score:")
if st.button("💾 Save Highscore"):
    if name.strip():
        save_highscore(name.strip(), st.session_state.score)
        st.success("Saved!")
    else:
        st.warning("Enter a name!")

# Leaderboard in sidebar
st.sidebar.title("🏆 Leaderboard")
for i, entry in enumerate(load_highscores(), 1):
    st.sidebar.write(f"**{i}. {entry['name']}** — {entry['score']} pts")
