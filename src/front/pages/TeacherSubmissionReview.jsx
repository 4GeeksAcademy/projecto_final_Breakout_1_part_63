import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import useGlobalReducer from "../hooks/useGlobalReducer.jsx";

export const TeacherSubmissionReview = () => {
  const { store } = useGlobalReducer();
  const { todoId, submissionId } = useParams();

  const backend = (import.meta.env.VITE_BACKEND_URL || "").trim();
  const token = localStorage.getItem("token");

  const [todo, setTodo] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [students, setStudents] = useState([]);

  const [status, setStatus] = useState(null);
  const [stateValue, setStateValue] = useState("pendiente");
  const [feedback, setFeedback] = useState("");

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const role = store?.role;

  const authHeaders = useMemo(() => {
    return {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }, [token]);

  const mapStateToBackend = (uiState) => {
    const m = {
      pendiente: "PENDING",
      aprobado: "APPROVED",
      rechazado: "REJECTED",
    };
    return m[uiState] || "PENDING";
  };

  const mapStateToUI = (apiState) => {
    const s = String(apiState || "").toUpperCase();
    if (s === "APPROVED") return "aprobado";
    if (s === "REJECTED") return "rechazado";
    return "pendiente";
  };

  const safeReadJsonOrTextError = async (resp) => {
    const ct = resp.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const data = await resp.json().catch(() => null);
      return { json: data, text: null };
    }
    const text = await resp.text().catch(() => "");
    return { json: null, text };
  };

  const getTeacherId = () => {
    const u = store?.user;
    const id =
      u?.id ??
      u?.user_id ??
      u?.uid ??
      (typeof window !== "undefined" ? localStorage.getItem("user_id") : null);
    return id ? Number(id) : null;
  };

  const studentById = useMemo(() => {
    const m = new Map();
    (students || []).forEach((st) => m.set(String(st.user_id), st));
    return m;
  }, [students]);

  const student = useMemo(() => {
    if (!submission) return null;
    return studentById.get(String(submission.student_id)) || null;
  }, [submission, studentById]);

  useEffect(() => {
    const load = async () => {
      setErr(null);
      setLoading(true);

      try {
        if (!backend) throw new Error("VITE_BACKEND_URL no está definido.");
        if (!todoId) throw new Error("Falta todoId en la URL.");
        if (!submissionId) throw new Error("Falta submissionId en la URL.");

        const todoResp = await fetch(`${backend}/todos/${todoId}`);
        const todoParsed = await safeReadJsonOrTextError(todoResp);

        if (!todoResp.ok) {
          const msg = todoParsed.json?.msg || todoParsed.text || "Error al cargar tarea";
          throw new Error(msg);
        }
        const todoData = todoParsed.json;
        setTodo(todoData);

        const listResp = await fetch(`${backend}/submissions?todo_id=${todoId}`);
        const listParsed = await safeReadJsonOrTextError(listResp);

        if (!listResp.ok) {
          const msg = listParsed.json?.msg || listParsed.text || "Error al cargar entregas";
          throw new Error(msg);
        }

        const list = Array.isArray(listParsed.json?.submissions)
          ? listParsed.json.submissions
          : [];

        const found = list.find((s) => String(s.id) === String(submissionId)) || null;
        if (!found) throw new Error("No se encontró la entrega para esta tarea.");
        setSubmission(found);

        if (todoData?.group_id) {
          const studentsResp = await fetch(`${backend}/groups/${todoData.group_id}/students`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          });

          const studentsParsed = await safeReadJsonOrTextError(studentsResp);

          if (!studentsResp.ok) {
            const msg =
              studentsParsed.json?.msg ||
              studentsParsed.text ||
              "Error al cargar alumnos del grupo";
            throw new Error(msg);
          }

          setStudents(Array.isArray(studentsParsed.json) ? studentsParsed.json : []);
        } else {
          setStudents([]);
        }

        const stResp = await fetch(`${backend}/submissions/${submissionId}/status`);
        const stParsed = await safeReadJsonOrTextError(stResp);

        if (!stResp.ok) {
          setStatus(null);
          setStateValue("pendiente");
          setFeedback("");
        } else {
          setStatus(stParsed.json);
          setStateValue(mapStateToUI(stParsed.json?.state));
          setFeedback(stParsed.json?.feedback || "");
        }
      } catch (e) {
        setErr(e.message || "Error inesperado");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [backend, todoId, submissionId, token]);

  const saveReview = async () => {
    setErr(null);

    try {
      if (!backend) throw new Error("VITE_BACKEND_URL no está definido.");
      if (!submissionId) throw new Error("Falta submissionId.");

      const teacherId = getTeacherId();
      if (!teacherId) throw new Error("No se encontró el ID del docente.");

      const payload = {
        submission_id: Number(submissionId),
        teacher_id: teacherId,
        state: mapStateToBackend(stateValue),
        feedback: feedback,
      };

      if (status?.id) {
        const putResp = await fetch(`${backend}/statuses/${status.id}`, {
          method: "PUT",
          headers: authHeaders,
          body: JSON.stringify(payload),
        });

        const putParsed = await safeReadJsonOrTextError(putResp);

        if (!putResp.ok) {
          const msg =
            putParsed.json?.msg ||
            putParsed.text ||
            `Error actualizando calificación (${putResp.status})`;
          throw new Error(msg);
        }
      } else {
        const postResp = await fetch(`${backend}/statuses/1`, {
          method: "POST",
          headers: authHeaders,
          body: JSON.stringify(payload),
        });

        const postParsed = await safeReadJsonOrTextError(postResp);

        if (!postResp.ok) {
          const msg =
            postParsed.json?.msg ||
            postParsed.text ||
            `Error creando calificación (${postResp.status})`;
          throw new Error(msg);
        }
      }

      const stResp = await fetch(`${backend}/submissions/${submissionId}/status`);
      const stParsed = await safeReadJsonOrTextError(stResp);

      if (stResp.ok) {
        setStatus(stParsed.json);
        setStateValue(mapStateToUI(stParsed.json?.state));
        setFeedback(stParsed.json?.feedback || "");
      }

      alert("Calificación guardada ✅");
    } catch (e) {
      setErr(e.message || "Error guardando calificación");
    }
  };

  if (loading) return <div className="container mt-5">Cargando...</div>;

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-start gap-3 mb-3">
        <div>
          <h2 className="mb-1">Revisión de entrega</h2>
         
        </div>

        {role && (
          <span className="badge bg-secondary align-self-center">Rol: {role}</span>
        )}
      </div>

      {err && <div className="alert alert-danger">{err}</div>}

      <div className="card shadow-sm mb-4">
        <div className="card-body">
          <div className="mb-3">
            <h5 className="mb-2">Tarea</h5>
            <div>
              <strong>Título:</strong> {todo?.title || "—"}
            </div>
            <div className="mt-1">
              <strong>Vencimiento:</strong>{" "}
              {todo?.due_date ? new Date(todo.due_date).toLocaleString() : "—"}
            </div>
            <div className="mt-2">
              <strong>Descripción:</strong>
            </div>
            <div className="text-muted">{todo?.description || "—"}</div>
          </div>

          <hr />

          <div className="mb-3">
            <h5 className="mb-2">Alumno</h5>
            <div>
              <strong>Nombre:</strong>{" "}
              {student?.name ||
                (submission?.student_id ? `Alumno #${submission.student_id}` : "—")}
            </div>
            <div className="mt-1">
              <strong>Email:</strong> {student?.email || "—"}
            </div>
          </div>

          <hr />

          <div>
            <h5 className="mb-2">Entrega</h5>

            <div className="mt-2">
              <strong>Descripción:</strong>
            </div>
            <div className="text-muted">{submission?.description || "—"}</div>

            <div className="mt-2">
              <strong>Link:</strong>
            </div>
            {submission?.response_url ? (
              <a href={submission.response_url} target="_blank" rel="noreferrer">
                Abrir entrega
              </a>
            ) : (
              <div className="text-muted">—</div>
            )}
          </div>
        </div>
      </div>

      <div className="card shadow-sm mb-5">
        <div className="card-body">
          <h5 className="mb-3">Corrección</h5>

          <div className="row g-3">
            <div className="col-md-4">
              <label className="form-label">Estado</label>
              <select
                className="form-select"
                value={stateValue}
                onChange={(e) => setStateValue(e.target.value)}
              >
                <option value="pendiente">Pendiente</option>
                <option value="aprobado">Aprobado</option>
                <option value="rechazado">Rechazado</option>
              </select>
              <div className="form-text">
                {status?.id ? "Calificación existente" : "Sin calificación aún"}
              </div>
            </div>

            <div className="col-md-8">
              <label className="form-label">Devolución</label>
              <textarea
                className="form-control"
                rows={4}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Escribí comentarios para el alumno..."
              />
            </div>
          </div>

          <div className="d-flex gap-2 mt-3">
            <button className="btn btn-primary" onClick={saveReview}>
              Guardar calificación
            </button>

            <button
              className="btn btn-outline-secondary"
              onClick={() => {
                setStateValue(mapStateToUI(status?.state));
                setFeedback(status?.feedback || "");
              }}
            >
              Revertir cambios
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
