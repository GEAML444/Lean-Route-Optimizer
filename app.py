import streamlit as st
import networkx as nx
import pandas as pd
import itertools
import matplotlib.pyplot as plt

instructions_text = """
Route Optimization Tool - Instructions

Overview:
This tool calculates optimal routes between locations using distance or time.

Input Format:
NodeA,NodeB,Value

Example:
Ct,Df,1033.783
Df,D,516.8913

Input Type:
- Distance mode: values are distances
- Time mode: values are travel times
- Speed is used to convert between them

Units:
- Units can be changed for display (feet, meters, minutes)
- Internal calculations use base units

Obstacles / Modifiers:
D,X,block
C1,C2,penalty,200

- block removes a connection
- penalty adds cost

Constraints:
- Start/End nodes fix route endpoints
- Return to start creates a loop
- Skip nodes removes locations

Matrices:
- Input Matrix = direct connections
- Distance Matrix = shortest paths (distance)
- Time Matrix = shortest paths (time)

Notes:
- Constant speed → same optimal path for distance and time
- Do not mix units in input
- >10 nodes may slow performance
"""
st.title("Route Optimization Tool")
with st.expander("Instructions (click to expand)"):

    st.write("### Overview")
    st.write(
        "This tool calculates optimal routes between locations based on your inputs. "
        "It supports distance- or time-based modeling, constraints, and scenario testing."
    )

    st.write("### Step 1: Define Connections (Edges)")
    st.write("Enter connections between nodes using the format:")
    st.code("NodeA,NodeB,Value")

    st.write("Example:")
    st.code("""Ct,Df,1033.783
Df,D,516.8913
D,C1,581.5027""")

    st.write(
        "- Each row defines a direct path between two locations\n"
        "- Values represent either distance or time depending on selected mode\n"
        "- Nodes are created automatically"
    )

    st.write("### Step 2: Choose Input Type")
    st.write(
        "- Distance mode: values are interpreted as physical distance\n"
        "- Time mode: values are interpreted as travel time\n"
        "- The tool converts between distance and time using the selected speed"
    )

    st.write("### Step 3: Units")
    st.write(
        "- You can select preferred units for display (e.g., feet, meters, minutes)\n"
        "- Internally, calculations use base units for consistency\n"
        "- Unit selection does not change routing results, only how they are displayed"
    )

    st.write("### Step 4: Obstacles / Modifiers")
    st.write("Simulate blocked paths or delays:")
    st.code("""D,X,block
C1,C2,penalty,200""")

    st.write(
        "- block → removes a connection entirely\n"
        "- penalty → adds extra cost (distance or time)"
    )

    st.write("### Step 5: Constraints")
    st.write(
        "- Start/End nodes restrict where the route begins and ends\n"
        "- 'Return to start' creates a loop\n"
        "- Skip nodes removes locations from the route"
    )

    st.write("### What the Matrices Show")
    st.write(
        "- Input Matrix: direct connections you entered\n"
        "- Distance Matrix: shortest distances between all nodes\n"
        "- Time Matrix: shortest travel times between all nodes\n"
        "- These are optimized paths, not just direct edges"
    )

    st.write("### Important Notes")
    st.write(
        "- With constant speed, shortest distance and shortest time produce the same route\n"
        "- Do not mix distance and time values in the same input\n"
        "- Large numbers of nodes (>10) may slow performance"
    )

st.download_button(
    label="Download Instructions",
    data=instructions_text,
    file_name="route_tool_instructions.txt",
    mime="text/plain"
)

st.write("Input format: NodeA, NodeB, Distance (in inches)")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

edges = []
input_type = st.radio("Input type", ["Distance (inches)", "Time (seconds)"])

speed = st.number_input("Speed (inches/sec)", value=55.0)
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    for _, row in df.iterrows():
        edges.append((str(row[0]).strip(), str(row[1]).strip(), float(row[2])))

else:
    edge_input = st.text_area("Or enter edges manually", """Ct,Df,1033.783
Df,D,516.8913
D,C1,581.5027
C1,C2,923.0201
C2,X,553.8121
X,F,369.208
F,Ct,479.9705
D,X,415.35""")

    for line in edge_input.strip().split("\n"):
        if not line.strip():
            continue

        parts = [p.strip() for p in line.split(",")]

        if len(parts) != 3:
            st.warning(f"Skipping invalid line: {line}")
            continue

        try:
            a, b = parts[0], parts[1]
            d = float(parts[2])
            edges.append((a, b, d))
        except:
            st.warning(f"Could not parse line: {line}")

unit = st.selectbox("Distance unit", ["inches", "feet", "meters"])
time_unit = st.selectbox("Time unit", ["seconds", "minutes"])

# Build graph
G = nx.Graph()

# Build graph
G = nx.Graph()
for a, b, d in edges:
    G.add_edge(a, b, weight=d)

mod_input = st.text_area("Obstacles / Modifiers", "")

for line in mod_input.strip().split("\n"):
    if not line.strip():
        continue

    parts = [p.strip() for p in line.split(",")]

    if len(parts) >= 3:
        a, b, action = parts[0], parts[1], parts[2]

        if action == "block":
            if G.has_edge(a, b):
                G.remove_edge(a, b)

        elif action == "penalty" and len(parts) == 4:
            penalty = float(parts[3])
            if G.has_edge(a, b):
                G[a][b]["weight"] += penalty
nodes = list(G.nodes())
skip_nodes = st.multiselect("Skip nodes", nodes)

active_nodes = [n for n in nodes if n not in skip_nodes]
if len(nodes) > 10:
    st.warning("More than 10 nodes may be very slow. Consider simplifying.")
start_node = st.selectbox("Start node (optional)", ["None"] + nodes)
end_node = st.selectbox("End node (optional)", ["None"] + nodes)
return_to_start = st.checkbox("Return to start (make it a loop)", value=False)

# Distance matrix
dist = dict(nx.all_pairs_dijkstra_path_length(G, weight="weight"))
df_base = pd.DataFrame(dist).T[nodes]

if input_type == "Distance (inches)":
    df_dist = df_base
    df_time = df_base / speed
else:
    df_time = df_base
    df_dist = df_base * speed

st.subheader("Distance Matrix (inches)")
st.dataframe(df_dist.round(2))
csv_dist = df_dist.to_csv().encode('utf-8')

st.download_button(
    label="Download Distance Matrix (CSV)",
    data=csv_dist,
    file_name="distance_matrix.csv",
    mime="text/csv"
)

st.subheader("Time Matrix (seconds)")
st.dataframe(df_time.round(2))
csv_time = df_time.to_csv().encode('utf-8')

st.download_button(
    label="Download Time Matrix (CSV)",
    data=csv_time,
    file_name="time_matrix.csv",
    mime="text/csv"
)

# TSP (best path)
def path_length(path):
    total = 0

    for i in range(len(path)-1):
        total += dist[path[i]][path[i+1]]

    # If loop required, return to start
    if return_to_start:
        total += dist[path[-1]][path[0]]

    return total

best_path = None
best_len = float("inf")

for perm in itertools.permutations(active_nodes):

    # Enforce start node
    if start_node != "None" and perm[0] != start_node:
        continue

    # Enforce end node
    if end_node != "None" and perm[-1] != end_node:
        continue

    length = path_length(perm)

    if length < best_len:
        best_len = length
        best_path = perm

st.subheader("Best Route (visit all nodes)")
if return_to_start:
    display_path = list(best_path) + [best_path[0]]
else:
    display_path = best_path

st.write(" → ".join(display_path))
st.write(f"Total distance: {best_len:.2f} inches")
if input_type == "Distance (inches)":
    total_time = best_len / speed
else:
    total_time = best_len

st.write(f"Estimated time: {total_time:.2f} seconds")

# Prepare route for export
if return_to_start:
    export_path = list(best_path) + [best_path[0]]
else:
    export_path = list(best_path)

route_df = pd.DataFrame({
    "Step": range(1, len(export_path)+1),
    "Node": export_path
})

csv_route = route_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Route (CSV)",
    data=csv_route,
    file_name="route.csv",
    mime="text/csv"
)
# --- Visualization ---

st.subheader("Route Visualization")

# Create layout (spring layout = decent automatic positioning)
# Fixed layout (approximate physical circuit)
# Use fixed layout if known, otherwise auto-layout
default_pos = {
    "Ct": (0, 1),
    "Df": (1, 1),
    "D": (2, 1),
    "C1": (3, 1),
    "C2": (3, 0),
    "X": (2, 0),
    "F": (1, 0),
}

if all(node in default_pos for node in G.nodes()):
    pos = default_pos
else:
    pos = nx.spring_layout(G, seed=42)
# Handle any unexpected nodes
for node in G.nodes():
    if node not in pos:
        pos[node] = (0, 0)

plt.figure(figsize=(6,4))
plt.clf()
pos = nx.spring_layout(G, seed=42, k=1.5)
# Draw full graph (light gray)
nx.draw(G, pos, with_labels=True, node_color="lightgray",
        edge_color="lightgray", node_size=800, font_size=8)

# Build edge list for best path
path_edges = []
for i in range(len(best_path)-1):
    path_edges.append((best_path[i], best_path[i+1]))

# If returning to start, close the loop
try:
    if return_to_start:
        path_edges.append((best_path[-1], best_path[0]))
except:
    pass

# Highlight best path
nx.draw_networkx_edges(
    G, pos,
    edgelist=path_edges,
    edge_color="red",
    width=3
)

# Highlight nodes in path
nx.draw_networkx_nodes(
    G, pos,
    nodelist=best_path,
    node_color="red",
    node_size=900
)

edge_labels = nx.get_edge_attributes(G, 'weight')
# nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)

st.pyplot(plt)