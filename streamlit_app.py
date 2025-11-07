import streamlit as st
import random
import json

# -----------------------------
# File Handling
# -----------------------------
SAVE_FILE = "streamlit_treasure_save.json"
HIGHS_FILE = "streamlit_treasure_highscores.json"

def load_json(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data,f,indent=2)

# -----------------------------
# Classes
# -----------------------------
class Player:
    def __init__(self, name):
        self.name = name
        self.row = 0
        self.col = 0
        self.health = 10
        self.lives = 3
        self.score = 0
        self.inventory = {"coins":0,"hearts":0}
        self.moves = 0

    def pos(self):
        return (self.row, self.col)

    def reset_level(self):
        self.row, self.col = 0,0
        self.health = 10

class GameMap:
    def __init__(self,size=5,level=1,treasures=1):
        self.size=size
        self.level=level
        self.treasures=set()
        self.rocks=set()
        self.traps=set()
        self.powerups={}
        self.generate_map(treasures)

    def random_empty(self):
        while True:
            r=random.randint(0,self.size-1)
            c=random.randint(0,self.size-1)
            pos=(r,c)
            if pos in self.treasures or pos in self.rocks or pos in self.traps or pos in self.powerups or pos==(0,0):
                continue
            return pos

    def generate_map(self, treasures):
        for _ in range(treasures):
            self.treasures.add(self.random_empty())
        for _ in range(max(1,self.size+ (self.level-1)*2)):
            if random.random()<0.7:
                self.rocks.add(self.random_empty())
            else:
                self.traps.add(self.random_empty())
        # Powerups
        for _ in range(2):
            ptype=random.choice(["coin","heart"])
            self.powerups[self.random_empty()] = ptype

    def nearest_treasure(self,pos):
        if not self.treasures:
            return None
        r,c=pos
        return min(self.treasures,key=lambda t:abs(t[0]-r)+abs(t[1]-c))

# -----------------------------
# Streamlit Session State Setup
# -----------------------------
if 'player' not in st.session_state:
    st.session_state['player']=None
if 'gmap' not in st.session_state:
    st.session_state['gmap']=None
if 'level' not in st.session_state:
    st.session_state['level']=1
if 'message' not in st.session_state:
    st.session_state['message']="Welcome to Treasure Hunt!"

# -----------------------------
# Game Functions
# -----------------------------
def start_game(name,size):
    st.session_state['player']=Player(name)
    treasures = 1 if size==3 else 2 if size==5 else 3
    st.session_state['gmap']=GameMap(size,st.session_state['level'],treasures)

def move_player(dr,dc):
    player=st.session_state['player']
    gmap=st.session_state['gmap']
    nr,nc=player.row+dr,player.col+dc
    if nr<0 or nr>=gmap.size or nc<0 or nc>=gmap.size:
        st.session_state['message']="Hit the boundary!"
        return
    player.row, player.col = nr,nc
    player.moves+=1
    pos=(nr,nc)
    # Check events
    if pos in gmap.treasures:
        gmap.treasures.remove(pos)
        player.score+=50
        st.session_state['message']="Treasure found! +50 score 🎉"
    elif pos in gmap.rocks:
        gmap.rocks.remove(pos)
        player.health-=2
        st.session_state['message']="Hit a rock! -2 health"
        if player.health<=0:
            player.lives-=1
            if player.lives>0:
                player.reset_level()
                st.session_state['message']="Lost health! Respawned"
            else:
                st.session_state['message']="Game Over! No lives left"
    elif pos in gmap.traps:
        gmap.traps.remove(pos)
        player.health-=3
        player.row,player.col=0,0
        st.session_state['message']="Trap! -3 health, back to start"
    elif pos in gmap.powerups:
        p=gmap.powerups.pop(pos)
        player.inventory[p]+=1
        player.score+=10
        st.session_state['message']=f"Found {p}! +10 score"
    else:
        st.session_state['message']="Moved safely."

def show_map():
    player=st.session_state['player']
    gmap=st.session_state['gmap']
    size=gmap.size
    fog=2
    grid=""
    for r in range(size):
        for c in range(size):
            dist=abs(r-player.row)+abs(c-player.col)
            if dist>fog:
                grid+="⬛"
            elif (r,c)==player.pos():
                grid+="🟦"
            elif (r,c) in gmap.treasures:
                grid+="🟨"
            elif (r,c) in gmap.rocks:
                grid+="⬜"
            elif (r,c) in gmap.traps:
                grid+="🟥"
            elif (r,c) in gmap.powerups:
                grid+="🟩"
            else:
                grid+="⬛"
        grid+="\n"
    st.text(grid)

def give_hint():
    player=st.session_state['player']
    gmap=st.session_state['gmap']
    nearest=gmap.nearest_treasure(player.pos())
    if not nearest:
        st.session_state['message']="No treasures remaining!"
        return
    pr,pc=player.row,player.col
    tr,tc=nearest
    vert="north" if tr<pr else "south" if tr>pr else ""
    horiz="west" if tc<pc else "east" if tc>pc else ""
    direction=vert+"-"+horiz if vert and horiz else vert or horiz or "here"
    dist=abs(tr-pr)+abs(tc-pc)
    st.session_state['message']=f"Hint: {direction}, Distance: {dist}"

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🎯 Treasure Hunt Game")

# New game or load
if st.session_state['player'] is None:
    name = st.text_input("Enter player name:")
    level_choice = st.radio("Select difficulty/grid size",["Easy 3x3","Medium 5x5","Hard 7x7"])
    size = 3 if level_choice=="Easy 3x3" else 5 if level_choice=="Medium 5x5" else 7
    if st.button("Start Game"):
        start_game(name,size)
        st.experimental_rerun()
else:
    player=st.session_state['player']
    st.write(f"Player: {player.name} | Health: {player.health} | Lives: {player.lives} | Score: {player.score}")
    st.write(f"Inventory: {player.inventory} | Moves: {player.moves}")
    st.write(st.session_state['message'])
    show_map()

    # Movement buttons
    col1,col2,col3=st.columns(3)
    with col1:
        if st.button("⬅️ Left"):
            move_player(0,-1)
            st.experimental_rerun()
    with col2:
        if st.button("⬆️ Up"):
            move_player(-1,0)
            st.experimental_rerun()
    with col3:
        if st.button("➡️ Right"):
            move_player(0,1)
            st.experimental_rerun()
    if st.button("⬇️ Down"):
        move_player(1,0)
        st.experimental_rerun()
    if st.button("Hint"):
        give_hint()
        st.experimental_rerun()

