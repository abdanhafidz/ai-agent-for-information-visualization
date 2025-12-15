import gradio as gr
import requests
import json
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any

# --- CONFIGURATION ---
API_BASE_URL = "http://localhost:8000/api/v1"
THEME_COLOR = "#22c55e" # Green accent

# --- CSS STYLING ---
# "Plotly Studio" dark theme style
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

:root {
    --bg-dark: #111111;
    --bg-panel: #1e1e1e;
    --border-dim: #333333;
    --accent: #22c55e;
    --text-primary: #e5e7eb;
}

body { background: var(--bg-dark); color: var(--text-primary); font-family: 'Inter', sans-serif; }
.gradio-container { max-width: 100% !important; background: var(--bg-dark); }

/* Panels */
.panel { background: var(--bg-panel); border: 1px solid var(--border-dim); border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 20px; }

/* Buttons */
.primary-btn { background: var(--accent) !important; color: white !important; font-weight: 600; border: none; }
.secondary-btn { background: #333 !important; color: white !important; border: 1px solid #555; }

/* Tabs */
.tabs { background: var(--bg-dark); border-bottom: 1px solid var(--border-dim); }
.tab-nav button.selected { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }

/* Typography */
h1, h2, h3 { color: white; margin-bottom: 0.5rem; }
.label { font-size: 0.8rem; text-transform: uppercase; color: #888; letter-spacing: 0.05em; margin-bottom: 4px; }
.viz-prompt { font-family: 'Fira Code', monospace; background: #222; padding: 10px; border-radius: 4px; color: #eee; border-left: 3px solid var(--accent); }
"""

# --- API HELPER FUNCTIONS ---
def get_datasets() -> List[tuple]:
    """Fetch datasets formatted for Dropdown (label, value)."""
    try:
        resp = requests.get(f"{API_BASE_URL}/datasets/?page_size=100")
        resp.raise_for_status()
        data = resp.json().get("founds", [])
        return [(f"{d['id']}: {d['filename']}", d['id']) for d in data]
    except Exception as e:
        print(f"Error fetching datasets: {e}")
        return []

def get_visualizations(dataset_id: int):
    """Fetch list of visualizations for a dataset."""
    try:
        resp = requests.get(f"{API_BASE_URL}/visualizations/dataset/{dataset_id}")
        if resp.status_code == 200:
            return resp.json()
        return []
    except:
        return []

def get_all_visualizations():
    """Fetch all visualizations for dashboard."""
    try:
        resp = requests.get(f"{API_BASE_URL}/visualizations/")
        resp.raise_for_status()
        return resp.json()
    except:
        return []

def parse_viz_config(viz_data):
    """Convert JSON config to Plotly Figure."""
    if not viz_data or not viz_data.get("chart_config"):
        return None
    try:
        config = viz_data["chart_config"]
        # Ensure data is a list
        data = config.get("data")
        if not isinstance(data, list): data = [data]
        
        fig = go.Figure(data=data, layout=config.get("layout"))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=40, t=40, b=40),
            font=dict(family="Inter, sans-serif")
        )
        return fig
    except Exception as e:
        print(f"Error parsing viz: {e}")
        return None

# --- UI LOGIC ---

# TAB 1: UPLOAD
def handle_upload(file_obj):
    if not file_obj:
        return "⚠️ No file selected.", gr.update(choices=get_datasets())
    try:
        filename = file_obj.name.split('\\')[-1].split('/')[-1]
        files = {'file': (filename, open(file_obj.name, 'rb'), 'application/octet-stream')}
        resp = requests.post(f"{API_BASE_URL}/datasets/upload", files=files)
        resp.raise_for_status()
        return "✅ Upload Successful!", gr.update(choices=get_datasets())
    except Exception as e:
        return f"❌ Error: {e}", gr.update(choices=get_datasets())

# TAB 2: VISUALIZE
def load_dataset_visualizations(dataset_id):
    if not dataset_id:
        return []
    
    viz_list = get_visualizations(dataset_id)
    # Return list of dicts for the state
    return viz_list

def append_history(dataset_id, current_history):
    if not dataset_id:
        return current_history
    new_items = get_visualizations(dataset_id)
    return current_history + new_items

def generate_visualization(dataset_id, prompt, current_history):
    if not dataset_id or not prompt:
        raise gr.Error("Please select a dataset and enter a prompt.")
    
    try:
        payload = {"dataset_id": dataset_id, "prompt": prompt}
        # 1. Analyze via Agent
        resp = requests.post(f"{API_BASE_URL}/agent/analyze", json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        # 2. Extract Data
        chart_config = data.get("chart_config", {})
        explanation = data.get("explanation", "")
        sql_query = data.get("sql_query", "")
        
        # 3. Save to Backend (New Entry)
        viz_payload = {
            "dataset_id": dataset_id,
            "prompt": prompt,
            "chart_config": chart_config,
            "explanation": explanation,
            "sql_query": sql_query
        }
        resp = requests.post(f"{API_BASE_URL}/visualizations/", json=viz_payload)
        try:
            resp.raise_for_status()
            new_viz = resp.json()
        except Exception as e:
            print(f"❌ Error Saving Visualization: {str(e)}")
            print(f"Response Status: {resp.status_code}")
            print(f"Response Text: {resp.text}")
            raise gr.Error(f"Failed to save visualization: {resp.text[:200]}")
        
        # 4. Append to History
        updated_history = current_history + [new_viz]
        return updated_history, "" # Return updated history and clear prompt
        
    except Exception as e:
        raise gr.Error(f"Error generating visualization: {str(e)}")

# TAB 3: DASHBOARD
def refresh_dashboard():
    viz_list = get_all_visualizations()
    plots = []
    
    # We will display up to 6 charts for now
    for viz in viz_list:
        fig = parse_viz_config(viz)
        if fig:
            # Add title annotation
            fig.update_layout(title_text=f"Dataset {viz['dataset_id']}: {viz['prompt'][:30]}...")
            plots.append(fig)
            
    # Pad with Nones if valid plots < expected output count (e.g. 6)
    # We will create a fixed grid of 6 slots
    outputs = plots[:6] + [None] * (6 - len(plots[:6]))
    return outputs

# --- APP LAYOUT ---
with gr.Blocks(title="◥꧁དℭ℟Åℤ¥༒₭ÏḼḼ℥℟ཌ꧂◤", css=custom_css, theme=gr.themes.Base()) as demo:
    
    # Header
    with gr.Row(elem_classes="panel"):
        gr.Markdown("## ◥꧁དℭ℟Åℤ¥༒₭ÏḼḼ℥℟ཌ꧂◤")
    
    with gr.Tabs():
        
        # === TAB 1: DATASET INPUT ===
        with gr.TabItem("📂 Dataset Input"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes="panel"):
                    gr.Markdown("### Upload New Dataset")
                    file_input = gr.File(label="Drop CSV/Excel Here", file_types=[".csv", ".xlsx"])
                    upload_btn = gr.Button("Upload Dataset", elem_classes="primary-btn")
                    upload_status = gr.Markdown()
                
                with gr.Column(scale=2, elem_classes="panel"):
                    gr.Markdown("### Available Datasets")
                    dataset_list = gr.Dataframe(
                        headers=["ID", "Filename"],
                        datatype=["number", "str"],
                        value=[(d[1], d[0]) for d in get_datasets()], 
                        label="Datasets"
                    )
                    refresh_list_btn = gr.Button("Refresh List", size="sm")
                    
                    def refresh_ds_list():
                        ds = get_datasets()
                        return [[d[1], d[0].split(':')[1].strip()] for d in ds]
                    
                    refresh_list_btn.click(refresh_ds_list, outputs=dataset_list)

        # === TAB 2: VISUALIZE ===
        with gr.TabItem("📈 Visualize"):
            # State to hold list of visualizations for current dataset
            viz_history = gr.State(value=[])
            
            # --- TOP: CONFIGURATION ---
            with gr.Group(elem_classes="panel"): 
                with gr.Row():
                    with gr.Column(scale=1):
                        ds_dropdown = gr.Dropdown(choices=get_datasets(), label="Select Dataset", interactive=True)
                        load_history_btn = gr.Button("📂 Load History", size="sm", elem_classes="secondary-btn")
                    with gr.Column(scale=4):
                        prompt_input = gr.Textbox(label="New Visualization Prompt", placeholder="e.g., Show me a bar chart of sales by region...", lines=1)
                    with gr.Column(scale=1):
                        generate_btn = gr.Button("✨ Generate", elem_classes="primary-btn")
            
            # --- BOTTOM: DYNAMIC RENDER ---
            @gr.render(inputs=viz_history)
            def render_visualizations(history):
                if not history:
                    gr.Markdown("_No visualizations generated yet. Select a dataset and enter a prompt._")
                else:
                    # Iterate backwards to show newest first? Or forward? 
                    # Requirement says "Appears below the previous one" (Append), so chronological order.
                    for i, viz in enumerate(history):
                        with gr.Group(elem_classes="panel"):
                            with gr.Row():
                                # LEFT: Prompt & Info
                                with gr.Column(scale=1):
                                    gr.Markdown(f"### Visualization #{i+1}")
                                    gr.Markdown(f"**Prompt:**")
                                    gr.HTML(f"<div class='viz-prompt'>{viz.get('prompt')}</div>")
                                    if viz.get('explanation'):
                                        gr.Markdown(f"**Insight:**\n{viz.get('explanation')}")
                                
                                # RIGHT: Chart
                                with gr.Column(scale=2):
                                    fig = parse_viz_config(viz)
                                    if fig:
                                        gr.Plot(value=fig, label=f"Chart #{i+1}")
                                    else:
                                        gr.Markdown("❌ Error rendering figure")

            # Wiring
            ds_dropdown.focus(lambda: gr.update(choices=get_datasets()), outputs=ds_dropdown)
            
            # Manual History Load
            load_history_btn.click(
                append_history,
                inputs=[ds_dropdown, viz_history],
                outputs=viz_history
            )
            
            # Generate & Append
            generate_btn.click(
                generate_visualization, 
                inputs=[ds_dropdown, prompt_input, viz_history], 
                outputs=[viz_history, prompt_input]
            )

        # === TAB 3: DASHBOARD OVERVIEW ===
        with gr.TabItem("📊 Dashboard"):
            with gr.Row(elem_classes="panel"):
                refresh_dash_btn = gr.Button("🔄 Refresh Dashboard", size="sm")
                delete_all_btn = gr.Button("🗑️ Clear All", size="sm", variant="stop")
            
            # State for dashboard data
            dashboard_data = gr.State(value=[])

            # Dynamic Grid Render
            @gr.render(inputs=dashboard_data)
            def render_dashboard(viz_list):
                if not viz_list:
                    gr.Markdown("_No visualizations found in the database._")
                else:
                    gr.Markdown(f"### Showing {len(viz_list)} Visualizations")
                    # Create 2-column grid
                    # Iterate in chunks of 2
                    for i in range(0, len(viz_list), 2):
                        with gr.Row():
                            # Column 1
                            if i < len(viz_list):
                                viz1 = viz_list[i]
                                with gr.Column(elem_classes="panel"):
                                    gr.Markdown(f"**Dataset {viz1['dataset_id']}**: {viz1['prompt'][:50]}...")
                                    fig1 = parse_viz_config(viz1)
                                    if fig1:
                                        gr.Plot(value=fig1, show_label=False)
                                    else:
                                        gr.Markdown("❌ Error rendering")
                            
                            # Column 2
                            if i + 1 < len(viz_list):
                                viz2 = viz_list[i+1]
                                with gr.Column(elem_classes="panel"):
                                    gr.Markdown(f"**Dataset {viz2['dataset_id']}**: {viz2['prompt'][:50]}...")
                                    fig2 = parse_viz_config(viz2)
                                    if fig2:
                                        gr.Plot(value=fig2, show_label=False)
                                    else:
                                        gr.Markdown("❌ Error rendering")

            # Wiring: Load data into State, then Render triggers automatically
            def load_dash_data():
                return get_all_visualizations()

            def delete_all_dash():
                try:
                    requests.delete(f"{API_BASE_URL}/visualizations/")
                    return load_dash_data()
                except Exception as e:
                    print(f"Error deleting: {e}")
                    return []

            refresh_dash_btn.click(load_dash_data, outputs=dashboard_data)
            delete_all_btn.click(delete_all_dash, outputs=dashboard_data)
            
            # Initial Load
            demo.load(load_dash_data, outputs=dashboard_data)


    # Upload wiring
    upload_btn.click(handle_upload, inputs=file_input, outputs=[upload_status, ds_dropdown])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7866)
