import streamlit as st
import random

st.set_page_config(page_title="Treasure Hunt", layout="wide")

# ---------------------------------------------------
# ✅ SESSION STATE INITIALIZATION (must be first)
# ---------------------------------------------------
if "initialized" not in st.session_state:

    st.session_state.grid_size = 10
    st.session_state.player = [5, 5]
    st.session_state.treasure = [random.randint(0, 9), random.randint(0, 9)]

    st.session_state.score = 0
    st.session_state.lives = 3

    # moves allowed = Manhattan distance + 5
    displacement = abs(st.session_state.player[0] - st.session_state.treasure[0]) + abs(
        st.session_state.player[1] - st.session_state.treasure[1]
    )

    st.session_state.moves = 0
    st.session_state.max_moves = displacement + 5

    st.session_state.initialized = True


# ---------------------------------------------------
# ✅ GAME RESET (restart button calls this)
# ---------------------------------------------------
def restart_game():
    st.session_state.player = [5, 5]
    st.session_state.treasure = [random.randint(0, 9), random.randint(0, 9)]

    displacement = abs(st.session_state.player[0] - st.session_state.treasure[0]) + abs(
        st.session_state.player[1] - st.session_state.treasure[1]
    )

    st.session_state.moves = 0
    st.session_state.max_moves = displacement + 5


# ---------------------------------------------------
# ✅ MOVEMENT LOGIC
# ---------------------------------------------------
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

    # ✅ Check WIN
    if st.session_state.player == st.session_state.treasure:
        st.session_state.score += 100
        st.success("💎 TREASURE FOUND! +100 points")
        restart_game()

    # ✅ Check OUT OF MOVES
    if st.session_state.moves >= st.session_state.max_moves:
        st.session_state.lives -= 1
        st.error("❌ OUT OF MOVES! Lost 1 ❤️")

        if st.session_state.lives == 0:
            st.warning("💀 GAME OVER! Restarting game...")
            st.session_state.score = 0
            st.session_state.lives = 3

        restart_game()


# ---------------------------------------------------
# ✅ SIDEBAR UI
# ---------------------------------------------------
with st.sidebar:
    st.header("⚙️ Controls")

    st.write(f"🏆 Score: **{st.session_state.score}**")
    st.write(f"❤️ Lives: **{st.session_state.lives}**")
    st.write(f"🚶 Moves: **{st.session_state.moves}/{st.session_state.max_moves}**")

    st.subheader("Movement")

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
    st.write(
        """
        🧛‍♂️ = You  
        💎 = Hidden treasure  

        ✅ Reach the treasure within allotted moves  
        ❌ Running out of moves loses 1 ❤️  
        💀 At 0 ❤️, game restarts  
        """
    )


# ---------------------------------------------------
# ✅ GAME GRID DISPLAY
# ---------------------------------------------------
st.title("Treasure Hunt 🧛")

for r in range(st.session_state.grid_size):
    cols = st.columns(st.session_state.grid_size)
    for c in range(st.session_state.grid_size):
        with cols[c]:
            if [r, c] == st.session_state.player:
                st.markdown("<h2 style='text-align:center'>🧛‍♂️</h2>", unsafe_allow_html=True)
            else:
                st.markdown("<h2 style='text-align:center;color:#444'>■</h2>", unsafe_allow_html=True)
