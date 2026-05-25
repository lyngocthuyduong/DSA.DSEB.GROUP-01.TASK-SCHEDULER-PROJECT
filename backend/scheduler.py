# -*- coding: utf-8 -*-

from core_dsa.min_heap import MinHeap
from core_dsa.graph_dependency import TaskGraph

def run_scheduler(tasks, algorithm_type='HPF'):
    """
    Điều phối lập lịch mô phỏng chuỗi công việc dựa trên cấu trúc đồ thị phụ thuộc và hàng đợi ưu tiên.
    Hỗ trợ 3 giải thuật: 
      - 'HPF': Highest Priority First (Độ ưu tiên cao nhất làm trước)
      - 'EDF': Earliest Deadline First (Hạn chót gần nhất làm trước)
      - 'SJF': Shortest Job First (Thời gian xử lý ngắn nhất làm trước)
    """
    # Khởi tạo đồ thị từ danh sách tasks
    graph = TaskGraph(tasks)
    
    # Kiểm tra chu trình phụ thuộc bất hợp pháp trước khi xử lý
    cycle = graph.find_cycle_path()
    if cycle:
        return {
            "status": "error",
            "message": f"Phát hiện lỗi phụ thuộc vòng tròn (Cycle loop): {' ➔ '.join(cycle)}",
            "cycle_path": cycle
        }

    # Bản đồ tra cứu nhanh thuộc tính task theo ID
    task_map = {t['id']: t for t in tasks}
    
    # Tính toán bộ chỉ số CPM đường găng làm giàu dữ liệu đầu ra cho Frontend hiển thị
    critical_nodes, cpm_details = graph.compute_critical_path_method(task_map)

    indegree = graph.indegree.copy()
    adj = graph.adj
    
    # Khởi tạo Ready Queue dựa trên cấu trúc Custom Min-Heap của chúng ta
    ready_queue = MinHeap()

    def push_by_algorithm_strategy(task_id):
        """Xác định trọng số (key) nạp vào Min-Heap tương ứng với từng chiến lược giải thuật."""
        task = task_map[task_id]
        if algorithm_type == 'HPF':
            # Do Min-Heap lấy giá trị nhỏ nhất ra trước, để ưu tiên tác vụ có chỉ số priority CAO NHẤT,
            # chúng ta nghịch đảo dấu thành số âm. (Ví dụ: Độ ưu tiên 10 thành -10, sẽ ra trước -5).
            key = -task.get('priority', 0)
        elif algorithm_type == 'EDF':
            # Hạn chót sớm nhất (số nhỏ nhất) thực hiện trước
            key = task.get('deadline', float('inf'))
        elif algorithm_type == 'SJF':
            # Thời gian xử lý ngắn nhất (số nhỏ nhất) thực hiện trước
            key = task.get('duration', 0)
        else:
            key = 0
        ready_queue.push(key, task_id)

    # Đưa toàn bộ các node gốc ban đầu (bán bậc vào bằng 0) vào hàng đợi sẵn sàng
    for t_id, ind in indegree.items():
        if ind == 0:
            push_by_algorithm_strategy(t_id)

    execution_order = []
    current_time = 0
    metrics = {}
    simulation_logs = []

    # Tiến trình mô phỏng điều phối dòng thời gian chạy đơn luồng (Single Processor)
    while not ready_queue.is_empty():
        # Lấy phần tử tối ưu nhất ra khỏi hàng đợi ưu tiên tại thời điểm hiện tại
        weight, curr_id = ready_queue.pop()
        task = task_map[curr_id]
        
        start_time = current_time
        duration = task.get('duration', 0)
        end_time = start_time + duration
        
        # Giả định tất cả công việc có sẵn tại thời điểm t=0 sau khi gỡ bỏ block phụ thuộc
        waiting_time = start_time 
        turnaround_time = end_time
        
        metrics[curr_id] = {
            "task_id": curr_id,
            "name": task.get('name', ''),
            "start_time": start_time,
            "end_time": end_time,
            "waiting_time": waiting_time,
            "turnaround_time": turnaround_time,
            "is_critical": curr_id in critical_nodes,
            "cpm_metrics": cpm_details.get(curr_id, {})
        }
        
        execution_order.append(curr_id)
        metric_val = abs(weight) if algorithm_type == 'HPF' else weight
        simulation_logs.append(
            f"Thời điểm {start_time}s: Tiến hành kích hoạt [{curr_id}] "
            f"(Trọng số đánh giá giải thuật = {metric_val}). Hoàn thành lúc {end_time}s."
        )
        
        # Cập nhật mốc thời gian hệ thống
        current_time = end_time
        
        # Duyệt qua các node lân cận, hạ bậc vào của chúng (Giải thuật Kahn)
        for neighbor in adj[curr_id]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                push_by_algorithm_strategy(neighbor)

    # Tính toán các chỉ số trung bình tổng quan toàn hệ thống
    total_tasks = len(tasks)
    avg_waiting = sum(m['waiting_time'] for m in metrics.values()) / total_tasks if total_tasks else 0
    avg_turnaround = sum(m['turnaround_time'] for m in metrics.values()) / total_tasks if total_tasks else 0

    return {
        "status": "success",
        "algorithm": algorithm_type,
        "execution_order": execution_order,
        "critical_path": critical_nodes,
        "task_details_and_metrics": metrics,
        "summary": {
            "average_waiting_time": round(avg_waiting, 2),
            "average_turnaround_time": round(avg_turnaround, 2),
            "total_execution_time": current_time
        },
        "logs": simulation_logs
    }
