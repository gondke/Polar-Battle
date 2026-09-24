import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Naval Torpedo Targeting Game", layout="centered")

# --- Initialize Game State ---
if 'game_initialized' not in st.state_dict():
    # 1. Fixed grid size (20cm x 20cm equivalent, mapped from -10 to 10 on both axes)
    st.session_state.grid_min = -10
    st.session_state.grid_max = 10
    
    # Origins A, B, C placed at distinct lattice points
    st.session_state.origins = {
        'A': np.array([-5, -4]),
        'B': np.array([4, 5]),
        'C': np.array([-2, 6])
    }
    
    # 3. Target (Red Star) placed at a random point in the grid
    st.session_state.target = np.random.uniform(-8, 8, size=2)
    
    # Track shots fired from each origin (Stores True/False or vector info)
    st.session_state.shots = {'A': None, 'B': None, 'C': None}
    st.session_state.game_status = "IN_PROGRESS"  # "IN_PROGRESS", "WON", "LOST"
    st.session_state.game_initialized = True

def reset_game():
    st.session_state.target = np.random.uniform(-8, 8, size=2)
    st.session_state.shots = {'A': None, 'B': None, 'C': None}
    st.session_state.game_status = "IN_PROGRESS"

# --- Title & Controls ---
st.title("🎯 Naval Torpedo Targeting Game")
st.write("Target the **Red Star** by rotating and firing vectors from ships **A, B, and C**.")

# Display game status
if st.session_state.game_status == "WON":
    st.success("🎉 Direct Hit! You WON the game!")
elif st.session_state.game_status == "LOST":
    st.error("💥 All 3 torpedoes missed or missed the target radius. Game Over!")

st.button("Reset / New Target", on_click=reset_game)

st.sidebar.header("Fire Control System")

# 6. User chooses origin first
available_origins = [k for k, v in st.session_state.shots.items() if v is None]

if available_origins and st.session_state.game_status == "IN_PROGRESS":
    chosen_origin = st.sidebar.selectbox("1. Select Ready Ship (Origin):", available_origins)
    
    # Input angle in degrees
    angle_deg = st.sidebar.slider(f"2. Set Angle (degrees) for Ship {chosen_origin}:", 0, 360, 45, step=5)
    angle_rad = np.radians(angle_deg)
    
    # Matrix selection (Matrix vs Transpose)
    # 2. Rotation matrix and its Transpose (Inverse Rotation)
    transform_type = st.sidebar.radio(
        "3. Choose Transformation Matrix:",
        ["Standard Matrix (Counter-Clockwise)", "Transpose Matrix (Clockwise)"]
    )
    
    # Torpedo reach range (Length of firing vector)
    vector_len = st.sidebar.slider("4. Torpedo Range / Vector Length:", 1.0, 15.0, 5.0, step=0.5)

    if st.sidebar.button("🔥 FIRE TORPEDO"):
        # Base reference vector pointing along positive X-axis
        base_vector = np.array([vector_len, 0.0])
        
        # Build rotation matrix according to selected angle
        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
        rot_matrix = np.array([[cos_a, -sin_a], 
                               [sin_a,  cos_a]])
        
        if transform_type == "Transpose Matrix (Clockwise)":
            rot_matrix = rot_matrix.T  # Transpose of 2D rotation matrix is its inverse
            
        # 4. Multiply matrix by vector to calculate rotated trajectory
        fired_vector = rot_matrix @ base_vector
        st.session_state.shots[chosen_origin] = fired_vector
        
        # Check Hit condition (Hit radius threshold of 0.8 units)
        origin_pos = st.session_state.origins[chosen_origin]
        impact_point = origin_pos + fired_vector
        distance_to_target = np.linalg.norm(impact_point - st.session_state.target)
        
        if distance_to_target <= 0.8:
            st.session_state.game_status = "WON"
        elif all(v is not None for v in st.session_state.shots.values()):
            st.session_state.game_status = "LOST"
            
        st.rerun()

# --- Plotting the Grid & Polar Frames ---
fig, ax = plt.subplots(figsize=(7, 7))

# 1. 20 cm x 20 cm representation grid (-10 to 10 limits)
ax.set_xlim(st.session_state.grid_min, st.session_state.grid_max)
ax.set_ylim(st.session_state.grid_min, st.session_state.grid_max)
ax.set_aspect('equal')
ax.grid(True, which='both', color='lightgrey', linestyle='--', linewidth=0.5)
ax.set_xlabel("X (cm)")
ax.set_ylabel("Y (cm)")

# 3. Draw Target (Red Star)
target = st.session_state.target
ax.plot(target[0], target[1], marker='*', markersize=18, color='red', label="Target", zorder=5)

# 1 & 5. Draw Polar Frames at Origins A, B, C
angles_36 = np.radians(np.arange(0, 360, 10))  # 36 poles separated by 10 degrees

for name, origin in st.session_state.origins.items():
    # Draw Origin point
    ax.plot(origin[0], origin[1], 'bo', markersize=6)
    ax.text(origin[0] + 0.3, origin[1] + 0.3, f"Ship {name}", fontsize=11, fontweight='bold')
    
    # 1. Draw 3 concentric circles differing by unit radii (r = 1, 2, 3)
    for r in [1.0, 2.0, 3.0]:
        circle = plt.Circle((origin[0], origin[1]), r, color='blue', fill=False, linestyle=':', alpha=0.4)
        ax.add_patch(circle)
        
    # 5. Divide polar grid into 36 arcs (10 degrees spacing) radiating up to unit radius 3
    for theta in angles_36:
        dx = 3.0 * np.cos(theta)
        dy = 3.0 * np.sin(theta)
        ax.plot([origin[0], origin[0] + dx], [origin[1], origin[1] + dy], 
                color='cyan', linestyle='-', linewidth=0.3, alpha=0.5)

# 7. Draw Fired Torpedo Vectors
colors = {'A': 'purple', 'B': 'orange', 'C': 'green'}
for name, vec in st.session_state.shots.items():
    if vec is not None:
        start = st.session_state.origins[name]
        ax.quiver(start[0], start[1], vec[0], vec[1], 
                   angles='xy', scale_units='xy', scale=1, 
                   color=colors[name], label=f"Torpedo {name}", width=0.008)

ax.legend(loc='upper right')
st.pyplot(fig)
