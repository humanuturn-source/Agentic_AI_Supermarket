
# Setup Guide: Agentic AI Supermarket Helpdesk

This guide provides a comprehensive, step-by-step walkthrough to set up and run the Agentic AI Supermarket Helpdesk application on your local machine. The architecture integrates **Claude Desktop** as the user interface, a local **PostgreSQL** database running inside **Docker**, and a multi-agent system powered by **CrewAI** running a local open-source LLM via **Ollama**.

---

## 🛠️ Architecture Overview
* **User Interface:** Claude Desktop
* **Communication Protocol:** Model Context Protocol (MCP) via `FastMCP`
* **Agent Framework:** CrewAI
* **Local LLM Host:** Ollama (running `gemma2`)
* **Database:** PostgreSQL (deployed via Docker)

---

## 🚀 Step-by-Step Setup Instructions

### Step 1: Install Ollama & Pull the Local LLM

1. Download and install **Ollama** for your operating system from [ollama.com](https://ollama.com).
2. Open your system terminal and start the Ollama application.
3. Download and run the open-source **Gemma 2** model by executing the following command:
   ```bash
   ollama run gemma2
   ```

---

### Step 2: Set Up the PostgreSQL Database via Docker.

We will use Docker to instantly spin up a local PostgreSQL instance and populate it with sample products.

1. Launch the PostgreSQL Container: Run the following command in your terminal: 
  ```
  docker run --name supermarket-postgres \   -e POSTGRES_USER=postgres \   -e POSTGRES_PASSWORD=myangel \   -e POSTGRES_DB=postgres \   -p 5432:5432 \   -d postgres
  ```

2. Initialize Database Schema & Load Data: 
  Connect to your database container using a database administration tool (such as pgAdmin, DBeaver, or a VS Code SQL extension) with these parameters: 
  
  host: localhost, 
  port: 5432, 
  user: <YOUR USERNAME>, 
  password: <YOUR PASSWORD>, 
  database: <DATABASE NAME>. 
  
  Execute the following SQL script to create the table and seed sample records: 
  ```sql
  CREATE TABLE Products (     product_id SERIAL PRIMARY KEY,     name VARCHAR(255) NOT NULL,     size VARCHAR(100),     price NUMERIC(10, 2) );  
  
  INSERT INTO Products (name, size, price) VALUES  ('Whole Milk', '1 gallon', 4.29), ('Oat Milk (Barista Blend)', '32 oz', 4.19), ('Plain Bagels', '6-pack', 3.69), ('Frozen Pizza Pepperoni', '22 oz', 7.99), ('Frozen Peas', '16 oz', 1.89), ('Frozen Mixed Berries', '24 oz', 4.99), ('Frozen Waffles', '10-pack', 2.49), ('Frozen Chicken Nuggets', '32 oz', 6.49), ('Vanilla Ice Cream', '48 oz', 4.49);
  ```

---

### Step 3: Configure the Python Environment and Dependencies

1. Create a Project Directory: 
  ```
  mkdir supermarket-helpdesk 
  cd supermarket-helpdesk
  ```

2. Initialize a Virtual Environment: 
  ```
  python3 -m venv .venv source .venv/bin/activate
  ```

3. Install Required Libraries: 
`Upgrade pip and install CrewAI, the database adapter, Pydantic validation toolkit, and the MCP runtime development libraries: 

  ```
  pip install --upgrade pip 
  pip install crewai langchain-community psycopg2-binary pydantic mcp
  ```
---

### Step 4: Link the Script to Claude Desktop via MCP

To let Claude Desktop use your Python script as an active tool extension, you must modify your local configuration profile.

1. Locate or create your Claude Desktop configuration file. On macOS, this file is located at: ~/Library/Application Support/Claude/claude_desktop_config.json

2. Open the file in a text editor and add the supermarket-helpdesk configuration block. Make sure to supply absolute paths to both your virtual environment python executable and your script location:

```json
    {
      "mcpServers": {
        "supermarket-helpdesk": {
          "command": "/Users/YOUR_MAC_USERNAME/supermarket-helpdesk/.venv/bin/python",
          "args": [
            "/Users/YOUR_MAC_USERNAME/supermarket-helpdesk/supermarket.py"
          ]
        }
      }
    }
```

(Remember to replace YOUR_MAC_USERNAME with your actual Mac user account shortname).

----

🚀 Launch and Test the System

1. Restart Claude Desktop: Fully quit out of Claude Desktop (Cmd + Q) and reopen it to parse the updated settings.

2. Verify Integration Connection: Look for a small plug icon 🔌 in the Claude Desktop chat interface input bar to verify that the server successfully mounted.

3. Run Validation Prompts: Try chatting with your local database agent: • “Do you have bagels?” • “What kinds of frozen food items do you have available right now?”

---
