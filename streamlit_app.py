import streamlit as st
import random
import json
import os

# ----------------------------
# GAME CONFIG
# ----------------------------
GRID_SIZE = 6
PLAYER_EMOJI = "🧍‍♂️"
SPRITE_PATHS = {
    "player": "sprites/player.png",
    "treasure": "sprites/treasure.gif",
    "coin": "sprites/coin.gif",
    "heart": "sprites/heart.gif",
    "rock": "sprites/rock.png",
    "trap": "sprites/trap.png",
    "fog": "sprites/fog.png",
}

HIGHSCORE_FILE = "highscores.json"


# ----------------------------
# LEADERBOARD FUNCTIONS
# ----------------------------
def load_highscores():
    if not os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump([], f)
    with open(HIGHSCORE_FILE, "r") as f:
        return json.load(f)


def save_highscore(name, score):
    highscores = load_highscores()
    highscores.append({"name": name, "score": score})
    highscores = sorted(highscores, key=lambda x: x["score"], reverse=True)[:10]
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(highscores, f, indent=2)


def display_leaderboard():
    st.subheader("🏆 Leaderboard")
    highscores = load_highscores()
    if highscores:
        for i, entry in enumerate(highscores, 1):
            st.write(f"**{i}. {entry['name']}** — {entry['score']} pts")
    else:
        st.info("No highscores yet. Be the first!")


# ----------------------------
# GAME INIT
# ----------------------------
def init_game():
    st.session_state.player_pos = [0, 0]
    st.session_state.score = 0
    st.session_state.level = 1
    st.session_state.grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    place_objects()


def place_objects():
    grid = st.session_state.grid

    def random_empty_cell():
        while True:
            r, c = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if grid[r][c] == "" and [r, c] != st.session_state.player_pos:
                return r, c

    for _ in range(3):
        r, c = random_empty_cell()
        grid[r][c] = "treasure"
    for _ in range(2):
        r, c = random_empty_cell()
        grid[r][c] = "trap"
    for _ in range(2):
        r, c = random_empty_cell()
        grid[r][c] = "heart"


# ----------------------------
# MOVE PLAYER
# ----------------------------
def move_player(direction):
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
        st.toast("💥 Ouch! Trap triggered!")
    elif cell == "heart":
        st.session_state.score += 3
        st.session_state.grid[r][c] = ""
        st.toast("❤️ Health bonus!")
    if st.session_state.score >= 30:
        st.session_state.level += 1
        st.session_state.score = 0
        st.toast("⭐ Level Up!")
        place_objects()


# ----------------------------
# DRAW GRID
# ----------------------------
def draw_grid():
    grid = st.session_state.grid
    player_r, player_c = st.session_state.player_pos

    for r in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE)
        for c in range(GRID_SIZE):
            if [r, c] == [player_r, player_c]:
                cols[c].image(SPRITE_PATHS["player"], use_container_width=True)
            elif grid[r][c] == "treasure":
                cols[c].image(SPRITE_PATHS["treasure"], use_container_width=True)
            elif grid[r][c] == "trap":
                cols[c].image(SPRITE_PATHS["trap"], use_container_width=True)
            elif grid[r][c] == "heart":
                cols[c].image(SPRITE_PATHS["heart"], use_container_width=True)
            else:
                cols[c].image(SPRITE_PATHS["fog"], use_container_width=True)


# ----------------------------
# STREAMLIT UI
# ----------------------------
st.set_page_config(page_title="Treasure Hunt Game", layout="centered")

st.title("🏝️ Treasure Hunt")
st.markdown("Use the buttons to explore and find treasures!")

if "player_pos" not in st.session_state:
    init_game()

draw_grid()

st.write(f"**Score:** {st.session_state.score} | **Level:** {st.session_state.level}")

col1, col2, col3, col4 = st.columns(4)
col1.button("⬆️ Up", on_click=move_player, args=("up",))
col2.button("⬅️ Left", on_click=move_player, args=("left",))
col3.button("➡️ Right", on_click=move_player, args=("right",))
col4.button("⬇️ Down", on_click=move_player, args=("down",))

st.divider()

name = st.text_input("Enter your name to save score:")
if st.button("💾 Save Highscore"):
    if name:
        save_highscore(name, st.session_state.score)
        st.success("Highscore saved!")
    else:
        st.warning("Please enter your name.")

display_leaderboard()





