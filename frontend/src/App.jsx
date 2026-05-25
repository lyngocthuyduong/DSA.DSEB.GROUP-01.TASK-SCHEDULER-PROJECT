import "./App.css";
import { useState } from "react";

const STATUS_COLORS = {
  PENDING: "#9e9e9e",
  READY: "#2979ff",
  RUNNING: "#ff9800",
  COMPLETED: "#00c853",
  BLOCKED: "#ff5252",
};

export default function App() {
  const [tasks, setTasks] = useState([
    {
      id: "task_1",
      name: "Database Design",
      priority: 8,
      duration: 120,
      dependencies: [],
      status: "COMPLETED",
      category: "Database",
    },

    {
      id: "task_2",
      name: "Backend API",
      priority: 7,
      duration: 180,
      dependencies: ["task_1"],
      status: "READY",
      category: "Backend",
    },

    {
      id: "task_3",
      name: "Frontend Integration",
      priority: 6,
      duration: 90,
      dependencies: ["task_2"],
      status: "PENDING",
      category: "Frontend",
    },
  ]);

  const [name, setName] = useState("");
  const [duration, setDuration] = useState(60);
  const [priority, setPriority] = useState(5);
  const [category, setCategory] = useState("Backend");
  const [deps, setDeps] = useState([]);

  const [timeline, setTimeline] = useState([]);

  const addTask = () => {
    if (!name) return;

    const newTask = {
      id: `task_${tasks.length + 1}`,
      name,
      priority: Number(priority),
      duration: Number(duration),
      dependencies: deps,
      status: "PENDING",
      category,
    };

    setTasks([...tasks, newTask]);

    setName("");
    setDuration(60);
    setPriority(5);
    setDeps([]);
  };

  const clearAll = () => {
    setTasks([]);
    setTimeline([]);
  };

  const runScheduler = () => {
    let currentTime = 0;

    const sorted = [...tasks].sort((a, b) => {
      if (b.priority !== a.priority)
        return b.priority - a.priority;

      if (a.duration !== b.duration)
        return a.duration - b.duration;

      return a.id.localeCompare(b.id);
    });

    const result = sorted.map((task) => {
      const start = currentTime;

      const end = start + task.duration;

      currentTime = end;

      return {
        ...task,
        start,
        end,
        status: "COMPLETED",
      };
    });

    setTasks(result);
    setTimeline(result);
  };

  const totalTasks = tasks.length;

  const completedTasks = tasks.filter(
    (t) => t.status === "COMPLETED"
  ).length;

  const makespan = timeline.length
    ? timeline[timeline.length - 1].end
    : "--";

  const avgWaiting =
    timeline.length > 0
      ? Math.floor(
          timeline.reduce(
            (a, b) => a + b.start,
            0
          ) / timeline.length
        )
      : "--";

  return (
    <div className="dashboard">

      {/* SIDEBAR */}

      <div className="sidebar">

        <div className="logo">
          DSA Scheduler
        </div>

        <div className="subtitle">
          DAG + Kahn Algorithm +
          Priority Queue Visualization
        </div>

        <div className="form-group">
          <label>TASK NAME</label>

          <input
            value={name}
            onChange={(e) =>
              setName(e.target.value)
            }
          />
        </div>

        <div className="form-group">
          <label>DURATION</label>

          <input
            type="number"
            value={duration}
            onChange={(e) =>
              setDuration(e.target.value)
            }
          />
        </div>

        <div className="form-group">
          <label>PRIORITY</label>

          <input
            type="number"
            min="1"
            max="10"
            value={priority}
            onChange={(e) =>
              setPriority(e.target.value)
            }
          />
        </div>

        <div className="form-group">
          <label>CATEGORY</label>

          <select
            value={category}
            onChange={(e) =>
              setCategory(e.target.value)
            }
          >
            <option>Backend</option>
            <option>Frontend</option>
            <option>Database</option>
            <option>DevOps</option>
          </select>
        </div>

        <div className="form-group">
          <label>DEPENDENCIES</label>

          <select
            multiple
            className="dep-list"
            value={deps}
            onChange={(e) =>
              setDeps(
                [...e.target.selectedOptions].map(
                  (o) => o.value
                )
              )
            }
          >
            {tasks.map((task) => (
              <option
                key={task.id}
                value={task.id}
              >
                {task.name}
              </option>
            ))}
          </select>
        </div>

        <button
          className="btn add-btn"
          onClick={addTask}
        >
          ADD TASK
        </button>

        <button
          className="btn run-btn"
          onClick={runScheduler}
        >
          RUN SCHEDULER
        </button>

        <button
          className="btn clear-btn"
          onClick={clearAll}
        >
          CLEAR ALL
        </button>

        <div className="task-list">

          {tasks.map((task) => (
            <div
              key={task.id}
              className="task-card"
            >
              <div className="task-title">
                {task.name}
              </div>

              <div>
                Priority: {task.priority}
              </div>

              <div>
                Duration: {task.duration}m
              </div>

              <div>
                Status: {task.status}
              </div>
            </div>
          ))}

        </div>

      </div>

      {/* RIGHT */}

      <div className="content">

        {/* METRICS */}

        <div className="metrics">

          <div className="metric-card">
            <div className="metric-title">
              MAKESPAN
            </div>

            <div className="metric-value">
              {makespan}
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-title">
              TOTAL TASKS
            </div>

            <div className="metric-value">
              {totalTasks}
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-title">
              COMPLETED
            </div>

            <div className="metric-value">
              {completedTasks}
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-title">
              AVG WAITING
            </div>

            <div className="metric-value">
              {avgWaiting}
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-title">
              CRITICAL PATH
            </div>

            <div className="metric-value">
              {timeline.length}
            </div>
          </div>

        </div>

        {/* STATUS */}

        <div className="status-row">

          {Object.entries(
            STATUS_COLORS
          ).map(([status, color]) => (
            <div
              key={status}
              className="status-item"
            >
              <div
                className="dot"
                style={{
                  background: color,
                }}
              />

              {status}
            </div>
          ))}

        </div>

        {/* DAG */}

        <div className="graph-section">
  <h2>Dependency Graph</h2>

  <div className="dag-container">

    {tasks.map((task, index) => (
      <div key={task.id} className="dag-row">

        <div
          className={`dag-node ${
            task.status === "COMPLETED"
              ? "node-completed"
              : task.status === "RUNNING"
              ? "node-running"
              : task.status === "READY"
              ? "node-ready"
              : task.status === "BLOCKED"
              ? "node-blocked"
              : "node-pending"
          }`}
        >
          <div className="dag-title">{task.name}</div>

          <div className="dag-info">
            Priority: {task.priority}
          </div>

          <div className="dag-info">
            Duration: {task.duration}m
          </div>

          <div className="dag-info">
            Status: {task.status}
          </div>
        </div>

        {index !== tasks.length - 1 && (
          <div className="dag-arrow">
            →
          </div>
        )}
      </div>
    ))}

  </div>
</div>

        {/* PRIORITY QUEUE */}

        <div className="box">

          <h2>Priority Queue</h2>

          <div className="queue">

            {[...tasks]
              .sort(
                (a, b) =>
                  b.priority -
                  a.priority
              )
              .map((task) => (
                <div
                  key={task.id}
                  className="queue-item"
                >
                  {task.name}
                  {" "}
                  (P:
                  {task.priority})
                </div>
              ))}

          </div>

        </div>

        {/* EXECUTION */}

        <div className="box">

          <h2>Execution Order</h2>

          <div className="execution">

            {timeline.map((task) => (
              <div
                key={task.id}
                className="execution-item"
              >
                {task.name}
              </div>
            ))}

          </div>

        </div>

        {/* GANTT */}

        <div className="timeline-box">
  <h2>Gantt Chart</h2>
  
  {timeline.length === 0 ? (
    <div style={{ opacity: 0.7, fontStyle: "italic", padding: "20px 0" }}>
      Biểu đồ sẽ xuất hiện sau khi chạy thuật toán...
    </div>
  ) : (
    <>
      <div className="gantt-header">
        {Array.from({ length: 20 }).map((_, i) => (
          <div key={i} className="gantt-time">
            {i * 60}m
          </div>
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
                  left: `${task.start * 2}px`, /* Đổi marginLeft thành left để định vị tuyệt đối */
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
<div className="schedule-output">
  <h2>Schedule Output</h2>
  
  {timeline.length === 0 ? (
    <div style={{ opacity: 0.7, fontStyle: "italic" }}>
      Chưa có lịch trình. Vui lòng ấn "RUN SCHEDULER"...
    </div>
  ) : (
    <table className="schedule-table">
      <thead>
        <tr>
          <th>Task Name</th>
          <th>Priority</th>
          <th>Status</th>
          <th>Start Time</th>
          <th>End Time</th>
        </tr>
      </thead>
      <tbody>
        {timeline.map((task) => (
          <tr key={task.id}>
            <td>{task.name}</td>
            <td>{task.priority}</td>
            <td>
              <span className={`status-badge status-${task.status.toLowerCase()}`}>
                {task.status}
              </span>
            </td>
            <td>{task.start}m</td>
            <td>{task.end}m</td>
          </tr>
        ))}
      </tbody>
    </table>
  )}
</div>
      </div>

    </div>
  );
}