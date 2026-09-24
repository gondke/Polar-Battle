import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from fractions import Fraction

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(page_title="Naval Torpedo Targeting Game", layout="wide")

# Custom CSS for compact layout
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        padding-top: 1rem;
    }
    .stSelectbox, .stRadio, .stSlider {
        margin-bottom: -10px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HELPER FUNCTIONS FOR LATEX FORMATTING
# =========================================================
def fmt_math(val):
    """Format trigonometric values into clean textbook LaTeX strings."""
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
# RANDOM GENERATION LOGIC FOR SHIPS & TARGET
# =========================================================
def generate_random_origins():
    """Generates random lattice (integer) positions for Ships A, B, and C."""
    coords = [
        np.array([-2.0, 0.0]), np.array([2.0, 0.0]), np.array([0.0, 2.0]),
        np.array([-3.0, 1.0]), np.array([1.0, -2.0]), np.array([-1.0, -2.0]),
        np.array([0.0, -2.0]), np.array([3.0, 1.0]), np.array([-2.0, 2.0])
    ]
    shift = np.random.randint(-2, 3, size=2)
    base_idx = np.random.choice(len(coords), size=3, replace=False)
    
    origins = {
        'A': np.array([float(coords[base_idx[0]][0] + shift[0]), float(coords[base_idx[0]][1] + shift[1])]),
        'B': np.array([float(coords[base_idx[1]][0] + shift[0]), float(coords[base_idx[1]][1] + shift[1])]),
        'C': np.array([float(coords[base_idx[2]][0] + shift[0]), float(coords[base_idx[2]][1] + shift[1])])
    }
    return origins

def generate_target_in_range_all(origins):
    """Generates target positioned randomly at an integer distance from ALL THREE ships."""
    attempts = 0
    while attempts < 2000:
        attempts += 1
        ref = origins['A']
        r_a = np.random.choice([1.0, 2.0, 3.0])
        theta_deg = np.random.choice(np.arange(10, 370, 10))
        theta_rad = np.radians(theta_deg)
        
        target_pos = ref + np.array([r_a * np.cos(theta_rad), r_a * np.sin(theta_rad)])
        
        d_b = np.linalg.norm(target_pos - origins['B'])
        d_c = np.linalg.norm(target_pos - origins['C'])
        
        is_int_b = abs(d_b - round(d_b)) < 1e-2 and 1.0 <= round(d_b) <= 3.0
        is_int_c = abs(d_c - round(d_c)) < 1e-2 and 1.0 <= round(d_c) <= 3.0
        
        if is_int_b and is_int_c:
            return target_pos

    return origins['A'] + np.array([2.0, 0.0])

def setup_new_game():
    st.session_state.origins = generate_random_origins()
    st.session_state.target = generate_target_in_range_all(st.session_state.origins)
    st.session_state.shots = {'A': None, 'B': None, 'C': None}
    st.session_state.game_status = "IN_PROGRESS"
    st.session_state.selected_ship = 'A'

if 'game_initialized' not in st.session_state:
    setup_new_game()
    st.session_state.game_initialized = True

# =========================================================
# HEADER & GAME STATUS
# =========================================================
st.title("🎯 2D Vector Rotation Naval Game")

if st.session_state.game_status == "WON":
    st.success("🎉 Direct Hit! You WON the game!")
elif st.session_state.game_status == "LOST":
    st.error("💥 All 3 torpedoes missed the target. Game Over!")

# =========================================================
# COMPACT SIDEBAR INPUT CONTROLS
# =========================================================
st.sidebar.subheader("🕹️ Fire Control Panel")

col_s1, col_s2 = st.sidebar.columns(2)
available_origins = [k for k, v in st.session_state.shots.items() if v is None]

with col_s1:
    if available_origins and st.session_state.game_status == "IN_PROGRESS":
        chosen_origin = st.selectbox("Ship:", available_origins, key="ship_select")
        st.session_state.selected_ship = chosen_origin
    else:
        chosen_origin = st.session_state.selected_ship
        st.write(f"Active: Ship {chosen_origin}")

with col_s2:
    grid_density = st.selectbox("Density:", [10, 20, 30, 60, 90], index=0, help="Grid separation (°)")

col_m1, col_m2 = st.sidebar.columns(2)

with col_m1:
    angle_opts = list(range(10, 370, 10))
    angle_deg = st.selectbox("Angle θ:", angle_opts, index=8)
    angle_rad = np.radians(angle_deg)

with col_m2:
    transform_type = st.radio("Matrix:", ["Matrix A", "Transpose Aᵀ"], horizontal=True)

vector_len = st.sidebar.slider("Vector Length (cm):", 1.0, 3.0, 1.0, step=0.5)

# Calculate Transformation Matrices
cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
base_vector = np.array([vector_len, 0.0])

matrix_names = {'A': r"A_{\theta}", 'B': r"B_{\phi}", 'C': r"C_{\alpha}"}
mat_symbol = matrix_names.get(chosen_origin, "A")

if transform_type == "Matrix A":
    rot_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
else:
    rot_matrix = np.array([[cos_a, sin_a], [-sin_a, cos_a]])
    mat_symbol += r"^{T}"

fired_vector = rot_matrix @ base_vector

# Live LaTeX Transformation
st.sidebar.markdown("---")
st.sidebar.markdown("**🧮 Live Textbook Transformation:**")

m00, m01 = fmt_math(rot_matrix[0,0]), fmt_math(rot_matrix[0,1])
m10, m11 = fmt_math(rot_matrix[1,0]), fmt_math(rot_matrix[1,1])
vx, vy = fmt_math(base_vector[0]), fmt_math(base_vector[1])
rx, ry = fmt_math(fired_vector[0]), fmt_math(fired_vector[1])

latex_eq = rf"""
$$
{mat_symbol} \cdot \mathbf{{v}} = 
\begin{{bmatrix}} {m00} & {m01} \\ {m10} & {m11} \end{{bmatrix}}
\begin{{bmatrix}} {vx} \\ {vy} \end{{bmatrix}}
=
\begin{{bmatrix}} {rx} \\ {ry} \end{{bmatrix}}
$$
"""
st.sidebar.latex(latex_eq)

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("🔥 FIRE", use_container_width=True) and st.session_state.game_status == "IN_PROGRESS":
        st.session_state.shots[chosen_origin] = fired_vector
        
        origin_pos = st.session_state.origins[chosen_origin]
        impact = origin_pos + fired_vector
        dist = np.linalg.norm(impact - st.session_state.target)
        
        if dist <= 0.4:
            st.session_state.game_status = "WON"
        elif all(v is not None for v in st.session_state.shots.values()):
            st.session_state.game_status = "LOST"
            
        st.rerun()

with col_btn2:
    if st.button("🔄 Reset", use_container_width=True):
        setup_new_game()
        st.rerun()

# =========================================================
# HIGH-CONTRAST PLOTTING (COORDINATES COMPLETELY HIDDEN)
# =========================================================
fig, ax = plt.subplots(figsize=(8.5, 8.5), facecolor="#0e1117")
ax.set_facecolor("#0e1117")

ax.set_xlim(-7, 7)
ax.set_ylim(-7, 7)
ax.set_aspect('equal')

# Gridlines
ax.grid(True, which='both', color='#262730', linestyle='--', linewidth=0.8)
ax.axhline(0, color='#444444', linewidth=1.2)
ax.axvline(0, color='#444444', linewidth=1.2)
ax.set_xlabel("X (cm)", color="white")
ax.set_ylabel("Y (cm)", color="white")
ax.tick_params(colors='white')

# Target (Red Star)
target = st.session_state.target
ax.plot(target[0], target[1], marker='*', markersize=22, color='#ff0055', markeredgecolor='white', label="Target", zorder=6)

angles_grid = np.radians(np.arange(grid_density, 360 + grid_density, grid_density))
ship_colors = {'A': '#00d2ff', 'B': '#ff9900', 'C': '#00ff66'}

# Draw Ships and Polar Grids
for name, origin in st.session_state.origins.items():
    color = ship_colors[name]
    is_selected = (name == st.session_state.selected_ship)
    line_alpha = 0.85 if is_selected else 0.12
    circle_alpha = 0.90 if is_selected else 0.15
    
    # Draw Ship Point and Name ONLY (NO COORDINATES TEXT DISPLAYED)
    ax.plot(origin[0], origin[1], 'o', color=color, markersize=9, zorder=5)
    ax.text(origin[0] + 0.15, origin[1] + 0.15, f"Ship {name}", color=color, fontweight='bold', fontsize=11, zorder=5)

    # Initial horizontal vector
    ax.quiver(origin[0], origin[1], 1.0, 0.0, 
              angles='xy', scale_units='xy', scale=1, 
              color=color, alpha=0.4 if is_selected else 0.15, linestyle='--', width=0.006, zorder=4)

    # Concentric circles
    for r in [1.0, 2.0, 3.0]:
        circle = plt.Circle((origin[0], origin[1]), r, color=color, fill=False, 
                            linestyle='-', alpha=circle_alpha, linewidth=1.4 if is_selected else 0.8)
        ax.add_patch(circle)
        
    # Radial lines
    for theta in angles_grid:
        dx = 3.0 * np.cos(theta)
        dy = 3.0 * np.sin(theta)
        ax.plot([origin[0], origin[0] + dx], [origin[1], origin[1] + dy], 
                color=color, linestyle=':', linewidth=0.8 if is_selected else 0.4, alpha=line_alpha)

# Render Fired Torpedo Vectors
for name, vec in st.session_state.shots.items():
    if vec is not None:
        start = st.session_state.origins[name]
        ax.quiver(start[0], start[1], vec[0], vec[1], 
                  angles='xy', scale_units='xy', scale=1, 
                  color=ship_colors[name], label=f"Torpedo {name}", width=0.012, zorder=5)

ax.set_title(f"Naval Grid (Active Focus: Ship {st.session_state.selected_ship})", color="white", fontsize=14, pad=10)
for spine in ax.spines.values():
    spine.set_color('#444444')
ax.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', labelcolor='white')

st.pyplot(fig)
