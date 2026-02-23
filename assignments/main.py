from fastapi import FastAPI, HTTPException, Query, Path
from typing import List, Optional
from datetime import datetime
from schemas import TaskCreate, TaskUpdate, TaskOut

app = FastAPI(title="Mini Task Manager API")

tasks_db = {}
current_id = 1


@app.post("/tasks", response_model=TaskOut)
def create_task(task_in: TaskCreate):
    global current_id

    task_data = task_in.model_dump()
    task_data["id"] = current_id
    task_data["created_at"] = datetime.now()
    tasks_db[current_id] = task_data
    current_id += 1

    return task_data


@app.get("/tasks", response_model=List[TaskOut])
def get_tasks(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=50),
        is_done: Optional[bool] = Query(None),
        priority: Optional[int] = Query(None, ge=1, le=5),
        tag: Optional[str] = Query(None),
        search: Optional[str] = Query(None)
):
    filtered_tasks = []

    for task in tasks_db.values():
        if is_done is not None and task["is_done"] != is_done:
            continue
        if priority is not None and task["priority"] != priority:
            continue
        if tag is not None and tag not in task["tags"]:
            continue
        if search is not None:
            s_lower = search.lower()
            t_lower = task["title"].lower()
            d_lower = task["description"].lower() if task["description"] else ""
            if s_lower not in t_lower and s_lower not in d_lower:
                continue

        filtered_tasks.append(task)

    return filtered_tasks[skip: skip + limit]


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int = Path(..., gt=0)):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Assignment is unavailable!")
    return tasks_db[task_id]


@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_in: TaskUpdate, task_id: int = Path(..., gt=0)):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Assignment is unavailable!")

    update_data = task_in.model_dump(exclude_unset=True)
    task = tasks_db[task_id]
    for key, value in update_data.items():
        task[key] = value

    tasks_db[task_id] = task
    return task


@app.put("/tasks/{task_id}/done", response_model=TaskOut)
def toggle_task_status(task_id: int = Path(..., gt=0), value: bool = Query(True)):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Assignment is unavailable!")

    tasks_db[task_id]["is_done"] = value
    return tasks_db[task_id]


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int = Path(..., gt=0)):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Assignment is unavailable!")

    del tasks_db[task_id]
    return {"status": "deleted", "id": task_id}