# 🎮 Zaverecny Projekt — *Kindergarten-Inspired 2D Game*

## 💡 Concept
This game draws inspiration from the **Kindergarten** series and reimagines it as a **2D pixel-art adventure** built with **Pygame**.  
The world may look cute and innocent, but it hides a **darkly humorous and twisted reality**.

---

## 🕹️ Core Gameplay Elements

### 🕓 1. Daily Loop Structure  
Each in-game day resets like a **time loop**, offering new opportunities based on your actions.  
Players can experiment with different paths to uncover new storylines and endings.

---

### 🌳 2. Branching Storylines & Player Choices  
Your **decisions truly matter** — who you talk to, what you say, and what you do will shape how each day unfolds.  
Different choices can lead to wildly different outcomes.

---

### 🧩 3. Puzzle & Quest System  
Progress through a variety of **mini-quests** and **logic puzzles**.  
You’ll need to collect items, talk to the right characters, and perform actions in the right order to advance.

---

### 🎒 4. Item-Based Progression  
Items are **key to success**. Some can be reused or have hidden purposes that unlock new interactions or secret endings on later days.

---

### 🤝 5. Cooperative Gameplay  
A planned feature is **co-op mode**, allowing two players to experience the chaos together for extra fun and creativity.

---

## ⚙️ Installation & Setup
Firstly be sure that you have python installed in your coding enviroment.

Follow these steps to run the game locally:

### 1️⃣ Clone the repository
```bash
git clone https://github.com/MFrly/zaverecny-projekt.git
cd <your-repo-name>
```
### 2️⃣ Create a virtual environment
```bash
python -m venv venv
```

### 3️⃣ Activate the virtual environment
```bash
venv\Scripts\activate
```

### 4️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

## ⚙️⚙️ Project Progress

The project is currently in an active development phase.
Most of the core singleplayer mechanics are already implemented and working, including player movement, basic interactions, item collection and NPC dialogue system.

## 🎮 Current State

The game world is functional and can be freely explored

Player movement, collisions and camera system are implemented

Item-based progression (key parts) works correctly

NPC dialogue system reacts dynamically to player progress

## 🌐 Multiplayer / Co-op Progress

One of the main goals of the project is to support cooperative gameplay.
After experimenting with classic TCP/UDP communication, the project now uses Socket.IO for network communication.

Current multiplayer state:

Basic server–client architecture is implemented

Player position synchronization works in local testing

Hosting a server for a single player works correctly

Remote player entities are created and updated dynamically

At this stage, the multiplayer system has been successfully tested on one device.
The next planned step is to test the co-op functionality across multiple devices on the same network to verify real two-player synchronization.

## 🔜 Planned Improvements

Full multiplayer testing on multiple computers

Improved synchronization (animations, states, interactions)

Shared item interactions in co-op mode

Additional story branches and endings

Polishing UI and player feedback
