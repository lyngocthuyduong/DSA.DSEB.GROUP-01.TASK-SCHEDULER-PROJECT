from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import uuid
import json
import os
from schemas import TaskCreate, TaskResponse, ScheduleRequest, ScheduleResult
from core_dsa.scheduler import scheduler

app = FastAPI(title="Task Scheduler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory Database dùng để lưu tạm các task
db_tasks: Dict[str, dict] = {}
# ==========================================
# HÀM TỰ ĐỘNG LOAD DỮ LIỆU TEST TỪ FILE JSON
# ==========================================
def load_test_data(filename: str):
    db_tasks.clear() # Xóa dữ liệu cũ trước khi nạp file mới
    
    # 1. Tự động dò tìm thư mục đang chứa file maindsa.py
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Ghép tên thư mục với tên file JSON để ra đường dẫn tuyệt đối
    file_path = os.path.join(current_directory, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            tasks_list = json.load(f)
            for t in tasks_list:
                db_tasks[t['id']] = t
        print(f"✅ Đã nạp thành công {len(tasks_list)} tasks từ file {filename}!")
    else:
        # In ra đường dẫn chi tiết để bạn dễ dàng bắt bệnh
        print(f"❌ Không tìm thấy file. Máy tính đang tìm tại địa chỉ này: {file_path}")

# Đổi tên file test tại đây
load_test_data("stress_test_100.json")
# ==========================================
# 1. API QUẢN LÝ TASK (CRUD)
# ==========================================

@app.post("/api/v1/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate):
    task_id = f"task_{uuid.uuid4().hex[:6]}"
    
    # Validation: Ràng buộc toàn vẹn
    for dep_id in task.dependencies:
        if dep_id not in db_tasks:
            raise HTTPException(status_code=400, detail=f"Dependency '{dep_id}' không tồn tại!")
    if task_id in task.dependencies:
        raise HTTPException(status_code=400, detail="Lỗi: Task không thể phụ thuộc vào chính nó.")

    new_task = task.dict()
    new_task["id"] = task_id
    new_task["status"] = "PENDING"
    
    db_tasks[task_id] = new_task
    return new_task

@app.get("/api/v1/tasks", response_model=List[TaskResponse])
def get_all_tasks():
    return list(db_tasks.values())

@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    if task_id not in db_tasks:
        raise HTTPException(status_code=404, detail="Không tìm thấy Task")
    return db_tasks[task_id]

@app.delete("/api/v1/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    if task_id not in db_tasks:
        raise HTTPException(status_code=404, detail="Không tìm thấy Task")
    
    # Cần xóa task này khỏi danh sách dependencies của các task khác trước khi xóa nó
    for t in db_tasks.values():
        if task_id in t["dependencies"]:
            t["dependencies"].remove(task_id)
            
    del db_tasks[task_id]
    return None
@app.put("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task_update: TaskCreate):
    # 1. Kiểm tra xem task cần sửa có tồn tại trong DB không
    if task_id not in db_tasks:
        raise HTTPException(status_code=404, detail="Không tìm thấy Task để cập nhật")
    
    # 2. Validation: Kiểm tra xem các dependencies mới truyền vào có hợp lệ không
    for dep_id in task_update.dependencies:
        if dep_id not in db_tasks:
            raise HTTPException(status_code=400, detail=f"Dependency '{dep_id}' không tồn tại!")
            
    # 3. Chặn không cho task tự phụ thuộc chính nó
    if task_id in task_update.dependencies:
        raise HTTPException(status_code=400, detail="Lỗi: Task không thể phụ thuộc vào chính nó.")

    # 4. Tiến hành đè dữ liệu mới lên dữ liệu cũ (nhưng giữ nguyên ID và Trạng thái cũ)
    updated_data = task_update.dict()
    updated_data["id"] = task_id
    updated_data["status"] = db_tasks[task_id]["status"]  # Giữ nguyên status cũ (PENDING/COMPLETED...)
    
    db_tasks[task_id] = updated_data
    return updated_data

# ==========================================
# 2. API TÍCH HỢP THUẬT TOÁN (GỌI M2 CODE)
# ==========================================

@app.post("/api/v1/schedule", response_model=ScheduleResult)
def run_scheduling(payload: ScheduleRequest):
    # Chuẩn bị dữ liệu đầu vào cho M2
    tasks_to_schedule = list(db_tasks.values())
    if payload.task_ids:
        tasks_to_schedule = [t for t in tasks_to_schedule if t["id"] in payload.task_ids]
        
    if not tasks_to_schedule:
        raise HTTPException(status_code=400, detail="Không có task nào để lập lịch!")

    # ----------------------------------------------------
    # GỌI HÀM CỦA M2 TẠI ĐÂY
    # ----------------------------------------------------
    m2_result = scheduler(tasks_to_schedule, algorithm_type=payload.algorithm)
    
    # Xử lý nếu M2 phát hiện chu trình (Graph invalid)
    if m2_result.get("status") == "error":
        raise HTTPException(
            status_code=409, 
            detail=f"{m2_result.get('message')} - Nodes: {m2_result.get('cycle_path')}"
        )

    # ----------------------------------------------------
    # BIẾN ĐỔI KẾT QUẢ M2 THÀNH ĐỊNH DẠNG PDF CHO M4
    # ----------------------------------------------------
    schedule_output = []
    task_details = m2_result["task_details_and_metrics"]
    
    # Lặp theo thứ tự thực thi mà M2 đã sắp xếp
    for t_id in m2_result["execution_order"]:
        t_metric = task_details[t_id]
        original_task = db_tasks[t_id]
        
        schedule_output.append({
            "task_id": t_id,
            "task_name": t_metric["name"],
            "priority": original_task["priority"],
            "status": "COMPLETED",
            "start_time": t_metric["start_time"],
            "end_time": t_metric["end_time"],
            "dependencies_satisfied": original_task["dependencies"]
        })

    # Cập nhật trạng thái trong "Database"
    for t_id in m2_result["execution_order"]:
        db_tasks[t_id]["status"] = "COMPLETED"

    # Đóng gói đối tượng Summary
    summary_output = {
        "total_tasks": len(tasks_to_schedule),
        "completed_tasks": len(m2_result["execution_order"]),
        "blocked_tasks": len(tasks_to_schedule) - len(m2_result["execution_order"]),
        "makespan": m2_result["summary"]["total_execution_time"],
        "critical_path": m2_result["critical_path"],
        "average_waiting_time": m2_result["summary"]["average_waiting_time"],
        "is_valid": True
    }

    return {
        "schedule": schedule_output,
        "summary": summary_output,
        "logs": m2_result.get("logs", [])
    }
