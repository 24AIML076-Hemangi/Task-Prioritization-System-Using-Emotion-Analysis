import requests
import json

BASE_URL = "http://localhost:5000/api"
USER_EMAIL = "john@test.com"

print("\n" + "="*60)
print("🧪 COMPLETE TASK PRIORITY SYSTEM TEST")
print("="*60)

# Test 1: Create tasks with different priorities
print("\n1️⃣  CREATE TASKS WITH DIFFERENT PRIORITIES")
print("-" * 60)

test_tasks = [
    {"title": "URGENT: Fix critical bug", "importance": "important", "urgency": "urgent"},
    {"title": "Plan Q2 quarter", "importance": "important", "urgency": "not-urgent"},
    {"title": "Check emails", "importance": "not-important", "urgency": "urgent"},
    {"title": "Take a break", "importance": "not-important", "urgency": "not-urgent"},
]

created_tasks = []
for task_data in test_tasks:
    payload = {
        "user_id": USER_EMAIL,
        "title": task_data["title"],
        "importance": task_data["importance"],
        "urgency": task_data["urgency"]
    }
    response = requests.post(f"{BASE_URL}/tasks", json=payload)
    
    if response.ok:
        task = response.json()
        created_tasks.append(task)
        print(f"   ✅ {task['id']:2d} | {task_data['title']:30s} | {task['importance']:15s} | {task['urgency']}")
    else:
        print(f"   ❌ Failed to create: {task_data['title']}")

# Test 2: Update task priority
print("\n2️⃣  UPDATE TASK PRIORITY")
print("-" * 60)

if created_tasks:
    task = created_tasks[0]
    print(f"   Task ID: {task['id']}")
    print(f"   Old Priority: {task['importance']} | {task['urgency']}")
    
    update_payload = {
        "importance": "not-important",
        "urgency": "not-urgent",
        "completed": False
    }
    response = requests.put(f"{BASE_URL}/tasks/{task['id']}", json=update_payload)
    
    if response.ok:
        updated = response.json()
        print(f"   New Priority: {updated['importance']} | {updated['urgency']}")
        print(f"   ✅ Update successful")
    else:
        print(f"   ❌ Update failed: {response.json()}")

# Test 3: Get all tasks for user
print("\n3️⃣  GET ALL TASKS FOR USER")
print("-" * 60)

response = requests.get(f"{BASE_URL}/tasks?user_id={USER_EMAIL}")
if response.ok:
    tasks = response.json()
    print(f"   Total Tasks: {len(tasks)}")
    print(f"\n   Matrix Breakdown:")
    
    matrix = {
        ('important', 'urgent'): 0,
        ('important', 'not-urgent'): 0,
        ('not-important', 'urgent'): 0,
        ('not-important', 'not-urgent'): 0,
    }
    
    for task in tasks:
        key = (task['importance'], task['urgency'])
        if key in matrix:
            matrix[key] += 1
    
    print(f"   🔴 Q1 (Important + Urgent):        {matrix[('important', 'urgent')]} tasks")
    print(f"   🟠 Q2 (Important + Not Urgent):    {matrix[('important', 'not-urgent')]} tasks")
    print(f"   🟡 Q3 (Not Important + Urgent):    {matrix[('not-important', 'urgent')]} tasks")
    print(f"   🟢 Q4 (Not Important + Not Urgent):{matrix[('not-important', 'not-urgent')]} tasks")
else:
    print(f"   ❌ Failed to get tasks: {response.json()}")

# Test 4: Complete a task
print("\n4️⃣  MARK TASK AS COMPLETE")
print("-" * 60)

if created_tasks:
    task = created_tasks[0]
    response = requests.patch(f"{BASE_URL}/tasks/{task['id']}/complete")
    
    if response.ok:
        completed = response.json()
        print(f"   Task ID: {task['id']}")
        print(f"   Completed: {completed['completed']}")
        print(f"   ✅ Task marked as complete")
    else:
        print(f"   ❌ Failed: {response.json()}")

print("\n" + "="*60)
print("✅ ALL TESTS COMPLETED")
print("="*60 + "\n")
