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

def query_system(dataset_strs, command, progress=gr.Progress()):
    if not dataset_strs or not command:
        return [], "⚠️ Please select a dataset and enter a command."

    try:
        progress(0.1, desc="Initializing Query...")
        
        # data_strs is a list of "{id}: name..."
        print(f"DEBUG: query_system dataset_strs: {dataset_strs}")
        
        valid_ids = []
        for s in dataset_strs:
            if isinstance(s, str) and ':' in s:
                try:
                    valid_ids.append(int(s.split(':')[0]))
                except:
                    pass
        
        if not valid_ids:
             return [], "⚠️ No valid datasets selected."
             
        dataset_ids = valid_ids
        # dataset_ids = [int(s.split(':')[0]) for s in dataset_strs if s]
        payload = {"dataset_ids": dataset_ids, "prompt": command}
        
        progress(0.3, desc=f"Analyzing {len(dataset_ids)} datasets with AI...")

        # NOTE: This single call waits for ALL datasets. 
        # For better UX with many datasets, we would parallelize or stream, 
        # but for now we just show we are working.
        response = requests.post(f"{API_BASE_URL}/agent/analyze", json=payload)
        response.raise_for_status()
        
        progress(0.8, desc="Processing Results...")
        data = response.json()
        
        # data is {"results": [...]}
        results = data.get("results", [])
        
        # Process results for rendering (parse JSON configs and results)
        processed_results = []
        for res in results:
            chart_config = res.get("chart_config", {})
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
            
            # Parse table
            raw_result = res.get("query_result", "[]")
            try:
                result_list = json.loads(raw_result)
                result_df = pd.DataFrame(result_list)
            except:
                result_df = pd.DataFrame({"Error": ["Failed to parse result table"]})

            processed_results.append({
                "dataset_id": res.get("dataset_id"),
                "fig": fig,
                "df": result_df,
                "explanation": res.get("explanation"),
                "sql_query": res.get("sql_query")
            })
            
        progress(1.0, desc="Done!")
        return processed_results, "✅ Query Completed Successfully"

    except Exception as e:
        print(f"Error querying system: {e}")
        gr.Warning(f"Query failed: {str(e)}")
        return [], f"❌ Error: {str(e)}"

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
.status-msg { 
    min-height: 50px !important; 
    height: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: rgba(0,0,0,0.2) !important;
    border-radius: 6px !important;
    margin-top: 5px !important;
}
"""

# --- APP LAYOUT ---
with gr.Blocks(title="NEXUS v7", css=nexus_css) as demo:
    # State to hold the full list of results
    results_state = gr.State(value=[])
    
    # States for Data Center (kept for compatibility if needed, though mostly local variables)
    # (No global state needed for Data Center as it was direct wiring, but let's check)

    with gr.Column(elem_id="app-wrapper"):
        
        # HEADER
        with gr.Group(elem_id="top-header"):
            with gr.Row():
                gr.HTML('<div class="brand-title" style="color:green">◥꧁དℭ℟Åℤ¥༒₭ÏḼḼ℥℟ཌ꧂◤</div>')

        # TABS
        with gr.Tabs():
            
            # --- TAB 1: DASHBOARD ---
            with gr.TabItem("📊 INTELLIGENCE DASHBOARD"):
                        # TERMINAL
                with gr.Group(elem_id="terminal-area"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            # Multi-select enabled
                            dataset_selector = gr.Dropdown(choices=get_datasets(), label="ACTIVE DATASETS", container=True, multiselect=True)
                        with gr.Column(scale=4):
                            cmd_input = gr.Textbox(show_label=False, placeholder="Enter natural language query (e.g., 'Show trend of sales over time')...", container=False, autofocus=True, lines=1)
                            status_msg = gr.Markdown("", elem_classes="status-msg")
                        with gr.Column(scale=0, min_width=100):
                            run_btn = gr.Button("RUN", elem_classes="nexus-btn")
                # Dynamic Rendering Area
                @gr.render(inputs=results_state)
                def render_dashboard(results):
                    if not results:
                        gr.Markdown("### Waiting for input...", elem_classes="panel")
                        return
                        
                    for res in results:
                        dataset_id = res.get("dataset_id")
                        fig = res.get("fig")
                        df = res.get("df")
                        explanation = res.get("explanation")
                        sql_query = res.get("sql_query")
                        
                        with gr.Group(elem_classes="panel"):
                            gr.Markdown(f"### 🔮 Analysis Result for Dataset {dataset_id}")
                            
                            # 1. Viz
                            if fig:
                                gr.Plot(value=fig, label=f"Visualization {dataset_id}", container=False)
                            
                            # 2. Results Table
                            if df is not None and not df.empty:
                                with gr.Accordion(f"Query Results ({len(df)} rows)", open=True): 
                                    gr.Dataframe(value=df, interactive=False, wrap=True)
                            
                            # 3. Insights & SQL
                            with gr.Row():
                                with gr.Column(scale=1):
                                    gr.Markdown("#### 🧠 INSIGHTS")
                                    gr.HTML("<div style = 'padding:10px'>" + explanation + "</div>")
                                with gr.Column(scale=1):
                                    gr.Markdown("#### ⚙️ SQL TRACE")
                                    gr.Code(value=sql_query or "-- No SQL", language="sql")
                                    
                            gr.Markdown("---") # Separator

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



    # --- WIRING ---
    
    # 1. Dashboard Logic
    # Update results_state, which triggers the render function automatically
    cmd_input.submit(query_system, inputs=[dataset_selector, cmd_input], outputs=[results_state, status_msg], show_progress="full")
    run_btn.click(query_system, inputs=[dataset_selector, cmd_input], outputs=[results_state, status_msg], show_progress="full")
    
    # 2. Data Center Logic
    upload_btn.click(upload_file, inputs=file_in, outputs=[upload_msg, dataset_selector])
    
    # Update preview when dataset changes or refresh clicked
    # NOTE: dataset_selector is now a list. get_preview expects strings.
    # We should probably only preview the *first* selected dataset or disable preview for multi.
    # Let's handle the list in get_preview to avoid errors, or just take the first one.
    
    def get_preview_wrapper(dataset_strs):
        try:
            print(f"DEBUG: get_preview_wrapper input: {dataset_strs} (type: {type(dataset_strs)})")
            if not dataset_strs: return pd.DataFrame()
            if isinstance(dataset_strs, list) and len(dataset_strs) > 0:
                # Ensure element is string
                first = dataset_strs[0]
                if isinstance(first, str):
                    return get_preview(first)
                else:
                    return pd.DataFrame({"Error": [f"Invalid dataset format: {type(first)}"]})
            elif isinstance(dataset_strs, str):
                return get_preview(dataset_strs)
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"DEBUG: Preview Error: {e}")
            return pd.DataFrame({"Error": [f"Preview failed: {str(e)}"]})

    dataset_selector.change(get_preview_wrapper, inputs=dataset_selector, outputs=preview_table)
    refresh_preview_btn.click(get_preview_wrapper, inputs=dataset_selector, outputs=preview_table)

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7866)
