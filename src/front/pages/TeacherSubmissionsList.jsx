import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";

export const TeacherSubmissionsList = () => {
  const { todoId } = useParams();

  const [todo, setTodo] = useState(null);
  const [students, setStudents] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [statusBySubmissionId, setStatusBySubmissionId] = useState({});
  const [err, setErr] = useState(null);

  const [currentPage, setCurrentPage] = useState(1);
  const perPage = 10;

  const backendBase = (import.meta.env.VITE_BACKEND_URL || "").trim();

  useEffect(() => {
    const load = async () => {
      setErr(null);
      setTodo(null);
      setStudents([]);
      setSubmissions([]);
      setStatusBySubmissionId({});
      setCurrentPage(1);

      try {
        if (!backendBase) {
          throw new Error(
            "VITE_BACKEND_URL no está definido. En Codespaces poné la URL del backend (puerto 3001)."
          );
        }

        if (!todoId) {
          throw new Error("Falta todoId en la URL. Ej: /teachersubmissionslist/1");
        }

        const token = localStorage.getItem("token");

        const todoResp = await fetch(`${backendBase}/todos/${todoId}`);
        const todoData = await todoResp.json().catch(() => ({}));
        if (!todoResp.ok) throw new Error(todoData?.msg || "Error al cargar la tarea");
        setTodo(todoData);

        if (!todoData.group_id) {
          throw new Error("La tarea no tiene group_id (no se puede listar alumnos).");
        }

        const studentsResp = await fetch(
          `${backendBase}/groups/${todoData.group_id}/students`,
          {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          }
        );
        const studentsData = await studentsResp.json().catch(() => ({}));
        if (!studentsResp.ok) {
          throw new Error(studentsData?.msg || "Error al cargar alumnos del grupo");
        }
        setStudents(Array.isArray(studentsData) ? studentsData : []);

        const subResp = await fetch(`${backendBase}/submissions?todo_id=${todoId}`);
        const subData = await subResp.json().catch(() => ({}));
        if (!subResp.ok) throw new Error(subData?.msg || "Error al cargar entregas");

        const subs = Array.isArray(subData.submissions) ? subData.submissions : [];
        setSubmissions(subs);

        const statusMap = {};
        await Promise.all(
          subs.map(async (s) => {
            try {
              const r = await fetch(`${backendBase}/submissions/${s.id}/status`);
              if (!r.ok) return;
              const st = await r.json().catch(() => null);
              if (st) statusMap[s.id] = st;
            } catch {}
          })
        );
        setStatusBySubmissionId(statusMap);
      } catch (e) {
        setErr(e.message || "Error inesperado");
      }
    };

    load();
  }, [todoId, backendBase]);

  const rows = useMemo(() => {
    const subByStudentId = new Map();
    for (const s of submissions) subByStudentId.set(String(s.student_id), s);

    return students.map((st) => {
      const sub = subByStudentId.get(String(st.user_id)) || null;
      const status = sub ? statusBySubmissionId[sub.id] : null;

      return {
        user_id: st.user_id,
        name: st.name,
        email: st.email,
        submission: sub,
        state: status?.state || (sub ? "entregado" : "pendiente"),
        feedback: status?.feedback || "",
      };
    });
  }, [students, submissions, statusBySubmissionId]);

  const totalPages = Math.ceil(rows.length / perPage);
  const currentRows = useMemo(() => {
    const start = (currentPage - 1) * perPage;
    return rows.slice(start, start + perPage);
  }, [rows, currentPage]);

  if (err) return <div className="container mt-5 alert alert-danger">{err}</div>;
  if (!todo) return <div className="container mt-5">Cargando...</div>;

  return (
    <div className="container mt-4">
      <div className="mb-3">
        <h4 className="mb-1">Entregas / {todo.title}</h4>
        <div className="text-muted small">
          Grupo {todo.group_id} · {rows.length} alumnos
        </div>
      </div>

      <div className="list-group">
        {currentRows.map((r) => (
          <div
            key={r.user_id}
            className="list-group-item d-flex justify-content-between align-items-center"
          >
            <div className="me-3">
              <div className="fw-semibold">{r.name}</div>
              <div className="text-muted small">{r.email}</div>
            </div>

            <div className="d-flex align-items-center gap-3">
              <span
                className={`badge ${
                  r.state === "pendiente" ? "bg-secondary" : "bg-success"
                }`}
              >
                {r.state}
              </span>

              {r.submission ? (
                <Link
                  to={`/teacher/submissions/review/${todoId}/${r.submission.id}`}
                  className="btn btn-sm btn-primary"
                >
                  Corregir
                </Link>
              ) : (
                <button className="btn btn-sm btn-outline-secondary" disabled>
                  Sin entrega
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="d-flex justify-content-center mt-3 mb-3">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <button
              key={page}
              className={`btn me-2 ${
                page === currentPage ? "btn-dark" : "btn-outline-dark"
              }`}
              onClick={() => setCurrentPage(page)}
            >
              {page}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
