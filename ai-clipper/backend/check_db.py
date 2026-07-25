import sqlite3

conn = sqlite3.connect('../storage/ai_clipper.db')
cursor = conn.cursor()
cursor.execute("SELECT id, status, error_message, step_message, progress, step FROM jobs ORDER BY created_at DESC LIMIT 3")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}")
    print(f"Status: {row[1]}")
    print(f"Error: {row[2]}")
    print(f"Message: {row[3]}")
    print(f"Progress: {row[4]} (Step {row[5]})")
    print("-" * 20)
conn.close()
