# -*- coding: utf-8 -*-

class TaskGraph:
    """
    Quản lý Đồ thị phụ thuộc của các tác vụ (Dependency Graph) sử dụng Danh sách kề.
    """
    def __init__(self, tasks):
        """
        tasks: List gồm các dict dạng: 
        {'id': 'T1', 'name': 'Task 1', 'duration': 5, 'dependencies': []}
        """
        self.adj = {t['id']: [] for t in tasks}
        self.indegree = {t['id']: 0 for t in tasks}
        
        # Xây dựng đồ thị: Nếu B phụ thuộc vào A (A là dependency của B) -> Cạnh nối A -> B
        for t in tasks:
            for dep in t.get('dependencies', []):
                if dep in self.adj:
                    self.adj[dep].append(t['id'])
                    self.indegree[t['id']] += 1

    def find_cycle_path(self):
        """
        Sử dụng thuật toán DFS 3 màu để phát hiện chu trình phụ thuộc vòng tròn.
        Trạng thái màu sắc: 0 (White - Chưa duyệt), 1 (Grey - Đang duyệt), 2 (Black - Đã duyệt xong).
        Trả về: Danh sách thứ tự các node tạo thành chu trình, hoặc mảng rỗng nếu là DAG.
        """
        state = {node: 0 for node in self.adj}
        parent = {node: None for node in self.adj}
        cycle_nodes = []

        def dfs(node):
            state[node] = 1  # Chuyển sang Grey (Đang trong nhánh đệ quy hiện tại)
            for neighbor in self.adj[node]:
                if state[neighbor] == 1:
                    # Phát hiện chu trình phụ thuộc vòng tròn! Tiến hành truy vết đường đi lỗi
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
            state[node] = 2  # Chuyển sang Black (Hoàn thành nhánh duyệt)
            return False

        for node in self.adj:
            if state[node] == 0:
                if dfs(node):
                    return cycle_nodes
        return []

    def compute_critical_path_method(self, task_map):
        """
        Thuật toán Đường găng (Critical Path Method - CPM) qua 2 lượt duyệt đồ thị (Forward & Backward).
        Yêu cầu hệ thống phải là DAG (Không chứa chu trình).
        """
        # 1. Tạo thứ tự Topological bằng thuật toán Kahn cơ bản để phục vụ tính CPM
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
            return [], {}  # Tồn tại chu trình ngầm, không thể tính CPM

        # 2. Lượt duyệt xuôi (Forward Pass) -> Tính thời điểm bắt đầu sớm (ES) và kết thúc sớm (EF)
        es = {node: 0 for node in self.adj}
        ef = {node: 0 for node in self.adj}
        
        for u in topo_order:
            duration = task_map[u].get('duration', 0)
            ef[u] = es[u] + duration
            for v in self.adj[u]:
                if ef[u] > es[v]:
                    es[v] = ef[u]

        max_ef = max(ef.values()) if ef else 0

        # 3. Lượt duyệt ngược (Backward Pass) -> Tính thời điểm kết thúc muộn (LF) và bắt đầu muộn (LS)
        ls = {node: max_ef for node in self.adj}
        lf = {node: max_ef for node in self.adj}
        
        for u in reversed(topo_order):
            if self.adj[u]:
                lf[u] = min(ls[v] for v in self.adj[u])
            duration = task_map[u].get('duration', 0)
            ls[u] = lf[u] - duration

        # 4. Xác định các Node thuộc Đường găng nơi thời gian dự trữ (Slack) bằng 0
        critical_nodes = []
        cpm_details = {}
        for node in self.adj:
            slack = ls[node] - es[node]
            cpm_details[node] = {
                "ES": es[node], "EF": ef[node],
                "LS": ls[node], "LF": lf[node],
                "slack": slack
            }
            if slack == 0:
                critical_nodes.append(node)

        return critical_nodes, cpm_details