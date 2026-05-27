from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "hammer-2-processed.sqlite")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    # This magic line makes sure we get dictionaries back instead of weird tuples
    conn.row_factory = sqlite3.Row 
    return conn

@app.get("/api/search")
def search_food(query: str):
    conn = get_db()
    
    # 1. The SQL Command
    # SELECT * means "get all columns"
    # WHERE name LIKE ? is how we search for text
    sql_command = """
       SELECT 
            product.id, 
            product.vendor, 
            product.product_name AS name, 
            product.detail_url AS img, 
            raw.current_price AS price,
            raw.price_per_unit,
            MAX(raw.nowtime) as last_updated
        FROM product
        JOIN raw ON product.id = raw.product_id
        WHERE product.product_name LIKE ?
        GROUP BY product.id 

        ORDER BY 
        
        CASE 
            WHEN raw.current_price IS NULL OR raw.current_price = '' OR raw.current_price = 'N/A' OR raw.current_price = 0 THEN 1
            ELSE 0
        END ASC,
        
        
        CAST(raw.current_price AS REAL) ASC
        
        LIMIT 30
    """
    
    # 2. The Wildcards
    # The % symbols mean "anything can come before or after"
    # So if query is "milk", it searches for "%milk%" and will find "2% Milk 1L"
    search_term = f"%{query}%"
    
    # 3. Execute the search
    # We pass the search_term in a tuple (search_term,) for security against hackers
    cursor = conn.execute(sql_command, (search_term,))
    results = cursor.fetchall()
    
    conn.close()
    
    # 4. Convert the results into a clean list of dictionaries for React
    return [dict(row) for row in results]
