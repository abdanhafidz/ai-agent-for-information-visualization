from typing import TypedDict, Annotated, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.repository.dataset_repository import DatasetRepository
from sqlalchemy import text
import json

class AgentState(TypedDict):
    question: str
    dataset_id: int
    table_name: str
    columns_metadata: str
    sql_query: str
    query_result: str
    chart_config: Dict[str, Any]
    explanation: str

import re
import ast

class AgentService:
    def __init__(self, repository: DatasetRepository, llm=None):
        self.repository = repository
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0)
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("get_metadata", self.get_metadata)
        workflow.add_node("generate_sql", self.generate_sql)
        workflow.add_node("execute_sql", self.execute_sql)
        workflow.add_node("generate_visualization", self.generate_visualization)
        workflow.set_entry_point("get_metadata")
        workflow.add_edge("get_metadata", "generate_sql")
        workflow.add_edge("generate_sql", "execute_sql")
        workflow.add_edge("execute_sql", "generate_visualization")
        workflow.add_edge("generate_visualization", END)
        return workflow.compile()

    def get_metadata(self, state: AgentState):
        dataset = self.repository.read_by_id(state["dataset_id"])
        return {"table_name": dataset.table_name, "columns_metadata": dataset.columns_metadata}

    def generate_sql(self, state: AgentState):
        prompt = f"""
        You are a SQL expert. Given table '{state['table_name']}' with columns {state['columns_metadata']},
        generate a SQL query to answer: "{state['question']}".
        Return ONLY the SQL query.
        """
        response = self.llm.invoke([HumanMessage(content=prompt)])
        sql = response.content.strip().replace("```sql", "").replace("```", "")
        print(f"DEBUG: SQL: {sql}")
        return {"sql_query": sql}

    def execute_sql(self, state: AgentState):
        try:
            with self.repository.session_factory() as session:
                cursor = session.execute(text(state["sql_query"]))
                keys = cursor.keys()
                result = cursor.fetchall()
                if not result: return {"query_result": "[]"}
                data = [dict(zip(keys, row)) for row in result]
                return {"query_result": json.dumps(data, default=str)}
        except Exception as e:
            return {"query_result": f"Error: {str(e)}"}

    def generate_visualization(self, state: AgentState):
        prompt = f"""
        You are a Data Visualization Expert using Plotly.
        Data: {state['query_result']}
        Question: "{state['question']}"
        
        Generate a SINGLE Plotly Visualization configuration.
        
        Rules:
        1. Theme: Dark/Neon ("#22c55e" primary). Transparent Background.
        2. Limit data points to 50 max (aggregate if needed).
        3. Return JSON ONLY: {{ "data": [trace1, ...], "layout": {{ ... }} }}
        
        Summary: Provide a short text summary of the insight.
        
        Structure:
        {{
            "chart_config": {{ "data": [...], "layout": {{...}} }},
            "explanation": "..."
        }}
        """
        response = self.llm.invoke([HumanMessage(content=prompt)])
        try:
            content = response.content.strip()
            # Robust Parsing
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1: content = content[start : end + 1]
            content = re.sub(r",\s*([\]}])", r"\1", content) # Remove trailing commas
            
            try:
                result = json.loads(content)
            except:
                result = ast.literal_eval(content.replace("true","True").replace("false","False").replace("null","None"))
                
            return {
                "chart_config": result.get("chart_config", {}),
                "explanation": result.get("explanation", "")
            }
        except Exception as e:
            print(f"Error parsing viz: {e}")
            return {"chart_config": {}, "explanation": "Failed to generate visualization."}

    def analyze(self, question: str, dataset_id: int):
        return self.workflow.invoke({"question": question, "dataset_id": dataset_id})
