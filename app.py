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
    Requirement 3: Generates target such that with respect to EACH ship,
    it is at an exact integer distance (1 cm, 2 cm, or 3 cm) and within range (<= 3 cm).
    """
    origin_keys = list(origins.keys())
    while True:
        # Pick reference ship and an integer radius in {1, 2, 3} cm
        ref_ship = origins['A']
        r_a = np.random.choice([1.0, 2.0, 3.0])
        theta_deg = np.random.choice(np.arange(10, 370, 10))
        theta_rad = np.radians(theta_deg)
        
        target_pos = ref_ship + np.array([r_a * np.cos(theta_rad), r_a * np.sin(theta_rad)])
        
        # Check distance to all ships
        dist_b = np.linalg.norm(target_pos - origins['B'])
        dist_c = np.linalg.norm(target_pos - origins['C'])
        
        # Check if dist_b and dist_c are integers within floating point tolerance and <= 3.0 cm
        near_int_b = abs(dist_b - round(dist_b)) < 1e-3 and 1.0 <= round(dist_b) <= 3.0
        near_int_c = abs(dist_c - round(dist_c)) < 1e-3 and 1.0 <= round(dist_c) <= 3.0
        
        if near_int_b and near_int_c:
            return target_pos

if 'game_initialized' not in st.session_state:
    st.session_state.grid_min = -10
    st.session_state.grid_max = 10
    
    # Requirement 1: Ships positioned at lattice (integer) coordinates
    # Selected geometry where a shared integer point exists for r in {1, 2, 3}
    st.session_state.origins = {
        'A': np.array([-2.0, 0.0]),
        'B': np.array([2.0, 0.0]),
        'C': np.array([0.0, 2.0])
    }
    
    # Requirement 3: Position target at integer distance from ALL ships
    st.session_state.target = generate_valid_target(st.session_state.origins)
    st.session_state.shots = {'A': None, 'B': None, 'C': None}
    st.session_state.game_status = "IN_PROGRESS"
    st.session_state.grid_density = 10  # Default 10 degrees separation
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

# Requirement 4: Provision to change grid density
angular_separation = st.sidebar.selectbox(
    "⚙️ Polar Grid Angular Separation:",
    options=[10, 20, 30, 60, 90],
    index=0,
    help="Changes the density of polar grid radial poles."
)
st.session_state.grid_density = angular_separation

available_origins = [k for k, v in st.session_state.shots.items() if v is None]

if available_origins and st.session_state.game_status == "IN_PROGRESS":
    chosen_origin = st.sidebar.selectbox("1. Select Ready Ship (Origin):", available_origins)
    
    # Dropdown menu for angle from 10° to 360° in steps of 10°
    angle_options = list(range(10, 370, 10))
    angle_deg = st.sidebar.selectbox("2. Select Rotation Angle θ (degrees):", options=angle_options, index=8)
    angle_rad = np.radians(angle_deg)
    
    # Matrix choice (A vs A^T)
    transform_type = st.sidebar.radio(
        "3. Choose Orthogonal Transformation Matrix:",
        ["Standard Matrix A", "Transpose Matrix Aᵀ"]
    )
    
    # Requirement 2: Vector initial default length is 1 cm (user can adjust up to 3 cm)
    vector_len = st.sidebar.slider("4. Torpedo Vector Length (cm):", 1.0, 3.0, 1.0, step=0.5)

    # Calculate Matrix & Vector Transformation
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
    
    # Requirement 2: Initial vector positioned horizontally (parallel to relative horizontal axis)
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

    # Display live LaTeX textbook matrix multiplication
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
# HIGH-CONTRAST PLOTTING & INTERSECTING POLAR GRIDS
# =========================================================
fig, ax = plt.subplots(figsize=(10, 10), facecolor="#0e1117")
ax.set_facecolor("#0e1117")

ax.set_xlim(-6, 6)
ax.set_ylim(-6, 6)
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

# Requirement 4: Configurable Polar Density angles
step = st.session_state.grid_density
angles_grid = np.radians(np.arange(step, 360 + step, step))
ship_colors = {'A': '#00d2ff', 'B': '#ff9900', 'C': '#00ff66'}

for name, origin in st.session_state.origins.items():
    color = ship_colors[name]
    
    # Requirement 1: Draw Ship Point without explicitly printing coordinates
    ship_point, = ax.plot(origin[0], origin[1], 'o', color=color, markersize=8, zorder=5)
    
    # Requirement 1: Hide explicit text coordinates. Display label and interactive hover annotation
    ax.text(origin[0] + 0.15, origin[1] + 0.15, f"Ship {name}", 
            color=color, fontweight='bold', fontsize=11, zorder=5)
    
    # Annotation box shown on hover (Matplotlib annotation)
    annot = ax.annotate(f"Ship {name}: ({int(origin[0])}, {int(origin[1])})", 
                        xy=(origin[0], origin[1]), xytext=(15, 15),
                        textcoords="offset points", bbox=dict(boxstyle="round,pad=0.3", fc="#161b22", ec=color, lw=1.5),
                        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color=color),
                        color="white", fontsize=10, zorder=10)
    annot.get_bbox_patch().set_alpha(0.85)

    # Requirement 2: Initial unit vector visible at 1 cm length positioned horizontally
    ax.quiver(origin[0], origin[1], 1.0, 0.0, 
              angles='xy', scale_units='xy', scale=1, 
              color=color, alpha=0.35, linestyle='--', width=0.006, zorder=4,
              label=f"Initial v ({name})" if name == 'A' else "")

    # Concentric circles at 1, 2, 3 cm
    for r in [1.0, 2.0, 3.0]:
        circle = plt.Circle((origin[0], origin[1]), r, color=color, fill=False, linestyle='-', alpha=0.4, linewidth=1.2)
        ax.add_patch(circle)
        
    # Radial Poles based on selected angular separation
    for theta in angles_grid:
        dx = 3.0 * np.cos(theta)
        dy = 3.0 * np.sin(theta)
        ax.plot([origin[0], origin[0] + dx], [origin[1], origin[1] + dy], 
                color=color, linestyle=':', linewidth=0.6, alpha=0.35)

# Render Fired Torpedo Trajectories
for name, vec in st.session_state.shots.items():
    if vec is not None:
        start = st.session_state.origins[name]
        ax.quiver(start[0], start[1], vec[0], vec[1], 
                  angles='xy', scale_units='xy', scale=1, 
                  color=ship_colors[name], label=f"Torpedo {name}", width=0.01, zorder=5)

ax.set_title(f"Naval Coordinates Grid (Polar Separation: {step}°)", color="white", fontsize=14, pad=12)
for spine in ax.spines.values():
    spine.set_color('#444444')
ax.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', labelcolor='white')

st.pyplot(fig)
