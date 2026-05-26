import sys
import os

# 1. Ép Python nhận diện thư mục gốc (backend/) để tìm file scheduler.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
# Đảm bảo bạn import đúng đường dẫn tới file scheduler.py của nhóm
from core_dsa.scheduler import MinHeap, TaskGraph, build_dag, detect_cycle, topological_schedule, run_scheduler

class TestMinHeap:
    """Kiểm thử cấu trúc Hàng đợi ưu tiên (Priority Queue)"""
    
    def test_min_heap_basic(self):
        heap = MinHeap()
        assert heap.is_empty() is True
        
        heap.push(10, "Task_A")
        heap.push(5, "Task_B")
        heap.push(15, "Task_C")
        
        assert heap.is_empty() is False
        # Do là Min-Heap nên key nhỏ nhất (5) phải ra trước
        assert heap.pop()[1] == "Task_B"
        assert heap.pop()[1] == "Task_A"
        assert heap.pop()[1] == "Task_C"
        assert heap.is_empty() is True

    def test_heap_priority_rules(self):
        heap = MinHeap()
        # Trong thuật toán, nhóm dùng key = (-priority, duration, task_id)
        # -> Priority càng cao (VD: 10), âm priority càng nhỏ (-10) -> Lên đầu Heap
        # -> Nếu priority bằng nhau, duration nhỏ hơn sẽ lên đầu
        
        # Tuple: (-priority, duration, task_id)
        heap.push((-5, 30, "T1"), "T1")  # Priority 5, thời gian 30
        heap.push((-10, 50, "T2"), "T2") # Priority 10 (Cao nhất) -> Ra số 1
        heap.push((-8, 15, "T3"), "T3")  # Priority 8, thời gian 15
        heap.push((-8, 10, "T4"), "T4")  # Priority 8, thời gian 10 -> Ra số 2 (vì duration nhỏ hơn T3)

        assert heap.pop()[1] == "T2"
        assert heap.pop()[1] == "T4"
        assert heap.pop()[1] == "T3"
        assert heap.pop()[1] == "T1"


class TestTaskGraphAndCycle:
    """Kiểm thử cấu trúc Đồ thị (DAG), CPM và thuật toán Dò chu trình"""

    def test_valid_dag_and_cpm(self):
        # Đồ thị: T1 -> T2 (duration 20)
        #          -> T3 (duration 10)
        tasks = [
            {"id": "T1", "duration": 10, "dependencies": []},
            {"id": "T2", "duration": 20, "dependencies": ["T1"]}, # T2 phụ thuộc T1
            {"id": "T3", "duration": 10, "dependencies": ["T1"]}  # T3 phụ thuộc T1
        ]
        graph = TaskGraph(tasks)
        
        # Kiểm tra chu trình
        has_cycle = graph.find_cycle_path()
        assert len(has_cycle) == 0

        # Kiểm tra CPM (Đường găng)
        task_map = {t['id']: t for t in tasks}
        critical_nodes, cpm_details = graph.compute_critical_path_method(task_map)
        
        # Makespan = 10 (T1) + 20 (T2) = 30
        assert "T1" in critical_nodes
        assert "T2" in critical_nodes
        assert "T3" not in critical_nodes # T3 có slack vì chỉ tốn 10 phút, trong khi nhánh kia tốn 20 phút

        assert cpm_details["T1"]["slack"] == 0
        assert cpm_details["T3"]["slack"] > 0

    def test_cyclic_dependency(self):
        # Đồ thị có chu trình: A phụ thuộc C, B phụ thuộc A, C phụ thuộc B (C -> A -> B -> C)
        tasks = [
            {"id": "A", "dependencies": ["C"]},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": ["B"]}
        ]
        graph = TaskGraph(tasks)
        cycle_path = graph.find_cycle_path()
        
        assert len(cycle_path) > 0
        assert set(cycle_path) == {"A", "B", "C"}


class TestSchedulerEngine:
    """Kiểm thử toàn diện Bộ lập lịch lõi"""

    def test_topological_schedule_success(self):
        tasks = [
            {"id": "T1", "name": "Task 1", "priority": 10, "duration": 10, "dependencies": []},
            {"id": "T2", "name": "Task 2", "priority": 5, "duration": 20, "dependencies": ["T1"]},
            {"id": "T3", "name": "Task 3", "priority": 8, "duration": 15, "dependencies": ["T1"]}
        ]
        dag = build_dag(tasks)
        result = topological_schedule(tasks, dag)
        
        summary = result["summary"]
        assert summary["is_valid"] is True
        assert summary["total_tasks"] == 3
        assert summary["blocked_tasks"] == 0
        # Single-worker -> chạy tuần tự -> Tổng thời gian = 10 (T1) + 15 (T3) + 20 (T2) = 45
        assert summary["makespan"] == 45 
        
        schedule = result["schedule"]
        assert len(schedule) == 3
        assert schedule[0]["task_id"] == "T1"
        assert schedule[1]["task_id"] == "T3" 
        assert schedule[2]["task_id"] == "T2"

        # Thời gian chạy tuyến tính (Single-worker)
        assert schedule[0]["start_time"] == 0
        assert schedule[0]["end_time"] == 10
        
        assert schedule[1]["start_time"] == 10 # T3 chạy sau T1
        assert schedule[1]["end_time"] == 25
        
        assert schedule[2]["start_time"] == 25 # T2 chạy sau T3
        assert schedule[2]["end_time"] == 45

    def test_run_scheduler_with_cycle(self):
        # Sử dụng hàm wrapper run_scheduler như API Backend sẽ gọi
        tasks = [
            {"id": "T1", "name": "Task 1", "priority": 10, "duration": 10, "dependencies": ["T2"]},
            {"id": "T2", "name": "Task 2", "priority": 10, "duration": 10, "dependencies": ["T1"]}
        ]
        
        result = run_scheduler(tasks)
        
        assert result["status"] == "error"
        assert len(result["cycle_path"]) > 0
        assert "T1" in result["cycle_path"]
