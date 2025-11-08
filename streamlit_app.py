import streamlit as st
import random
import json
import os
import time

# ---------------------------------
# STREAMLIT CONFIG
# ---------------------------------
st.set_page_config(page_title="Treasure Hunt", layout="wide")

# ---------------------------------
# SPRITE PATHS
# ---------------------------------
SPRITE_PATHS = {
    "player": "sprites/player.png",
    "treasure": "sprites/treasure.gif",
    "heart": "sprites/heart.gif",
    "trap": "sprites/trap.png",
    "fog": "sprites/fog.png",
}

HIGHSCORE_FILE = "highscores.json"

# ---------------------------------
# SIDEBAR SETTINGS
# ---------------------------------
st.sidebar.title("⚙️ Settings")

grid_choice = st.sidebar.selectbox(
    "Grid Size",
    ["4×4", "8×8", "16×16"],
    index=1,
)

GRID_SIZE = int(grid_choice.split("×")[0])  # "8×8" -> 8

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

sound_enabled = st.sidebar.toggle("🔊 Sound Effects", value=False)

# difficulty configuration
difficulty_config = {
    "Easy":  {"TREASURES": 5, "TRAPS": 1, "HEARTS": 3, "MOVES": 35, "TIME": 90},
    "Normal":{"TREASURES": 3, "TRAPS": 2, "HEARTS": 2, "MOVES": 25, "TIME": 60},
    "Hard":  {"TREASURES": 2, "TRAPS": 4, "HEARTS": 1, "MOVES": 20, "TIME": 45},
}

config = difficulty_config[difficulty]


# ---------------------------------
# LEADERBOARD FUNCTIONS
# ---------------------------------
def load_highscores():
    if not os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump([], f)
    with open(HIGHSCORE_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return []


def save_highscore(name, score):
    highscores = load_highscores()
    highscores.append({"name": name, "score": score})
    highscores = sorted(highscores, key=lambda x: x["score"], reverse=True)[:10]

    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(highscores, f, indent=2)


# ---------------------------------
# GAME INITIALIZATION
# ---------------------------------
def init_game():
    st.session_state.player_pos = [0, 0]
    st.session_state.grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    st.session_state.revealed = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    st.session_state.revealed[0][0] = True

    st.session_state.score = 0
    st.session_state.level = 1
    st.session_state.moves_left = config["MOVES"]
    st.session_state.start_time = time.time()
    st.session_state.game_over = False

    place_objects()


def place_objects():
    grid = st.session_state.grid

    def random_cell():
        while True:
            r, c = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if grid[r][c] == "" and [r, c] != st.session_state.player_pos:
                return r, c

    for _ in range(config["TREASURES"]):
        r, c = random_cell()
        grid[r][c] = "treasure"

    for _ in range(config["TRAPS"]):
        r, c = random_cell()
        grid[r][c] = "trap"

    for _ in range(config["HEARTS"]):
        r, c = random_cell()
        grid[r][c] = "heart"


# ---------------------------------
# GAMEPLAY
# ---------------------------------
def reveal_cells(r, c):
    """ reveal surrounding cells including current cell """
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                st.session_state.revealed[nr][nc] = True


def move_player(direction):
    """ called when user presses movement button """
    if st.session_state.game_over:
        return

    r, c = st.session_state.player_pos
    if direction == "up" and r > 0:
        r -= 1
    elif direction == "down" and r < GRID_SIZE - 1:
        r += 1
    elif direction == "left" and c > 0:
        c -= 1
    elif direction == "right" and c < GRID_SIZE - 1:
        c += 1

    st.session_state.player_pos = [r, c]
    reveal_cells(r, c)

    st.session_state.moves_left -= 1
    check_cell(r, c)


def check_cell(r, c):
    grid = st.session_state.grid
    cell = grid[r][c]

    if cell == "treasure":
        st.session_state.score += 10
        grid[r][c] = ""
        st.toast("💰 Treasure found!")
    elif cell == "trap":
        st.session_state.score -= 5
        grid[r][c] = ""
        st.toast("💥 Trap triggered!")
    elif cell == "heart":
        st.session_state.score += 3
        grid[r][c] = ""
        st.toast("❤️ Heart found!")

    if st.session_state.moves_left <= 0:
        st.session_state.game_over = True
        st.error("🚨 Out of moves!")


# ---------------------------------
# DRAW GRID
# ---------------------------------
def draw_grid():
    grid = st.session_state.grid
    revealed = st.session_state.revealed
    r, c = st.session_state.player_pos

    for i in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE, gap="small")
        for j in range(GRID_SIZE):
            if [i, j] == [r, c]:
                cols[j].image(SPRITE_PATHS["player"], use_container_width=True)
            elif revealed[i][j]:
                tile = grid[i][j]
                if tile:
                    cols[j].image(SPRITE_PATHS[tile], use_container_width=True)
                else:
                    cols[j].image(SPRITE_PATHS["fog"], use_container_width=True)
            else:
                cols[j].image(SPRITE_PATHS["fog"], use_container_width=True)


# ---------------------------------
# ENSURE GAME EXISTS BEFORE RENDERING
# ---------------------------------
if "grid" not in st.session_state or "start_time" not in st.session_state:
    init_game()


# ---------------------------------
# TIMER
# ---------------------------------
elapsed = int(time.time() - st.session_state.start_time)
time_left = config["TIME"] - elapsed

if time_left <= 0 and not st.session_state.game_over:
    st.session_state.game_over = True
    st.error("⏳ Time’s up!")


# ---------------------------------
# UI LAYOUT
# ---------------------------------
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

st.divider()

# SAVE SCORE
name = st.text_input("Enter name to save score:")
if st.button("💾 Save Highscore"):
    if name.strip():
        save_highscore(name, st.session_state.score)
        st.success("✅ Score saved!")
    else:
        st.warning("Please enter a name.")

# SIDEBAR LEADERBOARD
st.sidebar.subheader("🏆 Leaderboard")
for i, entry in enumerate(load_highscores(), 1):
    st.sidebar.write(f"{i}. **{entry['name']}** — {entry['score']} pts")
