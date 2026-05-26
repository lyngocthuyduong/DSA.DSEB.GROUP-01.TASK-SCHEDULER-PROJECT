from pydantic import BaseModel, Field, validator
from typing import List, Optional

# --- SCHEMAS CHO TASK CRUD ---
class TaskBase(BaseModel):
    name: str = Field(..., description="Tên công việc")
    priority: int = Field(5, ge=1, le=10, description="Độ ưu tiên (1-10)")
    duration: int = Field(..., gt=0, description="Thời gian thực thi (phút)")
    dependencies: List[str] = Field(default=[])
    deadline: Optional[int] = Field(None, description="Dành cho thuật toán EDF của M2")
    category: Optional[str] = "General"

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: str
    status: str = "PENDING"

# --- SCHEMAS CHO SCHEDULING (M4 YÊU CẦU ĐẦU RA NHƯ THẾ NÀY) ---
class ScheduleRequest(BaseModel):
    task_ids: List[str] = []
    algorithm: Optional[str] = "HPF"  # Hỗ trợ M2 chọn HPF, EDF, SJF

class ScheduledTaskOutput(BaseModel):
    task_id: str
    task_name: str
    priority: int
    status: str
    start_time: int
    end_time: int
    slack: int = 0
    dependencies_satisfied: List[str]

class ScheduleSummary(BaseModel):
    total_tasks: int
    completed_tasks: int
    blocked_tasks: int
    makespan: int
    critical_path: List[str]
    average_waiting_time: float
    is_valid: bool

class ScheduleResult(BaseModel):
    schedule: List[ScheduledTaskOutput]
    summary: ScheduleSummary
    logs: List[str] = [] # M2 có trả về log, mình ném luôn cho Frontend hiện lên màn hình