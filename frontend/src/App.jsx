import React, { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  BookOpenCheck,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Database,
  FileWarning,
  ListChecks,
  Play,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { api } from "./api";

const emptyResult = { columns: [], rows: [] };

function DataTable({ columns = [], rows = [], compact = false }) {
  if (!columns.length || !rows.length) {
    return <div className="emptyLine">暂无数据</div>;
  }
  return (
    <div className={compact ? "tableWrap compactTable" : "tableWrap"}>
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${index}-${JSON.stringify(row)}`}>
              {columns.map((column) => (
                <td key={column}>{row[column] === null || row[column] === undefined ? "" : String(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusBadge({ task }) {
  if (task?.passed) {
    return (
      <span className="statusBadge good">
        <CheckCircle2 size={14} /> 已通过
      </span>
    );
  }
  if (task?.attempts > 0) {
    return (
      <span className="statusBadge warn">
        <AlertCircle size={14} /> 待复盘
      </span>
    );
  }
  return <span className="statusBadge">未开始</span>;
}

function Drawer({ open, title, children, onClose }) {
  if (!open) return null;
  return (
    <div className="drawerLayer" role="dialog" aria-modal="true">
      <button className="drawerBackdrop" onClick={onClose} aria-label="关闭" />
      <aside className="drawer">
        <div className="drawerHeader">
          <h2>{title}</h2>
          <button className="iconButton" onClick={onClose} title="关闭">
            <X size={18} />
          </button>
        </div>
        {children}
      </aside>
    </div>
  );
}

function WrongNotesDrawer({ open, notes, onClose, onRefresh, onReviewed }) {
  return (
    <Drawer open={open} title="错题本" onClose={onClose}>
      <div className="drawerToolbar">
        <button className="ghostButton" onClick={onRefresh}>
          <RefreshCw size={16} /> 刷新
        </button>
      </div>
      <div className="noteList">
        {notes.length === 0 ? (
          <div className="emptyState">还没有错题。</div>
        ) : (
          notes.map((note) => (
            <article className={note.reviewed ? "note reviewed" : "note"} key={note.id}>
              <div className="noteTop">
                <span>Day {note.day}</span>
                <span>{note.mode}</span>
              </div>
              <h3>{note.task_title}</h3>
              <p>{note.problem}</p>
              <div className="noteMeta">{note.error_type || "unknown"}</div>
              {!note.reviewed && (
                <button className="smallButton" onClick={() => onReviewed(note.id)}>
                  标记复盘
                </button>
              )}
            </article>
          ))
        )}
      </div>
    </Drawer>
  );
}

function FeedbackDrawer({ open, result, conclusionResult, onClose }) {
  const output = result?.result || emptyResult;
  return (
    <Drawer open={open} title="运行反馈" onClose={onClose}>
      {!result && !conclusionResult && <div className="emptyState">运行后这里会显示反馈。</div>}
      {result && (
        <div className={result.passed ? "feedbackBox good" : "feedbackBox bad"}>
          <strong>{result.passed ? "通过" : "未通过"}</strong>
          <span>{result.feedback}</span>
          <small>{result.hint}</small>
        </div>
      )}
      {output.columns.length > 0 && (
        <div className="drawerSection">
          <h3>输出结果</h3>
          <DataTable columns={output.columns} rows={output.rows} />
        </div>
      )}
      {conclusionResult && (
        <div className={conclusionResult.passed ? "feedbackBox good" : "feedbackBox bad"}>
          <strong>
            业务结论 {conclusionResult.score}/{conclusionResult.max_score}
          </strong>
          <span>{conclusionResult.feedback}</span>
          <small>{conclusionResult.hint}</small>
        </div>
      )}
    </Drawer>
  );
}

function LibraryView({ days, summary, selectedDay, setSelectedDay, onEnterTask }) {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const selected = days.find((day) => day.day === selectedDay) || days[0];
  const statusCounts = useMemo(() => {
    const base = selected?.tasks || [];
    return {
      all: base.length,
      todo: base.filter((task) => !task.passed && !task.attempts).length,
      passed: base.filter((task) => task.passed).length,
      wrong: base.filter((task) => !task.passed && task.attempts > 0).length,
    };
  }, [selected]);
  const tasks = useMemo(() => {
    const base = selected?.tasks || [];
    const keyword = query.trim().toLowerCase();
    return base.filter((task) => {
      const matchesQuery = !keyword || `${task.title} ${task.mode}`.toLowerCase().includes(keyword);
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "todo" && !task.passed && !task.attempts) ||
        (statusFilter === "passed" && task.passed) ||
        (statusFilter === "wrong" && !task.passed && task.attempts > 0);
      return matchesQuery && matchesStatus;
    });
  }, [query, selected, statusFilter]);

  return (
    <main className="libraryPage">
      <section className="libraryHero">
        <div>
          <span className="eyebrow">Practice Library</span>
          <h1>选择一题进入练习</h1>
          <p>题库页只负责选题；进入练习后页面会切到单题工作台。</p>
        </div>
        <div className="summaryStrip">
          <div>
            <span>{summary.completed_count}</span>
            <small>已通过</small>
          </div>
          <div>
            <span>{summary.task_count}</span>
            <small>总任务</small>
          </div>
          <div>
            <span>{summary.wrong_note_count}</span>
            <small>待复盘</small>
          </div>
        </div>
      </section>

      <section className="dayChooser" aria-label="训练天数">
        {days.map((day) => {
          const progress = day.task_count ? Math.round((day.completed_count / day.task_count) * 100) : 0;
          return (
            <button
              key={day.day}
              className={day.day === selectedDay ? "dayTab active" : "dayTab"}
              onClick={() => setSelectedDay(day.day)}
            >
              <strong>Day {day.day}</strong>
              <span>{day.title}</span>
              <small>{progress}%</small>
            </button>
          );
        })}
      </section>

      <section className="taskLibrary">
        <div className="libraryHeader">
          <div>
            <h2>{selected?.title}</h2>
            <p>{selected?.focus}</p>
          </div>
          <label className="searchBox">
            <Search size={17} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索当前 Day 的题" />
          </label>
        </div>
        <div className="statusFilters" aria-label="题目状态筛选">
          {[
            ["all", "全部", statusCounts.all],
            ["todo", "未开始", statusCounts.todo],
            ["passed", "已通过", statusCounts.passed],
            ["wrong", "待复盘", statusCounts.wrong],
          ].map(([value, label, count]) => (
            <button
              key={value}
              className={statusFilter === value ? "statusFilter active" : "statusFilter"}
              onClick={() => setStatusFilter(value)}
            >
              {label}
              <span>{count}</span>
            </button>
          ))}
        </div>
        <div className="taskGrid">
          {tasks.map((task) => (
            <article
              className={
                task.passed
                  ? "taskCard passed"
                  : task.attempts > 0
                    ? "taskCard wrong"
                    : "taskCard todo"
              }
              key={task.id}
            >
              <div className="taskCardTop">
                <span className={task.mode === "sql" ? "modeBadge sql" : "modeBadge py"}>{task.mode.toUpperCase()}</span>
                <StatusBadge task={task} />
              </div>
              <h3>{task.title}</h3>
              <p>
                {task.timebox_minutes} 分钟
                {task.attempts > 0 && !task.passed ? ` · 已尝试 ${task.attempts} 次` : ""}
              </p>
              <button className="enterButton" onClick={() => onEnterTask(task.id)}>
                进入练习 <ChevronRight size={16} />
              </button>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

function FieldDictionary({ fieldDictionary }) {
  const tables = Object.entries(fieldDictionary || {});
  if (!tables.length) return null;
  return (
    <div className="stackList">
      {tables.map(([table, fields]) => (
        <div className="dataBlock" key={table}>
          <div className="tableName">{table}</div>
          <DataTable columns={["field", "type", "meaning"]} rows={fields} compact />
        </div>
      ))}
    </div>
  );
}

function SampleData({ sampleData }) {
  const tables = Object.entries(sampleData || {});
  if (!tables.length) return null;
  return (
    <div className="stackList">
      {tables.map(([table, rows]) => (
        <div className="dataBlock" key={table}>
          <div className="tableName">{table}</div>
          <DataTable columns={rows[0] ? Object.keys(rows[0]) : []} rows={rows} compact />
        </div>
      ))}
    </div>
  );
}

function PracticeView({
  taskDetail,
  currentTaskMeta,
  code,
  setCode,
  conclusion,
  setConclusion,
  activeInfoTab,
  setActiveInfoTab,
  runState,
  onRun,
  onBack,
  onOpenFeedback,
  onSubmitConclusion,
}) {
  if (!taskDetail) {
    return <main className="practicePage emptyState">正在加载题目。</main>;
  }
  const task = taskDetail.task;
  const infoTabs = [
    { id: "data", label: "数据预览", icon: ClipboardList },
    { id: "fields", label: "字段结构", icon: Database },
    { id: "brief", label: "题目要求", icon: BookOpenCheck },
  ];
  const hasFeedback = Boolean(runState.result);

  return (
    <main className="practicePage">
      <div className="practiceTopbar">
        <button className="backButton" onClick={onBack}>
          <ArrowLeft size={17} /> 返回题库
        </button>
        <div className="practiceTitle">
          <div className="taskMeta">
            <span>{task.mode.toUpperCase()}</span>
            <span>Day {task.day}</span>
            <span>{task.timebox_minutes} min</span>
          </div>
          <h1>{task.title}</h1>
        </div>
        <StatusBadge task={currentTaskMeta} />
      </div>

      <section className="promptBand">
        <div>
          <span className="eyebrow">Task Requirement</span>
          <p>{task.prompt}</p>
          {task.mysql_tip && <small>{task.mysql_tip}</small>}
        </div>
        {hasFeedback && (
          <button className={runState.result.passed ? "feedbackEntry good" : "feedbackEntry bad"} onClick={onOpenFeedback}>
            {runState.result.passed ? <CheckCircle2 size={17} /> : <AlertCircle size={17} />}
            查看反馈
          </button>
        )}
      </section>

      <section className="practiceWorkspace">
        <div className="infoPanel">
          <div className="infoTabs">
            {infoTabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  className={activeInfoTab === tab.id ? "infoTab active" : "infoTab"}
                  onClick={() => setActiveInfoTab(tab.id)}
                >
                  <Icon size={16} /> {tab.label}
                </button>
              );
            })}
          </div>
          <div className="infoBody">
            {activeInfoTab === "data" && <SampleData sampleData={taskDetail.sample_data} />}
            {activeInfoTab === "fields" && <FieldDictionary fieldDictionary={taskDetail.field_dictionary} />}
            {activeInfoTab === "brief" && (
              <div className="briefText">
                <h2>{task.objective}</h2>
                <p>{task.prompt}</p>
                <ul>
                  <li>输出列名和顺序要与题目要求一致。</li>
                  <li>可以使用不同写法，只要结果口径正确即可。</li>
                  <li>运行后可在反馈入口查看结果表和提示。</li>
                </ul>
              </div>
            )}
          </div>
        </div>

        <div className="workPanel">
          <div className="workPanelHeader">
            <div>
              <span className="eyebrow">Submission</span>
              <h2>{task.mode === "sql" ? "SQL 编辑区" : "Python solve(df)"}</h2>
            </div>
            <div className="workActions">
              <button className="ghostButton" onClick={onOpenFeedback} disabled={!hasFeedback}>
                <FileWarning size={16} /> 反馈
              </button>
              <button className="primaryButton" onClick={onRun} disabled={runState.loading}>
                <Play size={17} /> {runState.loading ? "运行中" : "运行评分"}
              </button>
            </div>
          </div>
          <textarea
            className={task.mode === "sql" ? "codeEditor sqlEditor" : "codeEditor"}
            value={code}
            onChange={(event) => setCode(event.target.value)}
            spellCheck={false}
          />
          <div className="conclusionPanel">
            <div className="conclusionHeader">
              <div>
                <span className="eyebrow">Business Output</span>
                <h3>业务结论</h3>
              </div>
              <button className="secondaryButton" onClick={onSubmitConclusion}>
                检查结论
              </button>
            </div>
            <textarea
              className="conclusionEditor"
              value={conclusion}
              onChange={(event) => setConclusion(event.target.value)}
              placeholder="发现... 原因可能... 建议..."
            />
          </div>
        </div>
      </section>
    </main>
  );
}

function App() {
  const [days, setDays] = useState([]);
  const [summary, setSummary] = useState({ task_count: 0, completed_count: 0, wrong_note_count: 0 });
  const [selectedDay, setSelectedDay] = useState(1);
  const [view, setView] = useState("library");
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [taskDetail, setTaskDetail] = useState(null);
  const [code, setCode] = useState("");
  const [conclusion, setConclusion] = useState("");
  const [conclusionResult, setConclusionResult] = useState(null);
  const [runState, setRunState] = useState({ loading: false, result: null, error: null });
  const [notes, setNotes] = useState([]);
  const [wrongNotesOpen, setWrongNotesOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [activeInfoTab, setActiveInfoTab] = useState("data");

  const currentTaskMeta = useMemo(() => {
    for (const day of days) {
      const found = day.tasks.find((task) => task.id === selectedTaskId);
      if (found) return found;
    }
    return null;
  }, [days, selectedTaskId]);

  async function loadDays() {
    const payload = await api.getDays();
    setDays(payload.days);
    setSummary(payload.summary);
  }

  async function loadNotes() {
    const payload = await api.getWrongNotes();
    setNotes(payload.notes);
  }

  useEffect(() => {
    loadDays().catch((error) => setRunState((state) => ({ ...state, error: error.message })));
    loadNotes().catch(() => {});
  }, []);

  async function enterTask(taskId) {
    setSelectedTaskId(taskId);
    setView("practice");
    setRunState({ loading: false, result: null, error: null });
    setConclusion("");
    setConclusionResult(null);
    setFeedbackOpen(false);
    setActiveInfoTab("data");
    const payload = await api.getTask(taskId);
    setTaskDetail(payload);
    setCode(payload.starter_code || "");
  }

  async function runCode() {
    if (!taskDetail) return;
    setRunState({ loading: true, result: null, error: null });
    try {
      const result = await api.runTask(taskDetail.task.id, code);
      setRunState({ loading: false, result, error: null });
      setFeedbackOpen(true);
      await loadDays();
      await loadNotes();
    } catch (error) {
      setRunState({ loading: false, result: null, error: error.message });
      setFeedbackOpen(true);
    }
  }

  async function submitConclusion() {
    if (!taskDetail) return;
    const result = await api.submitConclusion(taskDetail.task.id, conclusion);
    setConclusionResult(result);
    setFeedbackOpen(true);
  }

  async function markReviewed(noteId) {
    await api.markReviewed(noteId);
    await loadNotes();
    await loadDays();
  }

  function backToLibrary() {
    setView("library");
    setTaskDetail(null);
    setSelectedTaskId(null);
    setRunState({ loading: false, result: null, error: null });
    setFeedbackOpen(false);
  }

  return (
    <div className="appShell">
      <header className="topBar">
        <button className="brandButton" onClick={() => setView("library")}>
          <ListChecks size={21} />
          <span>本地机考训练器</span>
        </button>
        <nav className="topNav">
          <button className={view === "library" ? "navButton active" : "navButton"} onClick={() => setView("library")}>
            题库
          </button>
          <button className="navButton" onClick={() => setWrongNotesOpen(true)}>
            错题本 {summary.wrong_note_count > 0 ? summary.wrong_note_count : ""}
          </button>
          {view === "practice" && (
            <button className="navButton" onClick={() => setFeedbackOpen(true)}>
              反馈
            </button>
          )}
        </nav>
      </header>

      {view === "library" ? (
        <LibraryView
          days={days}
          summary={summary}
          selectedDay={selectedDay}
          setSelectedDay={setSelectedDay}
          onEnterTask={enterTask}
        />
      ) : (
        <PracticeView
          taskDetail={taskDetail}
          currentTaskMeta={currentTaskMeta}
          code={code}
          setCode={setCode}
          conclusion={conclusion}
          setConclusion={setConclusion}
          activeInfoTab={activeInfoTab}
          setActiveInfoTab={setActiveInfoTab}
          runState={runState}
          onRun={runCode}
          onBack={backToLibrary}
          onOpenFeedback={() => setFeedbackOpen(true)}
          onSubmitConclusion={submitConclusion}
        />
      )}

      <WrongNotesDrawer
        open={wrongNotesOpen}
        notes={notes}
        onClose={() => setWrongNotesOpen(false)}
        onRefresh={loadNotes}
        onReviewed={markReviewed}
      />
      <FeedbackDrawer
        open={feedbackOpen}
        result={runState.result || (runState.error ? { passed: false, feedback: runState.error, hint: "", result: emptyResult } : null)}
        conclusionResult={conclusionResult}
        onClose={() => setFeedbackOpen(false)}
      />
    </div>
  );
}

export default App;
