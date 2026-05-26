# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
import uuid
import json
import os

# Import các Schema Pydantic định sẵn từ lớp cấu trúc dữ liệu trung gian
from schemas import TaskCreate, TaskResponse, ScheduleRequest, ScheduleResult
# Import hàm xử lý giải thuật lõi của M2
from core_dsa.scheduler import run_scheduler
# Import cấu trúc kết nối và định nghĩa bảng từ hệ thống database nâng cấp
from database import engine, SessionLocal, Base
import models

# Tự động kiểm tra và sinh tệp database vật lý "tasks.db" cùng các bảng nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Scheduler API with SQLite Persistance")

# Cấu hình Middleware CORS cho phép Frontend kết nối API không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# DEPENDENCY: KHỞI TẠO VÀ ĐÓNG SESSION DATABASE
# ==========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# HÀM TRỢ GIÚP: TỰ ĐỘNG NẠP DỮ LIỆU CŨ LÚC KHỞI CHẠY (NẾU CẦN)
# ==========================================
def load_test_data_on_startup(filename: str):
    db = SessionLocal()
    # Xóa sạch dữ liệu cũ trong bảng để nạp bộ dữ liệu kiểm thử mới
    db.query(models.TaskDB).delete()
    db.commit()
    
    current_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_directory, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            tasks_list = json.load(f)
            for t in tasks_list:
                db_task = models.TaskDB(
                    id=t['id'],
                    name=t['name'],
                    priority=t['priority'],
                    duration=t['duration'],
                    dependencies=t.get('dependencies', []),
                    category=t.get('category', 'General'),
                    status='PENDING'
                )
                db.add(db_task)
            db.commit()
        print(f"✅ [Startup] Đã nạp thành công {len(tasks_list)} tasks từ file {filename} vào SQLite!")
    else:
        print(f"❌ [Startup] Không tìm thấy tệp tin Mock Data tại: {file_path}")
    db.close()

# Bỏ comment dòng dưới đây nếu nhóm muốn tự động nạp cứng dữ liệu mỗi khi bật Server
# load_test_data_on_startup("stress_test_100.json")


# ==========================================
# 1. NHÓM API QUẢN LÝ TASK (CRUD TỪ SQLITE)
# ==========================================

@app.post("/api/v1/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    task_id = f"task_{uuid.uuid4().hex[:6]}"
    
    # Validation: Ràng buộc toàn vẹn thực thể (Kiểm tra ID phụ thuộc có tồn tại trong DB không)
    existing_ids = [t.id for t in db.query(models.TaskDB.id).all()]
    for dep_id in task.dependencies:
        if dep_id not in existing_ids:
            raise HTTPException(status_code=400, detail=f"Dependency '{dep_id}' không tồn tại trong hệ thống!")
            
    if task_id in task.dependencies:
        raise HTTPException(status_code=400, detail="Lỗi logic: Tác vụ không thể phụ thuộc vào chính nó.")

    # Đóng gói dữ liệu lưu xuống SQLite
    db_task = models.TaskDB(
        id=task_id,
        name=task.name,
        priority=task.priority,
        duration=task.duration,
        dependencies=task.dependencies,
        deadline=task.deadline,
        category=task.category,
        status="PENDING"
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/api/v1/tasks", response_model=List[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db)):
    return db.query(models.TaskDB).all()

@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(models.TaskDB).filter(models.TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy Tác vụ yêu cầu")
    return task

@app.put("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task_update: TaskCreate, db: Session = Depends(get_db)):
    db_task = db.query(models.TaskDB).filter(models.TaskDB.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Không tìm thấy Tác vụ để tiến hành cập nhật")
    
    # Validation: Kiểm tra tính hợp lệ của mảng phụ thuộc mới gửi lên
    existing_ids = [t.id for t in db.query(models.TaskDB.id).all()]
    for dep_id in task_update.dependencies:
        if dep_id not in existing_ids:
            raise HTTPException(status_code=400, detail=f"Dependency '{dep_id}' không tồn tại!")
            
    if task_id in task_update.dependencies:
        raise HTTPException(status_code=400, detail="Lỗi logic: Tác vụ không thể phụ thuộc vào chính nó.")

    # Đè dữ liệu mới lên bản ghi cũ (Giữ nguyên ID và Trạng thái vòng đời cũ)
    db_task.name = task_update.name
    db_task.priority = task_update.priority
    db_task.duration = task_update.duration
    db_task.dependencies = task_update.dependencies
    db_task.deadline = task_update.deadline
    db_task.category = task_update.category
    
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/api/v1/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task_to_delete = db.query(models.TaskDB).filter(models.TaskDB.id == task_id).first()
    if not task_to_delete:
        raise HTTPException(status_code=404, detail="Không tìm thấy Tác vụ để thực hiện lệnh xóa")
    
    # Duyệt cập nhật: Xóa ID của tác vụ này ra khỏi danh sách dependencies của toàn bộ tác vụ khác
    all_tasks = db.query(models.TaskDB).all()
    for t in all_tasks:
        if task_id in t.dependencies:
            # Gán lại mảng mới loại trừ ID đã xóa để SQLAlchemy tự động nhận diện cập nhật trường JSON
            t.dependencies = [d for d in t.dependencies if d != task_id]
            
    db.delete(task_to_delete)
    db.commit()
    return None


# ==========================================
# 2. API TÍCH HỢP ĐIỀU PHỐI THUẬT TOÁN (M2 ENGINE)
# ==========================================

@app.post("/api/v1/schedule", response_model=ScheduleResult)
def run_scheduling(payload: ScheduleRequest, db: Session = Depends(get_db)):
    # 1. Truy vấn kéo tập hợp tác vụ từ SQLite ra ổ đĩa RAM
    query = db.query(models.TaskDB)
    if payload.task_ids:
        query = query.filter(models.TaskDB.id.in_(payload.task_ids))
    
    db_tasks_list = query.all()
    if not db_tasks_list:
        raise HTTPException(status_code=400, detail="Không tìm thấy tác vụ nào hợp lệ để tiến hành lập lịch!")

    # 2. Ánh xạ cấu trúc dữ liệu ORM thành dạng list[dict] thô nguyên bản để M2 Engine xử lý không lỗi
    tasks_for_m2 = [
        {
            "id": t.id,
            "name": t.name,
            "priority": t.priority,
            "duration": t.duration,
            "dependencies": t.dependencies
        }
        for t in db_tasks_list
    ]

    # 3. Kích hoạt bộ xử lý lõi cốt lõi của M2
    m2_result = run_scheduler(tasks_for_m2, algorithm_type=payload.algorithm)
    
    # Nhánh bẻ hướng: Nếu Engine của M2 phát hiện Đồ thị chứa chu trình (Invalid DAG)
    if m2_result.get("status") == "error":
        raise HTTPException(
            status_code=409, 
            detail=f"{m2_result.get('message')} - Tuyến chu trình kẹt: {m2_result.get('cycle_path')}"
        )

    # 4. Tái cấu trúc cấu trúc dữ liệu từ M2 trả về khớp với định dạng hiển thị yêu cầu của M4 (Frontend)
    schedule_output = []
    task_metrics_map = m2_result["task_details_and_metrics"]
    original_tasks_map = {t.id: t for t in db_tasks_list}
    
    # Lặp tuần tự sắp xếp dựa trên mảng thứ tự thực thi tuyến tính của thuật toán
    for t_id in m2_result["execution_order"]:
        t_metric = task_metrics_map[t_id]
        orig_task = original_tasks_map[t_id]
        
        schedule_output.append({
            "task_id": t_id,
            "task_name": t_metric["name"],
            "priority": orig_task.priority,
            "status": "COMPLETED",
            "start_time": t_metric["start_time"],
            "end_time": t_metric["end_time"],
            "slack": t_metric.get("slack", 0),
            "dependencies_satisfied": orig_task.dependencies
        })
        
        # Cập nhật trạng thái chu kỳ vòng đời của Tác vụ thành COMPLETED lưu xuống SQLite
        orig_task.status = "COMPLETED"

    db.commit()

    # Đóng gói chỉ số Dashboard Thống kê tổng hợp toàn cục phục vụ Render UI
    summary_output = {
        "total_tasks": len(tasks_for_m2),
        "completed_tasks": len(m2_result["execution_order"]),
        "blocked_tasks": len(tasks_for_m2) - len(m2_result["execution_order"]),
        "makespan": m2_result["summary"].get("makespan", 0),
        "critical_path": m2_result["critical_path"],
        "average_waiting_time": m2_result["summary"]["average_waiting_time"],
        "is_valid": True
    }

    return {
        "schedule": schedule_output,
        "summary": summary_output,
        "logs": m2_result.get("logs", [])
    }


# ==========================================
# 3. API ẨN DÀNH CHO ADMIN (M5 DÙNG ĐỂ NẠP FILE MOCK DATA KHI LIVE DEMO)
# ==========================================
@app.post("/api/v1/admin/load-mock-data/{filename}", tags=["Admin Backdoor"])
def admin_load_mock_data(filename: str, db: Session = Depends(get_db)):
    """
    API nội bộ dùng để Flush rỗng Database và nạp nhanh các kịch bản kiểm thử JSON có sẵn.
    Ví dụ tham số filename: normal_dag.json, cycle_error.json, stress_test_50.json
    """
    # Xóa sạch toàn bộ bản ghi cũ trong bảng dữ liệu
    db.query(models.TaskDB).delete()
    db.commit()
    
    current_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_directory, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Không tìm thấy file Mock Data mang tên '{filename}' tại thư mục Backend.")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        tasks_list = json.load(f)
        for t in tasks_list:
            db_task = models.TaskDB(
                id=t['id'],
                name=t['name'],
                priority=t['priority'],
                duration=t['duration'],
                dependencies=t.get('dependencies', []),
                category=t.get('category', 'General'),
                status='PENDING'
            )
            db.add(db_task)
        db.commit()
        
    return {"message": f"Kích hoạt thành công! Đã làm rỗng SQLite Database và nạp {len(tasks_list)} tác vụ từ tệp '{filename}'."}