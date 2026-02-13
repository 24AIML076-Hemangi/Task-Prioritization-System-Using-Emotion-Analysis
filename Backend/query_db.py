import sqlite3

conn = sqlite3.connect('tasks.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('=== TABLES ===')
for table in tables:
    print(f'  - {table[0]}')

print('\n=== TASKS ===')
cursor.execute('SELECT * FROM tasks;')
columns = [description[0] for description in cursor.description]
tasks = cursor.fetchall()
if tasks:
    for task in tasks:
        print(dict(zip(columns, task)))
else:
    print('  (No tasks)')

print('\n=== EMOTION LOGS ===')
cursor.execute('SELECT * FROM emotion_logs;')
columns = [description[0] for description in cursor.description]
logs = cursor.fetchall()
if logs:
    for log in logs:
        print(dict(zip(columns, log)))
else:
    print('  (No emotion logs)')

conn.close()
