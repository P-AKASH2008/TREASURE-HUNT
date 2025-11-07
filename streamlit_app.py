import streamlit as st
import json
import random
from pathlib import Path
from datetime import datetime

# -------------------------------
# Paths
BASE_DIR = Path(__file__).parent
SPRITES_DIR = BASE_DIR / "sprites"
SOUNDS_DIR = BASE_DIR / "sounds"
HIGHSCORES_FILE = BASE_DIR / "highscores.json"

# -------------------------------
# Load highscores
if HIGHSCORES_FILE.exists():
    with open(HIGHSCORES_FILE, "r") as f:
        highscores = json.load(f)
else:
    highscores = []

# -------------------------------
# Settings
GRID_SIZE = 6
TREASURE_COUNT = 3
COIN_COUNT = 2
HEART_COUNT = 1
TRAP_COUNT = 3
MAX_LIVES = 3

SPRITES = {
    "player": str(SPRITES_DIR / "player.png"),
    "treasure": str(SPRITES_DIR / "treasure.gif"),
    "coin": str(SPRITES_DIR / "coin.gif"),
    "heart": str(SPRITES_DIR / "heart.gif"),
    "trap": str(SPRITES_DIR / "trap.png"),
    "fog": str(SPRITES_DIR / "fog.gif")
}

# -------------------------------
# Initialize session state
if "player_pos" not in st.session_state:
    st.session_state.player_pos = [0, 0]
if "score" not in st.session_state:
    st.session_state.score = 0
if "level" not in st.session_state:
    st.session_state.level = 1
if "lives" not in st.session_state:
    st.session_state.lives = MAX_LIVES
if "sound_on" not in st.session_state:
    st.session_state.sound_on = True
if "grid_objects" not in st.session_state:
    objects = []
    def place(count, type_name):
        for _ in range(count):
            while True:
                pos = [random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)]
                if pos != [0,0] and pos not in [obj['pos'] for obj in objects]:
                    objects.append({"type": type_name, "pos": pos})
                    break
    place(TREASURE_COUNT, "treasure")
    place(COIN_COUNT, "coin")
    place(HEART_COUNT, "heart")
    place(TRAP_COUNT, "trap")
    st.session_state.grid_objects = objects
if "revealed" not in st.session_state:
    st.session_state.revealed = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
st.session_state.revealed[0][0] = True
if "move" not in st.session_state:
    st.session_state.move = None

# -------------------------------
# Sidebar
st.sidebar.title("Leaderboard (Top 10)")
for idx, entry in enumerate(sorted(highscores, key=lambda x: x["score"], reverse=True)[:10]):
    st.sidebar.write(f"{idx+1}. {entry['name']} | Score: {entry['score']} | Lv: {entry['level']} | Treasures: {entry['treasures_collected']} | {entry['date']}")
if st.sidebar.button("Toggle Sound"):
    st.session_state.sound_on = not st.session_state.sound_on
    st.sidebar.success("Sound ON" if st.session_state.sound_on else "Sound OFF")

# -------------------------------
# Helper: Play sound
def play_sound(filename):
    if st.session_state.sound_on:
        file_path = SOUNDS_DIR / filename
        if file_path.exists():
            with open(file_path, "rb") as f:
                st.audio(f.read(), format="audio/mp3")

# -------------------------------
# Handle clicks
def handle_click(x, y):
    px, py = st.session_state.player_pos
    if abs(px - x) + abs(py - y) == 1:  # allow move to adjacent tiles only
        st.session_state.player_pos = [x, y]
        st.session_state.revealed[x][y] = True
        for obj in st.session_state.grid_objects[:]:
            if obj['pos'] == [x, y]:
                if obj['type'] == "treasure":
                    st.session_state.score += 10
                    play_sound("treasure.mp3")
                    st.success("Treasure +10!")
                elif obj['type'] == "coin":
                    st.session_state.score += 5
                    play_sound("treasure.mp3")
                    st.info("Coin +5!")
                elif obj['type'] == "heart":
                    st.session_state.score += 15
                    st.session_state.lives = min(MAX_LIVES, st.session_state.lives + 1)
                    play_sound("treasure.mp3")
                    st.success("Heart +15! Life +1")
                elif obj['type'] == "trap":
                    st.session_state.score -= 5
                    st.session_state.lives -= 1
                    play_sound("trap.mp3")
                    st.error("Trap -5! Lost 1 life")
                st.session_state.grid_objects.remove(obj)
        # Level up if all treasures collected
        treasures_left = [o for o in st.session_state.grid_objects if o['type'] == "treasure"]
        if not treasures_left:
            st.session_state.level += 1
            st.session_state.score += 20  # level bonus
            play_sound("levelup.mp3")
            st.balloons()
            st.info(f"Level Up! Level {st.session_state.level}")
            # regenerate objects
            objects = []
            def place(count, type_name):
                for _ in range(count + st.session_state.level//2):
                    while True:
                        pos = [random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)]
                        if pos != st.session_state.player_pos and pos not in [obj['pos'] for obj in objects]:
                            objects.append({"type": type_name, "pos": pos})
                            break
            place(TREASURE_COUNT, "treasure")
            place(COIN_COUNT, "coin")
            place(HEART_COUNT, "heart")
            place(TRAP_COUNT, "trap")
            st.session_state.grid_objects = objects

# -------------------------------
# Display grid
st.markdown(f"### Level {st.session_state.level} | Score: {st.session_state.score} | Lives: {st.session_state.lives}")
grid_html = "<table style='border-collapse: collapse;'>"
for i in range(GRID_SIZE):
    grid_html += "<tr>"
    for j in range(GRID_SIZE):
        cell_style = "width:60px;height:60px;text-align:center;border:1px solid #999;"
        if [i,j] == st.session_state.player_pos:
            content = f"<img src='{SPRITES['player']}' width='50'/>"
        elif not st.session_state.revealed[i][j]:
            content = f"<img src='{SPRITES['fog']}' width='50'/>"
        else:
            obj_here = next((o for o in st.session_state.grid_objects if o['pos']==[i,j]), None)
            if obj_here:
                content = f"<img src='{SPRITES[obj_here['type']]}' width='50'/>"
            else:
                content = ""
        # Wrap cell in a clickable button form
        grid_html += f"<td style='{cell_style}'><form method='post'><button name='click' value='{i},{j}' style='width:100%;height:100%;background:none;border:none;padding:0;margin:0'>{content}</button></form></td>"
    grid_html += "</tr>"
grid_html += "</table>"

st.components.v1.html(grid_html, height=GRID_SIZE*65)

# -------------------------------
# Game Over check
if st.session_state.lives <= 0:
    st.error("Game Over! You lost all your lives.")
    with st.form("save_score_form"):
        name = st.text_input("Enter your name to save score:")
        submitted = st.form_submit_button("Save Score")
        if submitted and name:
            highscores.append({
                "name": name,
                "score": st.session_state.score,
                "level": st.session_state.level,
                "treasures_collected": sum(1 for o in st.session_state.grid_objects if o['type'] in ["treasure","coin","heart"]),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            highscores.sort(key=lambda x: x["score"], reverse=True)
            highscores[:] = highscores[:10]  # keep top 10
            with open(HIGHSCORES_FILE, "w") as f:
                json.dump(highscores, f, indent=4)
            st.success("Score saved! Refresh page to play again.")




