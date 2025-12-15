import gradio as gr
import requests
import json
import plotly.graph_objects as go
import pandas as pd
from io import StringIO

# --- API Configuration ---
API_BASE_URL = "http://localhost:8000/api/v1"

# --- Logic Functions ---
def get_datasets():
    try:
        response = requests.get(f"{API_BASE_URL}/datasets/?page_size=100")
        response.raise_for_status()
        data = response.json()
        return [f"{d['id']}: {d['filename']} ({d['table_name']})" for d in data.get("founds", [])]
    except Exception as e:
        return []

def upload_file(file_obj):
    if not file_obj:
        return "⚠️ Please select a file", gr.update(choices=get_datasets())
    
    try:
        # File object from Gradio is a temp path string
        filename = file_obj.split('\\')[-1].split('/')[-1]
        files = {'file': (filename, open(file_obj, 'rb'), 'application/octet-stream')}
        
        response = requests.post(f"{API_BASE_URL}/datasets/upload", files=files)
        response.raise_for_status()
        
        return "✅ Upload Successful", gr.update(choices=get_datasets())
    except Exception as e:
        return f"❌ Error: {str(e)}", gr.update(choices=get_datasets())

def get_preview(dataset_str):
    if not dataset_str:
        return pd.DataFrame()
    
    try:
        dataset_id = int(dataset_str.split(':')[0])
        
        # Use the dedicated fast preview endpoint
        response = requests.get(f"{API_BASE_URL}/datasets/{dataset_id}/preview")
        response.raise_for_status()
        data_list = response.json()
        
        if not data_list:
            return pd.DataFrame({"Message": ["Dataset is empty"]})
            
        return pd.DataFrame(data_list)
        
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})

PAGE_SIZE = 10

def update_table_view(search_query, full_df, page_index):
    if full_df is None or full_df.empty:
        return pd.DataFrame(), "Page 0 of 0", 0
        
    # 1. Filter
    if search_query:
        search_query = str(search_query).lower()
        full_df = full_df[full_df.apply(lambda x: x.astype(str).str.lower().str.contains(search_query).any(), axis=1)]
    
    total_rows = len(full_df)
    total_pages = (total_rows + PAGE_SIZE - 1) // PAGE_SIZE if total_rows > 0 else 1
    
    # 2. Validate Page Index
    if page_index < 0: page_index = 0
    if page_index >= total_pages: page_index = total_pages - 1
    
    # 3. Slice
    start_idx = page_index * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    visible_df = full_df.iloc[start_idx:end_idx]
    
    return visible_df, f"Page {page_index + 1} of {total_pages}", page_index

def handle_next(search_query, full_df, page_index):
    return update_table_view(search_query, full_df, page_index + 1)

def handle_prev(search_query, full_df, page_index):
    return update_table_view(search_query, full_df, page_index - 1)

def handle_search(search_query, full_df):
    # Reset to page 0 on new search
    return update_table_view(search_query, full_df, 0)

def query_system(dataset_str, command):
    if not dataset_str or not command:
        return None, pd.DataFrame(), pd.DataFrame(), "DEFAULT: WAITING FOR INPUT", ""
        
    try:
        dataset_id = int(dataset_str.split(':')[0])
        payload = {"dataset_id": dataset_id, "prompt": command}
        
        response = requests.post(f"{API_BASE_URL}/agent/analyze", json=payload)
        response.raise_for_status()
        data = response.json()
        
        chart_config = data.get("chart_config", {})
        explanation = data.get("explanation", "No explanation provided.")
        sql_query = data.get("sql_query", "")
        
        # Parse Result Table
        raw_result = data.get("query_result", "[]")
        print(f"DEBUG: Raw Query Result: {raw_result[:500]}") # Log first 500 chars
        try:
            result_list = json.loads(raw_result)
            result_df = pd.DataFrame(result_list)
        except:
            result_df = pd.DataFrame({"Error": ["Failed to parse result table"]})
        
        fig = None
        if chart_config:
            fig = go.Figure(data=chart_config.get("data"), layout=chart_config.get("layout"))
            fig.update_layout(
                template="plotly_dark", 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#e5e7eb"),
                margin=dict(l=40, r=40, t=50, b=40)
            )

        # Return result_df twice: once for View (sliced), once for State (full)
        # We must apply initial pagination (Page 0)
        visible_df, page_label, page_index = update_table_view("", result_df, 0)
        
        return fig, visible_df, result_df, explanation, sql_query, page_index, page_label

    except Exception as e:
        return None, pd.DataFrame(), pd.DataFrame(), f"ERROR: {str(e)}", "", 0, "Page 0 of 0"

# --- CSS Refresh ---
nexus_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Fira+Code:wght@400;600&display=swap');

:root {
    --bg-dark: #09090b;
    --bg-panel: #18181b;
    --border-color: #27272a;
    --accent: #22c55e;
    --text-main: #e4e4e7;
    --text-dim: #a1a1aa;
}

body { background-color: var(--bg-dark) !important; color: var(--text-main) !important; font-family: 'Inter', sans-serif !important; margin: 0; }
.gradio-container { background: transparent !important; max-width: 100% !important; }

/* Subtle Grid Background instead of scanlines */
body::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background-image: 
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: -1;
}

/* UI Layout */
#app-wrapper { max-width: 1600px; margin: 0 auto; padding: 2rem; display: flex; flex-direction: column; min-height: 95vh; }
#top-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; }
.brand-title { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.5px; }

/* Components */
.panel { background: var(--bg-panel); border: 1px solid var(--border-color); border-radius: 8px; padding: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
.nexus-btn { background: var(--accent) !important; color: black !important; font-weight: 600 !important; border: none !important; border-radius: 6px !important; }
.nexus-btn:hover { opacity: 0.9; }

/* Inputs */
.gradio-dropdown, .gradio-textbox { background: #000 !important; border: 1px solid var(--border-color) !important; }

/* Tabs */
.tabs { border-bottom: 1px solid var(--border-color); margin-bottom: 1rem; }
.tab-nav button { font-weight: 600; font-size: 1rem; }
.tab-nav button.selected { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }

/* Terminal */
#terminal-area { position: sticky; bottom: 20px; background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; margin-top: auto; z-index: 100; }
"""

# --- APP LAYOUT ---
with gr.Blocks(title="NEXUS v7", css=nexus_css) as demo:
    # State to hold the full dataset for filtering
    result_state = gr.State()
    # State for Current Page Index
    page_state = gr.State(value=0)

    with gr.Column(elem_id="app-wrapper"):
        
        # HEADER
        # ... (Header unchanged)
        with gr.Group(elem_id="top-header"):
            with gr.Row():
                gr.HTML('<div class="brand-title">NEXUS <span style="color:#22c55e">///</span> ANALYTICS</div>')
                gr.HTML('<div style="color:var(--text-dim); text-align:right;">SYSTEM READY v7.3</div>')

        # TABS
        with gr.Tabs():
            
            # --- TAB 1: DASHBOARD ---
            with gr.TabItem("📊 INTELLIGENCE DASHBOARD"):
                
                # 1. Main Visualization (Top Middle)
                with gr.Group(elem_classes="panel"):
                    gr.Markdown("### 📈 VISUALIZATION")
                    plot_output = gr.Plot(label="", container=False)
                
                # 2. Result Table with Search (Below Viz)
                with gr.Group(elem_classes="panel"):
                    with gr.Row(variant="compact"):
                        gr.Markdown("### 🔢 QUERY RESULTS")
                        search_box = gr.Textbox(
                            show_label=False, 
                            placeholder="🔍 Search / Filter results...", 
                            container=False, 
                            scale=0, 
                            min_width=300
                        )
                    result_output = gr.Dataframe(interactive=False, wrap=True)
                    
                    # Pagination Controls
                    with gr.Row(equal_height=True):
                        btn_prev = gr.Button("◀ PREV", size="sm")
                        label_page = gr.Textbox(value="Page 0 of 0", show_label=False, container=False, interactive=False, text_align="center")
                        btn_next = gr.Button("NEXT ▶", size="sm")

                # 3. Insights & SQL (Bottom Row)
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes="panel"):
                            gr.Markdown("### 🧠 INSIGHTS")
                            expl_output = gr.Markdown("_Execute a query to see insights..._")
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes="panel"):
                            gr.Markdown("### ⚙️ SQL TRACE")
                            sql_output = gr.Code(language="sql", elem_id="sql-code")

            # --- TAB 2: DATA CENTER ---
            with gr.TabItem("💾 DATA CENTER"):
                with gr.Row():
                    # Left: Management
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes="panel"):
                            gr.Markdown("### 📤 UPLOAD DATASET")
                            file_in = gr.File(file_types=[".csv", ".xlsx"])
                            upload_btn = gr.Button("UPLOAD FILE", elem_classes="nexus-btn")
                            upload_msg = gr.Markdown()
                    
                    # Right: Preview
                    with gr.Column(scale=3):
                        with gr.Group(elem_classes="panel"):
                            with gr.Row():
                                gr.Markdown("### 👁️ DATA PREVIEW (Top 20 Rows)")
                                refresh_preview_btn = gr.Button("REFRESH TABLE", size="sm")
                            preview_table = gr.Dataframe(interactive=False)

        with gr.Group(elem_id="terminal-area"):
            with gr.Row():
                with gr.Column(scale=1):
                    dataset_selector = gr.Dropdown(choices=get_datasets(), label="ACTIVE DATASET", container=True)
                with gr.Column(scale=4):
                    cmd_input = gr.Textbox(show_label=False, placeholder="Enter natural language query (e.g., 'Show trend of sales over time')...", container=False, autofocus=True, lines=1)
                with gr.Column(scale=0, min_width=100):
                    run_btn = gr.Button("RUN", elem_classes="nexus-btn")

    # --- WIRING ---
    
    # 1. Search Logic (Resets to Page 0)
    search_box.change(handle_search, inputs=[search_box, result_state], outputs=[result_output, label_page, page_state])
    
    # 2. Pagination Logic
    btn_prev.click(handle_prev, inputs=[search_box, result_state, page_state], outputs=[result_output, label_page, page_state])
    btn_next.click(handle_next, inputs=[search_box, result_state, page_state], outputs=[result_output, label_page, page_state])

    # 3. Dashboard Logic (Returns 7 outputs: Plot, TableView, TableState, Text, SQL, PageState, PageLabel)
    cmd_input.submit(query_system, inputs=[dataset_selector, cmd_input], outputs=[plot_output, result_output, result_state, expl_output, sql_output, page_state, label_page])
    run_btn.click(query_system, inputs=[dataset_selector, cmd_input], outputs=[plot_output, result_output, result_state, expl_output, sql_output, page_state, label_page])
    
    # 4. Data Center Logic
    upload_btn.click(upload_file, inputs=file_in, outputs=[upload_msg, dataset_selector])
    
    # Update preview when dataset changes or refresh clicked
    dataset_selector.change(get_preview, inputs=dataset_selector, outputs=preview_table)
    refresh_preview_btn.click(get_preview, inputs=dataset_selector, outputs=preview_table)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7866)
