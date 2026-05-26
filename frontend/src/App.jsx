import "./App.css";
import { useState, useEffect } from "react";
// Import thư viện vẽ đồ thị xịn xò
import ReactFlow, { Background, Controls, MarkerType } from "reactflow";
import "reactflow/dist/style.css";

const STATUS_COLORS = {
  PENDING: "#9e9e9e",
  READY: "#2979ff",
  RUNNING: "#ff9800",
  COMPLETED: "#00c853",
  BLOCKED: "#ff5252",
};

export default function App() {
  // 1. Cho giỏ hàng trống lúc mới mở web
  const [tasks, setTasks] = useState([]);

  // 2. Tự động gọi API cổng 8000 để hút dữ liệu ngay khi web vừa tải xong
  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/v1/tasks")
      .then(res => res.json())
      .then(data => {
        if(Array.isArray(data)) setTasks(data);
      })
      .catch(err => console.error("Lỗi lấy dữ liệu từ Backend:", err));
  }, []);

  const [name, setName] = useState("");
  const [duration, setDuration] = useState(60);
  const [priority, setPriority] = useState(5);
  const [category, setCategory] = useState("Backend");
  const [deps, setDeps] = useState([]);

  const [timeline, setTimeline] = useState([]);

  // ==========================================
  // HÀM ADD TASK MỚI (LƯU THẲNG XUỐNG DATABASE)
  // ==========================================
  const addTask = async () => {
    if (!name) return;

    // 1. Đóng gói dữ liệu gửi lên Backend (KHÔNG TỰ TẠO ID NỮA, ĐỂ BACKEND LO)
    const payload = {
      name: name,
      priority: Number(priority),
      duration: Number(duration),
      dependencies: deps,
      category: category
    };

    try {
      // 2. Gọi API POST để lưu vào SQLite
      const response = await fetch("http://127.0.0.1:8000/api/v1/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      // 3. Xử lý lỗi (Ví dụ: Trùng tên, lỗi logic dependency...)
      if (!response.ok) {
        const errorData = await response.json();
        alert("❌ LỖI TỪ BACKEND:\n" + errorData.detail);
        return;
      }

      // 4. Nếu thành công, lấy Task thật (đã kèm ID xịn) từ Backend trả về và vẽ lên UI
      const savedTask = await response.json();
      setTasks([...tasks, savedTask]);

      // Reset Form
      setName("");
      setDuration(60);
      setPriority(5);
      setDeps([]);

    } catch (error) {
      console.error(error);
      alert("⚠️ Không thể kết nối với Backend. Hãy kiểm tra server!");
    }
  };

  // ==========================================
  // HÀM CLEAR ALL MỚI (XÓA SẠCH TRONG DATABASE)
  // ==========================================
  const clearAll = async () => {
    const confirmDelete = window.confirm("Bạn có chắc chắn muốn xóa TOÀN BỘ dữ liệu trong Database không?");
    if (!confirmDelete) return;

    try {
      // Bắn API gọi lệnh DELETE cho từng task hiện có
      for (const task of tasks) {
        await fetch(`http://127.0.0.1:8000/api/v1/tasks/${task.id}`, { 
          method: "DELETE" 
        });
      }
      // Dọn dẹp màn hình UI
      setTasks([]);
      setTimeline([]);
    } catch (error) {
      console.error(error);
      alert("⚠️ Lỗi khi xóa dữ liệu từ Backend!");
    }
  };

  // ==========================================
  // NHIỆM VỤ 1 CỦA M4: GỌI API BACKEND THẬT
  // ==========================================
  const runScheduler = async () => {
    try {
      // 1. Gửi lệnh chạy thuật toán Kahn sang Backend
      const response = await fetch("http://127.0.0.1:8000/api/v1/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ algorithm: "kahn", task_ids: [] }), 
      });

      // 2. Bắt lỗi chu trình (409) và hiển thị cảnh báo đỏ chót
      if (!response.ok) {
        const errorData = await response.json();
        alert("🛑 BACKEND BÁO LỖI:\n" + errorData.detail);
        return;
      }

      const data = await response.json();
      
      // 3. Ép kiểu dữ liệu của Backend (task_id) cho khớp với Frontend (id)
      const backendTimeline = data.schedule || [];
      const formattedTimeline = backendTimeline.map(t => ({
         id: t.task_id,
         name: t.task_name,
         start: t.start_time,
         end: t.end_time,
         duration: t.end_time - t.start_time,
         status: t.status,
         slack: t.slack ?? 0
      }));

      setTimeline(formattedTimeline);

      // 4. Đổi màu trạng thái trên đồ thị DAG
      const updatedTasks = tasks.map((t) => {
        const scheduled = formattedTimeline.find((r) => r.id === t.id);
        return scheduled ? { ...t, status: scheduled.status } : t;
      });
      setTasks(updatedTasks);

    } catch (error) {
      console.error(error);
      alert("⚠️ Mất kết nối! Hãy kiểm tra xem Backend cổng 8000 đã bật chưa.");
    }
  };

  // Metrics
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((t) => t.status === "COMPLETED").length;
  const makespan = timeline.length ? Math.max(...timeline.map(t => t.end)) : "--";
  const avgWaiting = timeline.length > 0
    ? Math.floor(timeline.reduce((a, b) => a + (b.start || 0), 0) / timeline.length)
    : "--";
  const criticalPathCount = timeline.filter(t => t.slack === 0).length;

  // ==========================================
  // NHIỆM VỤ 2 CỦA M4: CHUẨN BỊ DATA CHO REACT FLOW (DAG THẬT)
  // ==========================================
  const taskLevels = {};
  const taskMap = Object.fromEntries(tasks.map((task) => [task.id, task]));

  const computeLevel = (task) => {
    if (taskLevels[task.id] !== undefined) return taskLevels[task.id];
    if (!task.dependencies || task.dependencies.length === 0) {
      taskLevels[task.id] = 0;
      return 0;
    }

    const depLevels = task.dependencies.map((depId) => {
      const depTask = taskMap[depId];
      return depTask ? computeLevel(depTask) : 0;
    });

    const level = Math.max(...depLevels) + 1;
    taskLevels[task.id] = level;
    return level;
  };

  tasks.forEach(computeLevel);
  const levelCount = {};

  const reactFlowNodes = tasks.map((task) => {
    const level = taskLevels[task.id] ?? 0;
    const indexInLevel = levelCount[level] || 0;
    levelCount[level] = indexInLevel + 1;

    return {
      id: task.id,
      sourcePosition: 'right',
      targetPosition: 'left',
      position: { x: level * 260, y: indexInLevel * 140 + 40 },
      data: {
        label: (
          <div style={{ textAlign: "center" }}>
            <div style={{ fontWeight: 700 }}>{task.name}</div>
            <div style={{ fontSize: 11, opacity: 0.9 }}>P:{task.priority} | {task.duration}m</div>
          </div>
        )
      },
      style: {
        background: STATUS_COLORS[task.status] || STATUS_COLORS.PENDING,
        color: "white",
        border: "none",
        borderRadius: "12px",
        padding: "15px",
        width: 180,
        boxShadow: "0 4px 6px rgba(0,0,0,0.1)"
      }
    };
  });

  const reactFlowEdges = tasks.flatMap(task => 
    task.dependencies.map(dep => ({
      id: `e-${dep}-${task.id}`,
      source: dep,
      target: task.id,
      type: 'smoothstep', 
      animated: task.status === "RUNNING", 
      markerEnd: { type: MarkerType.ArrowClosed, color: '#fff' },
      style: { stroke: '#fff', strokeWidth: 2 }
    }))
  );
  
  return (
    <div className="dashboard">
      {/* SIDEBAR */}
      <div className="sidebar">
        <div className="logo">DSA Scheduler</div>
        <div className="subtitle">Realtime DAG & CPM Visualization</div>

        <div className="form-group">
          <label>TASK NAME</label>
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </div>

        <div className="form-group">
          <label>DURATION (m)</label>
          <input type="number" value={duration} onChange={(e) => setDuration(e.target.value)} />
        </div>

        <div className="form-group">
          <label>PRIORITY</label>
          <input type="number" min="1" max="10" value={priority} onChange={(e) => setPriority(e.target.value)} />
        </div>

        <div className="form-group">
          <label>CATEGORY</label>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option>Backend</option>
            <option>Frontend</option>
            <option>Database</option>
            <option>DevOps</option>
          </select>
        </div>

        <div className="form-group">
          <label>DEPENDENCIES</label>
          <select multiple className="dep-list" value={deps} onChange={(e) => setDeps([...e.target.selectedOptions].map((o) => o.value))}>
            {tasks.map((task) => (
              <option key={task.id} value={task.id}>{task.name}</option>
            ))}
          </select>
        </div>

        <button className="btn add-btn" onClick={addTask}>ADD TASK</button>
        <button className="btn run-btn" onClick={runScheduler}>RUN SCHEDULER</button>
        <button className="btn clear-btn" onClick={clearAll}>CLEAR ALL</button>
      </div>

      {/* RIGHT CONTENT */}
      <div className="content">
        
        {/* METRICS */}
        <div className="metrics">
          <div className="metric-card">
            <div className="metric-title">MAKESPAN</div>
            <div className="metric-value">{makespan}</div>
          </div>
          <div className="metric-card">
            <div className="metric-title">TOTAL TASKS</div>
            <div className="metric-value">{totalTasks}</div>
          </div>
          <div className="metric-card">
            <div className="metric-title">COMPLETED</div>
            <div className="metric-value">{completedTasks}</div>
          </div>
          <div className="metric-card">
            <div className="metric-title">AVG WAITING</div>
            <div className="metric-value">{avgWaiting}</div>
          </div>
          <div className="metric-card" style={{ border: criticalPathCount > 0 ? "1px solid #ff5252" : "none" }}>
            <div className="metric-title" style={{ color: criticalPathCount > 0 ? "#ff5252" : "inherit" }}>
              CRITICAL PATH (TASKS)
            </div>
            <div className="metric-value">{timeline.length ? criticalPathCount : "--"}</div>
          </div>
        </div>

        {/* STATUS LEGEND */}
        <div className="status-row">
          {Object.entries(STATUS_COLORS).map(([status, color]) => (
            <div key={status} className="status-item">
              <div className="dot" style={{ background: color }} />
              {status}
            </div>
          ))}
        </div>

        {/* REACT FLOW DAG GRAPH */}
        <div className="box" style={{ height: "350px", display: "flex", flexDirection: "column" }}>
          <h2>Dependency Graph (DAG)</h2>
          <div style={{ flex: 1, borderRadius: "14px", overflow: "hidden", border: "1px solid rgba(255,255,255,0.1)" }}>
            <ReactFlow nodes={reactFlowNodes} edges={reactFlowEdges} fitView>
              <Background color="rgba(255,255,255,0.2)" gap={16} />
              <Controls style={{ fill: "black" }} />
            </ReactFlow>
          </div>
        </div>

        {/* GANTT CHART */}
        <div className="timeline-box">
          <h2>Gantt Chart</h2>
          {timeline.length === 0 ? (
            <div style={{ opacity: 0.7, fontStyle: "italic", padding: "20px 0" }}>
              Biểu đồ sẽ xuất hiện sau khi gọi API...
            </div>
          ) : (
            <>
              <div className="gantt-header">
                {Array.from({ length: 20 }).map((_, i) => (
                  <div key={i} className="gantt-time">{i * 60}m</div>
                ))}
              </div>
              <div className="timeline-wrapper">
                {timeline.map((task) => (
                  <div key={task.id} className="timeline-row">
                    <div className="timeline-name">{task.name}</div>
                    <div className="timeline-track">
                      <div
                        className="timeline-bar"
                        style={{
                          left: `${task.start * 2}px`,
                          width: `${task.duration * 2}px`,
                          background: STATUS_COLORS[task.status] || STATUS_COLORS.COMPLETED,
                        }}
                      >
                        {task.name}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* ==========================================
            NHIỆM VỤ 3 CỦA M4: HIỂN THỊ ES, EF, SLACK (CPM) 
        ========================================== */}
        <div className="box schedule-output">
          <h2>CPM & Schedule Details</h2>
          {timeline.length === 0 ? (
            <div style={{ opacity: 0.7, fontStyle: "italic" }}>
              Đang chờ dữ liệu từ Backend...
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="schedule-table">
                <thead>
                  <tr>
                    <th>Task Name</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Start (ES)</th>
                    <th>Finish (EF)</th>
                    <th>Slack</th>
                  </tr>
                </thead>
                <tbody>
                  {timeline.map((task) => (
                    <tr 
                      key={task.id} 
                      style={{ 
                        // Highlight màu đỏ nhạt nếu Slack = 0 (thuộc đường găng)
                        background: task.slack === 0 ? "rgba(255, 82, 82, 0.15)" : "transparent",
                      }}
                    >
                      <td>{task.name} {task.slack === 0 && "🔥"}</td>
                      <td>{task.priority}</td>
                      <td>
                        <span className={`status-badge status-${task.status.toLowerCase()}`}>
                          {task.status}
                        </span>
                      </td>
                      <td>{task.start}m</td>
                      <td>{task.end}m</td>
                      <td>
                        <span style={{ 
                          color: task.slack === 0 ? "#ff5252" : "#00c853", 
                          fontWeight: "bold" 
                        }}>
                          {task.slack !== undefined ? `${task.slack}m` : "--"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
