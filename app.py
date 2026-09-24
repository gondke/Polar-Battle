import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from fractions import Fraction

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(page_title="Naval Torpedo Targeting Game", layout="wide")

# =========================================================
# HELPER FUNCTIONS FOR LATEX FORMATTING
# =========================================================
def fmt_math(val):
    """Format common trigonometric values cleanly into LaTeX expressions."""
    if abs(val) < 1e-5:
        return "0"
    elif abs(val - 1.0) < 1e-5:
        return "1"
    elif abs(val + 1.0) < 1e-5:
        return "-1"
    elif abs(val - 0.5) < 1e-5:
        return r"\frac{1}{2}"
    elif abs(val + 0.5) < 1e-5:
        return r"-\frac{1}{2}"
    elif abs(val - np.sqrt(3)/2) < 1e-5:
        return r"\frac{\sqrt{3}}{2}"
    elif abs(val + np.sqrt(3)/2) < 1e-5:
        return r"-\frac{\sqrt{3}}{2}"
    elif abs(val - np.sqrt(2)/2) < 1e-5:
        return r"\frac{\sqrt{2}}{2}"
    elif abs(val + np.sqrt(2)/2) < 1e-5:
        return r"-\frac{\sqrt{2}}{2}"
    else:
        frac = Fraction(val).limit_denominator(100)
        if frac.denominator == 1:
            return f"{frac.numerator}"
        return rf"\frac{{{frac.numerator}}}{{{frac.denominator}}}"

# =========================================================
# GAME STATE INITIALIZATION
# =========================================================
def generate_valid_target(origins):
    """
    Generates target strictly on at least one polar arc (radius 1, 2, or 3),
    within vector reach (<= 3 units) of AT LEAST two ships.
    """
    origin_keys = list(origins.keys())
    while True:
        # Pick two primary ships that will have range to this target
        primary_ships = np.random.choice(origin_keys, size=2, replace=False)
        ref_ship = origins[primary_ships[0]]
        
        # Requirement 6: Target must sit on a polar arc (radius in {1, 2, 3})
        r = np.random.choice([1.0, 2.0, 3.0])
        theta_deg = np.random.choice(np.arange(10, 370, 10))
        theta_rad = np.radians(theta_deg)
        
        target_pos = ref_ship + np.array([r * np.cos(theta_rad), r * np.sin(theta_rad)])
        
        # Requirement 3: Ensure target is in range (<= 3.0 units) of at least two ships
        distances = [np.linalg.norm(target_pos - origins[k]) for k in origin_keys]
        in_range_count = sum(1 for d in distances if d <= 3.001)
        
        # Ensure target is not placed trivially close (< 0.5) to any ship
        if in_range_count >= 2 and all(d >= 0.5 for d in distances):
            return target_pos

if 'game_initialized' not in st.session_state:
    st.session_state.grid_min = -10
    st.session_state.grid_max = 10
    
    # Requirement 1: Ships positioned at lattice (integer) coordinates
    st.session_state.origins = {
        'A': np.array([-3.0, -2.0]),
        'B': np.array([2.0, 3.0]),
        'C': np.array([-1.0, 3.0])
    }
    
    # Requirement 3 & 6: Position target properly on polar arc
    st.session_state.target = generate_valid_target(st.session_state.origins)
    st.session_state.shots = {'A': None, 'B': None, 'C': None}
    st.session_state.game_status = "IN_PROGRESS"
    st.session_state.game_initialized = True

def reset_game():
    st.session_state.target = generate_valid_target(st.session_state.origins)
    st.session_state.shots = {'A': None, 'B': None, 'C': None}
    st.session_state.game_status = "IN_PROGRESS"

# =========================================================
# UI HEADER & GAME STATUS
# =========================================================
st.title("🎯 2D Vector Rotation Naval Game")
st.write("Understand orthogonal matrix transformations: select a ship, angle, and matrix type to fire at the target star.")

if st.session_state.game_status == "WON":
    st.success("🎉 Direct Hit! You WON the game!")
elif st.session_state.game_status == "LOST":
    st.error("💥 All 3 torpedoes missed or failed to hit the target. Game Over!")

st.button("Reset / New Target", on_click=reset_game)

# =========================================================
# SIDEBAR CONTROLS
# =========================================================
st.sidebar.header("Firing Control System")

# Requirement 6: Select origin first
available_origins = [k for k, v in st.session_state.shots.items() if v is None]

if available_origins and st.session_state.game_status == "IN_PROGRESS":
    chosen_origin = st.sidebar.selectbox("1. Select Ready Ship (Origin):", available_origins)
    
    # Requirement 5: Dropdown menu for angle from 10° to 360° in steps of 10°
    angle_options = list(range(10, 370, 10))
    angle_deg = st.sidebar.selectbox("2. Select Rotation Angle θ (degrees):", options=angle_options, index=8)
    angle_rad = np.radians(angle_deg)
    
    # Matrix choice (A vs A^T)
    transform_type = st.sidebar.radio(
        "3. Choose Orthogonal Transformation Matrix:",
        ["Standard Matrix A", "Transpose Matrix Aᵀ"]
    )
    
    # Requirement 3: Vector magnitude capped at max 3 units
    vector_len = st.sidebar.slider("4. Initial Vector Length (Max 3.0 units):", 0.5, 3.0, 2.0, step=0.5)

    # Calculate Matrix & Vector Transformation
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
    base_vector = np.array([vector_len, 0.0])
    
    if transform_type == "Standard Matrix A":
        # Matrix A = [[cos theta, -sin theta], [sin theta, cos theta]]
        rot_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
        matrix_sym = "A"
    else:
        # Transpose A^T = [[cos theta, sin theta], [-sin theta, cos theta]]
        rot_matrix = np.array([[cos_a, sin_a], [-sin_a, cos_a]])
        matrix_sym = "A^{T}"

    fired_vector = rot_matrix @ base_vector

    # Requirement 4: Display live LaTeX textbook matrix multiplication
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧮 Live Matrix Calculation")
    
    m00, m01 = fmt_math(rot_matrix[0,0]), fmt_math(rot_matrix[0,1])
    m10, m11 = fmt_math(rot_matrix[1,0]), fmt_math(rot_matrix[1,1])
    vx, vy = fmt_math(base_vector[0]), fmt_math(base_vector[1])
    rx, ry = fmt_math(fired_vector[0]), fmt_math(fired_vector[1])

    latex_str = f"""
    $$
    {matrix_sym} \\cdot \\mathbf{{v}} = 
    \\begin{{bmatrix}} {m00} & {m01} \\\\ {m10} & {m11} \\end{{bmatrix}}
    \\begin{{bmatrix}} {vx} \\\\ {vy} \\end{{bmatrix}}
    =
    \\begin{{bmatrix}} {rx} \\\\ {ry} \\end{{bmatrix}}
    $$
    """
    st.sidebar.latex(latex_str)

    if st.sidebar.button("🔥 FIRE TORPEDO"):
        st.session_state.shots[chosen_origin] = fired_vector
        
        # Hit detection (Radius threshold = 0.4 units)
        origin_pos = st.session_state.origins[chosen_origin]
        impact_point = origin_pos + fired_vector
        distance_to_target = np.linalg.norm(impact_point - st.session_state.target)
        
        if distance_to_target <= 0.4:
            st.session_state.game_status = "WON"
        elif all(v is not None for v in st.session_state.shots.values()):
            st.session_state.game_status = "LOST"
            
        st.rerun()

# =========================================================
# HIGH-CONTRAST PLOTTING & ZOOMED INTERSECTING POLAR GRIDS
# =========================================================
fig, ax = plt.subplots(figsize=(10, 10), facecolor="#0e1117")
ax.set_facecolor("#0e1117")

# Requirement 2: High contrast zoomed-in layout
ax.set_xlim(-7, 7)
ax.set_ylim(-7, 7)
ax.set_aspect('equal')

# Cartesian Background Grid
ax.grid(True, which='both', color='#262730', linestyle='--', linewidth=0.8)
ax.axhline(0, color='#555555', linewidth=1.2)
ax.axvline(0, color='#555555', linewidth=1.2)
ax.set_xlabel("X (cm)", color="white")
ax.set_ylabel("Y (cm)", color="white")
ax.tick_params(colors='white')

# Target (Red Star)
target = st.session_state.target
ax.plot(target[0], target[1], marker='*', markersize=20, color='#ff0055', markeredgecolor='white', label="Target", zorder=6)

# Requirement 2 & 5: Expanded Zoomed Intersecting Polar Grids
angles_36 = np.radians(np.arange(10, 370, 10))
ship_colors = {'A': '#00d2ff', 'B': '#ff9900', 'C': '#00ff66'}

for name, origin in st.session_state.origins.items():
    color = ship_colors[name]
    
    # Requirement 1: Lattice Point Ships
    ax.plot(origin[0], origin[1], 'o', color=color, markersize=8, zorder=5)
    ax.text(origin[0] + 0.2, origin[1] + 0.2, f"Ship {name} ({int(origin[0])}, {int(origin[1])})", 
            color=color, fontweight='bold', fontsize=11, zorder=5)
    
    # Concentric circles expanded up to radius 3
    for r in [1.0, 2.0, 3.0]:
        circle = plt.Circle((origin[0], origin[1]), r, color=color, fill=False, linestyle='-', alpha=0.4, linewidth=1.2)
        ax.add_patch(circle)
        
    # 36 Radial Poles separated by 10°
    for theta in angles_36:
        dx = 3.0 * np.cos(theta)
        dy = 3.0 * np.sin(theta)
        ax.plot([origin[0], origin[0] + dx], [origin[1], origin[1] + dy], 
                color=color, linestyle=':', linewidth=0.6, alpha=0.35)

# Render Torpedo Trajectories
for name, vec in st.session_state.shots.items():
    if vec is not None:
        start = st.session_state.origins[name]
        ax.quiver(start[0], start[1], vec[0], vec[1], 
                  angles='xy', scale_units='xy', scale=1, 
                  color=ship_colors[name], label=f"Torpedo {name}", width=0.01, zorder=5)

ax.set_title("Zoomed Intersecting Polar Coordinates Grid", color="white", fontsize=14, pad=12)
for spine in ax.spines.values():
    spine.set_color('#444444')
ax.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', labelcolor='white')

st.pyplot(fig)
