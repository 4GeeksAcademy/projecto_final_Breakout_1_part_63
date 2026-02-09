import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";

export const TodoDetailTeacher = () => {
  const { id } = useParams();
  const backend = import.meta.env.VITE_BACKEND_URL;

  const [todo, setTodo] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setErr(null);

      try {
        const resp = await fetch(`${backend}/todos/${id}`, {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        });

        const data = await resp.json().catch(() => null);
        if (!resp.ok) throw new Error(data?.msg || "Error cargando la tarea");

        setTodo(data);
      } catch (e) {
        setErr(e.message);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [backend, id]);

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="fw-bold mb-0">Detalle de tarea</h2>
        <Link to="/homeTeacher" className="btn btn-outline-secondary">
          Volver
        </Link>
      </div>

      {loading && <p>Cargando...</p>}
      {err && <div className="alert alert-danger">{err}</div>}

      {todo && (
        <div className="card shadow-sm border-0 p-4">
          <h4 className="fw-bold">{todo.title}</h4>

          <p className="text-muted mb-2">
            <strong>Entrega:</strong> {todo.due_date}
          </p>

          <p className="mb-3">{todo.description || "Sin descripción"}</p>

          {todo.archive_url && (
            <a href={todo.archive_url} target="_blank" rel="noreferrer" className="btn btn-primary">
              Abrir archivo adjunto
            </a>
          )}
        </div>
      )}
    </div>
  );
};
