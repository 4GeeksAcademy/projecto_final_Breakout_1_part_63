import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import SubirArchivo from "../components/UploadFiles";

const decodeJwtPayload = (token) => {
  try {
    const payload = token.split(".")[1];
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(json);
  } catch {
    return null;
  }
};

export const CreateTodoForm = () => {
  const backend = import.meta.env.VITE_BACKEND_URL;
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");
  const navigate = useNavigate();

  const jwtPayload = useMemo(() => (token ? decodeJwtPayload(token) : null), [token]);
  const teacherId = jwtPayload?.sub || jwtPayload?.identity || null;

  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [groupId, setGroupId] = useState("");
  const [description, setDescription] = useState("");
  const [archiveUrl, setArchiveUrl] = useState(null);
  const [uploading, setUploading] = useState(false);

  const [groups, setGroups] = useState([]);
  const [students, setStudents] = useState([]);

  const [loadingGroups, setLoadingGroups] = useState(false);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [okMsg, setOkMsg] = useState(null);
  const [studentSearch, setStudentSearch] = useState("");
  const teacherName = localStorage.getItem("user_name") || "Profesor";

  const authHeaders = useMemo(() => {
    const h = { "Content-Type": "application/json" };
    if (token) h.Authorization = `Bearer ${token}`;
    return h;
  }, [token]);

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    if (role !== "TEACHER" && role !== "ADMIN") {
      navigate("/login");
      return;
    }
  }, [token, role, navigate]);

  useEffect(() => {
    const loadGroups = async () => {
      setLoadingGroups(true);
      setErrorMsg(null);

      try {
        const resp = await fetch(`${backend}/groups`, {
          method: "GET",
          headers: authHeaders,
        });

        const data = await resp.json().catch(() => null);
        if (!resp.ok) throw new Error(data?.msg || "Error cargando grupos");

        const arr = Array.isArray(data) ? data : [];
        setGroups(arr);

        if (!groupId && arr.length > 0) setGroupId(String(arr[0].id));
      } catch (e) {
        setErrorMsg(e.message);
      } finally {
        setLoadingGroups(false);
      }
    };

    if (backend && token) loadGroups();
  }, [backend, token, authHeaders]);

  useEffect(() => {
    const loadStudents = async () => {
      setStudents([]);
      setStudentSearch("");

      if (!groupId) return;

      setLoadingStudents(true);
      setErrorMsg(null);

      try {
        const resp = await fetch(`${backend}/groups/${groupId}/students`, {
          method: "GET",
          headers: authHeaders,
        });

        const data = await resp.json().catch(() => null);
        if (!resp.ok) throw new Error(data?.msg || "Error cargando alumnos del grupo");

        setStudents(Array.isArray(data) ? data : []);
      } catch (e) {
        setErrorMsg(e.message);
      } finally {
        setLoadingStudents(false);
      }
    };

    if (backend && token) loadStudents();
  }, [backend, token, groupId, authHeaders]);

  const filteredStudents = useMemo(() => {
    const q = studentSearch.trim().toLowerCase();
    if (!q) return students;
    return students.filter((s) =>
      `${s.name || ""} ${s.email || ""}`.toLowerCase().includes(q)
    );
  }, [students, studentSearch]);

  const resetAlerts = () => {
    setErrorMsg(null);
    setOkMsg(null);
  };

  const formatForBackendISO = (dtLocal) => {
    return dtLocal;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    resetAlerts();

    if (!title.trim() || !dueDate || !groupId) {
      setErrorMsg("Completá título, fecha de entrega y grupo.");
      return;
    }

    const payload = {
      title: title.trim(),
      description: description?.trim() || "",
      due_date: formatForBackendISO(dueDate),
      group_id: Number(groupId),
      archive_url: archiveUrl || null,
    };

    try {
      const resp = await fetch(`${backend}/teacher/todos`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(payload),
      });

      const data = await resp.json().catch(() => null);
      if (!resp.ok) throw new Error(data?.msg || "Error creando tarea");

      setOkMsg("✅ Tarea creada y enviada al calendario");
      setTitle("");
      setDueDate("");
      setDescription("");
      setArchiveUrl(null);
    } catch (e2) {
      setErrorMsg(e2.message);
    }
  };

  const tileClassByIndex = (i) => {
    const options = ["tile-teal", "tile-sand", "tile-blue", "tile-pink"];
    return options[i % options.length];
  };

  return (
    <div className="page-teacher-todos">
      <div className="container-fluid">
        <div className="row g-0">
          <aside className="col-12 col-lg-3 sidebar-left">
            <div className="sidebar-inner">
              <div className="sidebar-header">
                <div
                  className="back-pill"
                  role="button"
                  aria-label="Volver"
                  title="Volver"
                  onClick={() => navigate(-1)}
                >
                  ←
                </div>

                <div>
                  <div className="sidebar-title">
                    Bienvenido, <strong>{teacherName}</strong>
                  </div>
                </div>
              </div>

              <div className="sidebar-section">
                <div className="section-title">Grupos</div>

                {loadingGroups ? (
                  <div className="text-muted small">Cargando grupos...</div>
                ) : groups.length === 0 ? (
                  <div className="text-muted small">No hay grupos para mostrar.</div>
                ) : (
                  <div className="tiles-list">
                    {groups.map((g, idx) => (
                      <button
                        key={g.id}
                        type="button"
                        className={`tile ${tileClassByIndex(idx)} ${String(groupId) === String(g.id) ? "tile-selected" : ""
                          }`}
                        onClick={() => setGroupId(String(g.id))}
                      >
                        {g.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="sidebar-section">
                <div className="section-title">Participantes</div>

                <input
                  className="form-control search-input"
                  placeholder="Buscar alumno..."
                  value={studentSearch}
                  onChange={(e) => setStudentSearch(e.target.value)}
                  disabled={!groupId || loadingStudents}
                />

                {loadingStudents ? (
                  <div className="text-muted small">Cargando participantes...</div>
                ) : !groupId ? (
                  <div className="text-muted small">Seleccioná un grupo arriba.</div>
                ) : filteredStudents.length === 0 ? (
                  <div className="text-muted small">No hay alumnos en este grupo.</div>
                ) : (
                  <div className="tiles-list">
                    {filteredStudents.map((s, idx) => (
                      <div
                        key={s.user_id}
                        className={`tile ${tileClassByIndex(idx)} tile-soft`}
                        title={s.email}
                      >
                        {s.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </aside>

          <main className="col-12 col-lg-9 main-right">
            <div className="main-header">
              <div className="main-header-inner main-header-inner--todo">
                <h1 className="header-title">Generador de tareas</h1>
                <div className="header-subtitle">Curso: Desarrollo Web</div>
              </div>
            </div>

            <div className="main-content main-content--todo">
              {(errorMsg || okMsg) && (
                <div className="mb-3">
                  {errorMsg && <div className="alert alert-danger mb-2">{errorMsg}</div>}
                  {okMsg && <div className="alert alert-success mb-0">{okMsg}</div>}
                </div>
              )}

              <div className="soft-card">
                <div className="card-body">
                  <h4 className="mb-2 fw-bold" style={{ color: "var(--c-navy)" }}>
                    Crear nueva tarea
                  </h4>
                  <p className="text-muted small mb-4">
                    En esta sección podrás crear una nueva tarea. Recordá asignarla a un grupo,
                    definir la fecha de entrega y adjuntar un archivo si corresponde.
                  </p>

                  <form onSubmit={handleSubmit}>
                    <div className="mb-3">
                      <label className="form-label fw-semibold">Título</label>
                      <input
                        className="form-control ctf-input"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Título de tarea"
                        required
                      />
                    </div>

                    <div className="mb-3">
                      <label className="form-label fw-semibold">Plazo de entrega</label>
                      <input
                        type="datetime-local"
                        className="form-control ctf-input"
                        value={dueDate}
                        onChange={(e) => setDueDate(e.target.value)}
                        required
                      />
                    </div>

                    <div className="mb-3">
                      <label className="form-label fw-semibold">Grupos</label>
                      <select
                        className="form-select ctf-input"
                        value={groupId}
                        onChange={(e) => setGroupId(e.target.value)}
                        required
                      >
                        {groups.length === 0 && <option value="">(sin grupos)</option>}
                        {groups.map((g) => (
                          <option key={g.id} value={g.id}>
                            {g.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="mb-3">
                      <label className="form-label fw-semibold">Descripción</label>
                      <textarea
                        className="form-control ctf-input"
                        rows={6}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Agregar descripción de la tarea"
                      />
                    </div>

                    <div className="mb-4">
                      <label className="form-label fw-semibold">Archivo</label>

                      <div className="d-flex align-items-center gap-3 flex-wrap">
                        <SubirArchivo onUpload={setArchiveUrl} setUploading={setUploading} />

                        {archiveUrl ? (
                          <span className="text-success fw-semibold">Archivo adjunto ✔</span>
                        ) : (
                          <span className="text-muted small">
                            (Opcional) Adjuntá un archivo antes de subir la tarea.
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="d-flex justify-content-end">
                      <button
                        type="submit"
                        className="btn btn-create px-4"
                        disabled={uploading}
                      >
                        {uploading ? "Subiendo archivo..." : "Subir tarea"}
                      </button>
                    </div>
                  </form>
                </div>
              </div>

              <div className="py-3" />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};
