import streamlit as st
import random

st.set_page_config(page_title="Treasure Hunt", layout="wide")

# -------------------------------------------
# INITIALIZE SESSION STATE
# -------------------------------------------
if "initialized" not in st.session_state:
    st.session_state.grid_size = 10
    st.session_state.player = [5, 5]
    st.session_state.treasure = [random.randint(0, 9), random.randint(0, 9)]
    st.session_state.score = 0
    st.session_state.lives = 3

    # moves allowed = minimum displacement + 5 bonus moves
    st.session_state.moves = 0
    st.session_state.max_moves = abs(st.session_state.player[0] - st.session_state.treasure[0]) + abs(
        st.session_state.player[1] - st.session_state.treasure[1]
    ) + 5

    st.session_state.initialized = True


# -------------------------------------------
# GAME RESET FUNCTION
# -------------------------------------------
def restart_game():
    st.session_state.player = [5, 5]
    st.session_state.treasure = [random.randint(0, 9), random.randint(0, 9)]
    st.session_state.moves = 0
    st.session_state.max_moves = abs(st.session_state.player[0] - st.session_state.treasure[0]) + abs(
        st.session_state.player[1] - st.session_state.treasure[1]
    ) + 5


# -------------------------------------------
# MOVEMENT CALLBACK
# -------------------------------------------
def move(direction):
    r, c = st.session_state.player

    if direction == "up" and r > 0:
        r -= 1
    elif direction == "down" and r < st.session_state.grid_size - 1:
        r += 1
    elif direction == "left" and c > 0:
        c -= 1
    elif direction == "right" and c < st.session_state.grid_size - 1:
        c += 1

    st.session_state.player = [r, c]
    st.session_state.moves += 1

    # Win check
    if st.session_state.player == st.session_state.treasure:
        st.session_state.score += 100
        st.success("💎 TREASURE FOUND! Score +100")
        restart_game()

    # Lose check
    if st.session_state.moves >= st.session_state.max_moves:
        st.session_state.lives -= 1
        st.error("❌ OUT OF MOVES! You lost a life.")

        if st.session_state.lives == 0:
            st.warning("💀 GAME OVER! Score reset.")
            st.session_state.score = 0
            st.session_state.lives = 3

        restart_game()


# -------------------------------------------
# SIDEBAR UI
# -------------------------------------------
with st.sidebar:
    st.header("⚙️ Controls")

    st.write(f"🏆 Score: **{st.session_state.score}**")
    st.write(f"❤️ Lives: **{st.session_state.lives}**")
    st.write(f"🚶 Moves: **{st.session_state.moves}/{st.session_state.max_moves}**")

    st.write("**Movement**")

    st.button("⬆ UP", on_click=move, args=("up",))

    col1, col2 = st.columns(2)
    with col1:
        st.button("⬅ LEFT", on_click=move, args=("left",))
    with col2:
        st.button("➡ RIGHT", on_click=move, args=("right",))

    st.button("⬇ DOWN", on_click=move, args=("down",))

    st.divider()
    st.button("🔄 Restart Game", on_click=restart_game)

    st.divider()
    st.subheader("📌 Instructions")
    st.markdown("""
- Move the **🧛‍♂️ Vampire** to find the **💎 treasure**
- You only have limited moves (shown above)
- Winning gives **+100 score**
- Running out of moves = lose 1 ❤️
- Game over at 0 ❤️
    """)

# -------------------------------------------
# MAIN GAME GRID DISPLAY
# -------------------------------------------
st.title("Treasure Hunt 🧛")

for r in range(st.session_state.grid_size):
    cols = st.columns(st.session_state.grid_size)
    for c in range(st.session_state.grid_size):
        with cols[c]:
            if [r, c] == st.session_state.player:
                st.markdown("<h2 style='text-align:center'>🧛‍♂️</h2>", unsafe_allow_html=True)
            else:
                # Fog blocks (dark squares)
                st.markdown("<h2 style='text-align:center;color:#444'>■</h2>", unsafe_allow_html=True)
