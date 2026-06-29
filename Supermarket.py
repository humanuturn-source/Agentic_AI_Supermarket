# supermarket.py

import os
import psycopg2
import sys
import asyncio  # Imported for async runtime handling
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import BaseTool
from mcp.server.fastmcp import FastMCP

# -------------------------------------------------------------
# 1. DATABASE CONFIGURATION & MANAGEMENT
# -------------------------------------------------------------
class DatabaseManager:
    """Handles connection lifecycles to the Postgres database running in Docker."""
    def __init__(self):
        self.db_config = {
            "dbname": os.getenv("DB_NAME", "postgres"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "myangel"), 
            "host": os.getenv("DB_HOST", "localhost"),             
            "port": os.getenv("DB_PORT", "5432")                 
        }

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            colnames = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall() if cursor.description else []
            
            cursor.close()
            return [dict(zip(colnames, row)) for row in rows]
        except Exception as e:
            return [{"error": f"Database error: {str(e)}"}]
        finally:
            if conn:
                conn.close()


# -------------------------------------------------------------
# 2. CUSTOM AGENT TOOLS
# -------------------------------------------------------------
class ProductQueryInput(BaseModel):
    """Input schema for the Product Search Tool."""
    search_term: str = Field(..., description="The name or partial name of the product to search for.")

class SupermarketInventoryTool(BaseTool):
    name: str = "Supermarket Inventory Search Tool"
    # OPTIMIZATION: Forced guidance to make the model pass a broad keyword (e.g. 'Frozen' instead of 'Frozen Pizza')
    description: str = (
        "Use this tool to search the database. Input a single, broad keyword (like 'Frozen', 'Milk', or 'Bread') "
        "to ensure you capture all varieties of products in that category."
    )
    args_schema: Type[BaseModel] = ProductQueryInput
    db_manager: DatabaseManager = Field(default_factory=DatabaseManager)

    def _run(self, search_term: str) -> str:
        query = "SELECT product_id, name, size, price FROM Products WHERE name ILIKE %s;"
        results = self.db_manager.execute_query(query, (f"%{search_term}%",))
        
        if not results:
            return f"No products found matching '{search_term}'."
        if "error" in results[0]:
            return results[0]["error"]
            
        formatted_output = "Found the following products:\n"
        for item in results:
            formatted_output += f"- ID: {item['product_id']} | Name: {item['name']} | Size: {item['size']} | Price: ${item['price']}\n"
        return formatted_output


# -------------------------------------------------------------
# 3. BASE AGENT FACTORY
# -------------------------------------------------------------
class HelpdeskAgentFactory:
    """Factory to generate specific agents using CrewAI's native LLM class."""
    def __init__(self, model_name: str = "gemma4"):
        self.llm = LLM(
            model=f"ollama/{model_name}", 
            base_url="http://localhost:11434"
        )
        self.db_manager = DatabaseManager()

    def create_inventory_agent(self) -> Agent:
        """Creates the Agent responsible for checking product stats."""
        inventory_tool = SupermarketInventoryTool(db_manager=self.db_manager)
        
        return Agent(
            role="Supermarket Inventory Assistant",
            # OPTIMIZATION: Overriding model laziness/summarization tendencies
            goal="Provide a complete and exhaustive list of ALL matching items from the database without summarizing or leaving anything out.",
            backstory=(
                "You are a precise inventory look-up clerk. When a customer asks for a category "
                "or type of food, you must report EVERY SINGLE product returned by your tool. "
                "Never abbreviate lists, never say 'and more', and never truncate results. "
                "If the tool returns 6 items, you must list all 6 items cleanly."
            ),
            tools=[inventory_tool],
            llm=self.llm,
            verbose=False,  
            memory=False
        )


# -------------------------------------------------------------
# 4. APPLICATION RUNTIME ENVIRONMENT
# -------------------------------------------------------------
class SupermarketHelpdeskApp:
    def __init__(self):
        self.factory = HelpdeskAgentFactory(model_name="gemma4")
        self.inventory_agent = self.factory.create_inventory_agent()

    async def handle_customer_query_async(self, query_text: str) -> str:
        lookup_task = Task(
            # OPTIMIZATION: Explicit task constraints targeting category matching issues
            description=(
                f"Address the customer's request: '{query_text}'. Search the database using the most general keyword possible "
                f"(for example, search 'Frozen' to catch all frozen items). "
                f"You MUST read the entire tool output and copy down every product found."
            ),
            expected_output="An exhaustive, bulleted list containing every single item, size, and price found in the tool output.",
            agent=self.inventory_agent
        )

        helpdesk_crew = Crew(
            agents=[self.inventory_agent],
            tasks=[lookup_task],
            process=Process.sequential,
            verbose=False 
        )

        result = await helpdesk_crew.kickoff_async()
        return str(result)


# -------------------------------------------------------------
# 5. MCP SERVER HOOK & RUNTIME (ASYNC COMPATIBLE)
# -------------------------------------------------------------
mcp_server = FastMCP("Supermarket Helpdesk")
app = SupermarketHelpdeskApp()

@mcp_server.tool()
async def ask_supermarket_agent(customer_query: str) -> str:
    """
    Queries the local multi-agent supermarket helpdesk to check for 
    product availability, sizing, pricing, or locations.
    """
    return await app.handle_customer_query_async(customer_query)

if __name__ == "__main__":
    mcp_server.run(transport="stdio")