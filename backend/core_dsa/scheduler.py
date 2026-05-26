# -*- coding: utf-8 -*-

# ==========================================
# 1. CẤU TRÚC DỮ LIỆU: MIN-HEAP
# ==========================================
class MinHeap:
    """Custom Min-Heap (Priority Queue) triển khai thủ công[cite: 7, 43]."""
    def __init__(self):
        self.heap = []

    def push(self, key, value):
        self.heap.append((key, value))
        self._heapify_up(len(self.heap) - 1)

    def pop(self):
        if self.is_empty():
            raise IndexError("Lỗi: Không thể pop từ một Heap rỗng.")
        if len(self.heap) == 1:
            return self.heap.pop()
        root = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return root

    def is_empty(self):
        return len(self.heap) == 0

    def _heapify_up(self, index):
        parent = (index - 1) // 2
        while index > 0 and self.heap[index][0] < self.heap[parent][0]:
            self.heap[index], self.heap[parent] = self.heap[parent], self.heap[index]
            index = parent
            parent = (index - 1) // 2

    def _heapify_down(self, index):
        length = len(self.heap)
        while True:
            left = 2 * index + 1
            right = 2 * index + 2
            smallest = index

            if left < length and self.heap[left][0] < self.heap[smallest][0]:
                smallest = left
            if right < length and self.heap[right][0] < self.heap[smallest][0]:
                smallest = right

            if smallest != index:
                self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
                index = smallest
            else:
                break


# ==========================================
# 2. CẤU TRÚC DỮ LIỆU: TASK GRAPH (DAG)
# ==========================================
class TaskGraph:
    """Quản lý Đồ thị phụ thuộc của các tác vụ (Dependency Graph)[cite: 6, 32]."""
    def __init__(self, tasks):
        self.adj = {t['id']: [] for t in tasks}
        self.indegree = {t['id']: 0 for t in tasks}
        
        # Build adjacency list [cite: 37]
        for t in tasks:
            for dep in t.get('dependencies', []):
                if dep in self.adj:
                    self.adj[dep].append(t['id'])
                    self.indegree[t['id']] += 1

    def find_cycle_path(self):
        """Phát hiện chu trình bằng DFS 3 màu[cite: 39, 48]."""
        state = {node: 0 for node in self.adj}
        parent = {node: None for node in self.adj}
        cycle_nodes = []

        def dfs(node):
            state[node] = 1 
            for neighbor in self.adj[node]:
                if state[neighbor] == 1:
                    curr = node
                    path = [neighbor, curr]
                    while curr != neighbor and parent[curr] is not None:
                        curr = parent[curr]
                        path.append(curr)
                    path.reverse()
                    cycle_nodes.extend(path)
                    return True
                elif state[neighbor] == 0:
                    parent[neighbor] = node
                    if dfs(neighbor):
                        return True
            state[node] = 2 
            return False

        for node in self.adj:
            if state[node] == 0:
                if dfs(node):
                    return cycle_nodes
        return []

    def compute_critical_path_method(self, task_map):
        """Thuật toán Đường găng (Critical Path Method - CPM)[cite: 84, 85]."""
        indeg_copy = self.indegree.copy()
        queue = [t_id for t_id, ind in indeg_copy.items() if ind == 0]
        topo_order = []
        
        while queue:
            u = queue.pop(0)
            topo_order.append(u)
            for v in self.adj[u]:
                indeg_copy[v] -= 1
                if indeg_copy[v] == 0:
                    queue.append(v)

        if len(topo_order) != len(self.adj):
            return [], {}

        es = {node: 0 for node in self.adj}
        ef = {node: 0 for node in self.adj}
        
        for u in topo_order:
            duration = task_map[u].get('duration', 0)
            ef[u] = es[u] + duration
            for v in self.adj[u]:
                if ef[u] > es[v]:
                    es[v] = ef[u]

        max_ef = max(ef.values()) if ef else 0

        ls = {node: max_ef for node in self.adj}
        lf = {node: max_ef for node in self.adj}
        
        for u in reversed(topo_order):
            if self.adj[u]:
                lf[u] = min(ls[v] for v in self.adj[u])
            duration = task_map[u].get('duration', 0)
            ls[u] = lf[u] - duration

        critical_nodes = []
        cpm_details = {}
        for node in self.adj:
            slack = ls[node] - es[node]
            cpm_details[node] = {"ES": es[node], "EF": ef[node], "LS": ls[node], "LF": lf[node], "slack": slack}
            if slack == 0:
                critical_nodes.append(node)

        return critical_nodes, cpm_details


# ==========================================
# 3. INTERFACE ENGINE (HÀM GIAO TIẾP VỚI API)
# ==========================================

def build_dag(tasks):
    """Return adjacency list [cite: 205-206]."""
    graph = TaskGraph(tasks)
    return graph

def detect_cycle(dag):
    """Return cycle nodes or None [cite: 207-208]."""
    cycle = dag.find_cycle_path()
    return cycle if cycle else None

def topological_schedule(tasks, dag):
    """
    Run Kahn's algorithm + Priority Queue [cite: 209-210].
    Priority rule: priority DESC -> duration ASC -> id ASC [cite: 211-214].
    Returns: schedule array and summary object [cite: 216-217].
    """
    cycle = detect_cycle(dag)
    
    # 1. Xử lý lỗi chu trình (Cycle Detection) [cite: 48-54]
    if cycle:
        return {
            "schedule": [],
            "summary": {
                "total_tasks": len(tasks), # [cite: 154]
                "completed_tasks": 0, # [cite: 155]
                "blocked_tasks": len(tasks), # [cite: 156]
                "makespan": 0, # [cite: 157]
                "critical_path": [], # [cite: 158]
                "average_waiting_time": 0, # [cite: 161]
                "is_valid": False, # [cite: 162]
                "cycle_nodes": cycle # Bổ sung để Frontend highlight lỗi
            }
        }

    task_map = {t['id']: t for t in tasks}
    critical_nodes, cpm_details = dag.compute_critical_path_method(task_map)

    indegree = dag.indegree.copy()
    adj = dag.adj
    
    ready_queue = MinHeap()

    # 2. Khởi tạo Queue với Priority Rule chuẩn PDF [cite: 44-47]
    for t_id, ind in indegree.items():
        if ind == 0:
            task = task_map[t_id]
            # Key: (-Priority, Duration, ID) -> Bảo đảm đúng thứ tự sắp xếp [cite: 211-214]
            key = (-task.get('priority', 1), task.get('duration', 0), t_id)
            ready_queue.push(key, t_id)

    schedule_output = []
    current_time = 0
    total_waiting_time = 0

    # 3. Vòng lặp điều phối chính [cite: 41-47]
    while not ready_queue.is_empty():
        weight_tuple, curr_id = ready_queue.pop()
        task = task_map[curr_id]
        
        start_time = current_time
        duration = task.get('duration', 0)
        end_time = start_time + duration
        
        waiting_time = start_time
        total_waiting_time += waiting_time
        
        slack = cpm_details.get(curr_id, {}).get('slack', 0)
        
        # Build Output Item [cite: 133-144]
        schedule_output.append({
            "task_id": curr_id, # [cite: 135]
            "task_name": task.get('name', ''), # [cite: 139]
            "priority": task.get('priority', 1), # [cite: 140]
            "status": "COMPLETED", # [cite: 141]
            "start_time": start_time, # [cite: 142]
            "end_time": end_time, # [cite: 143]
            "slack": slack,
            "dependencies_satisfied": task.get('dependencies', []) # [cite: 144]
        })
        
        current_time = end_time
        
        # Giải thuật Kahn's [cite: 8, 42]
        for neighbor in adj[curr_id]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                n_task = task_map[neighbor]
                n_key = (-n_task.get('priority', 1), n_task.get('duration', 0), neighbor)
                ready_queue.push(n_key, neighbor)

    # 4. Tính toán Metrics [cite: 80-86]
    total_tasks = len(tasks)
    avg_waiting_time = total_waiting_time / total_tasks if total_tasks > 0 else 0

    return {
        "schedule": schedule_output, # [cite: 133]
        "summary": { # [cite: 153]
            "total_tasks": total_tasks, # [cite: 154]
            "completed_tasks": len(schedule_output), # [cite: 155]
            "blocked_tasks": 0, # [cite: 156]
            "makespan": current_time, # [cite: 157]
            "critical_path": critical_nodes, # [cite: 158]
            "average_waiting_time": round(avg_waiting_time, 2), # [cite: 161]
            "is_valid": True # [cite: 162]
        }
    }


def run_scheduler(tasks, algorithm_type="HPF"):
    dag = build_dag(tasks)
    algorithm = (algorithm_type or "").strip().lower()
    if algorithm not in ["kahn", "topological", "hpf", "priority", "highestpriorityfirst"]:
        algorithm = "kahn"

    result = topological_schedule(tasks, dag)

    if not result["summary"].get("is_valid", True):
        return {
            "status": "error",
            "message": "Chu trình dependency được phát hiện.",
            "cycle_path": result["summary"].get("cycle_nodes", [])
        }

    task_details_and_metrics = {
        item["task_id"]: {
            "name": item["task_name"],
            "start_time": item["start_time"],
            "end_time": item["end_time"],
            "slack": item.get("slack", 0),
            "dependencies_satisfied": item.get("dependencies_satisfied", []),
        }
        for item in result["schedule"]
    }

    return {
        "status": "ok",
        "execution_order": [item["task_id"] for item in result["schedule"]],
        "task_details_and_metrics": task_details_and_metrics,
        "summary": result["summary"],
        "critical_path": result["summary"].get("critical_path", []),
        "logs": []
    }
