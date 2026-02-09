import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import useGlobalReducer from "../hooks/useGlobalReducer.jsx";
import UploadFiles from "../components/UploadFiles.jsx";

export const CreateReadings = () => {
  const { store, dispatch } = useGlobalReducer();
  const params = useParams();
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [group, setGroup] = useState("");
  const [teacher, setTeacher] = useState("");
  const [readingUrl, setReadingUrl] = useState("");
  const [uploading, setUploading] = useState(false);

  const [err, setErr] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (params.groupId) {
      setGroup(params.groupId);
    }
  }, [params.groupId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading || uploading) return;

    setErr(null);
    setSuccess(null);
    setLoading(true);

    try {
      const backend = import.meta.env.VITE_BACKEND_URL;

      const body = {
        title,
        content,
        teacher_id: teacher,
        group_id: group,
        reading_url: readingUrl
      };

      const resp = await fetch(`${backend}/readings/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify(body)
      });

      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.msg || "Error al crear lectura");
      }

      dispatch({
        type: "CREATE_READING_SUCCESS",
        payload: data
      });

      setSuccess("Lectura creada con éxito");

      setTitle("");
      setContent("");
      setTeacher("");
      setReadingUrl("");

    } catch (error) {
      setErr(error.message);
    } finally {
      setLoading(false);
    }
  };
return (
    <div className="container-fluid text-center">
      <div className="row">
        <div className="col-3 vh-100 text-start" style={{ backgroundColor: "#e9e9e9" }}>
          <h5 className="text-black p-4">
            Bienvenido, {store.user?.name || "Profesor"}
          </h5>
        </div>

        <div className="col-9 vh-100 d-flex flex-column p-0">
          <div className="text-white p-4 text-start" style={{ backgroundColor: "#49BBBD" }}>
            <h3>Generador de lecturas</h3>
            <h6 className="fw-light">Curso: Desarrollo Web</h6>
          </div>

          <div className="p-3 flex-grow-1" style={{ backgroundColor: "#9DCCFF" }}>
            <div className="mx-auto col-11">

              <form className="text-start bg-body rounded-4 p-4" onSubmit={handleSubmit}>

                {success && <div className="alert alert-success">{success}</div>}
                {err && <div className="alert alert-danger">{err}</div>}

                <div className="mb-3">
                  <label className="form-label">Profesor que asigna</label>
                  <input
                    className="form-control"
                    value={teacher}
                    onChange={(e) => setTeacher(e.target.value)}
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Grupo</label>
                  <input
                    className="form-control"
                    value={group}
                    onChange={(e) => setGroup(e.target.value)}
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Título</label>
                  <input
                    className="form-control"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">Instrucciones</label>
                  <textarea
                    className="form-control"
                    rows="4"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                  />
                </div>

                {/* SUBIR ARCHIVO */}
               <>
                <UploadFiles
                  onUpload={setReadingUrl}
                  setUploading={setUploading}
                />
                </>
 
                <button
                  className="btn btn-success"
                  disabled={loading || uploading}
                >
                  {loading ? "Creando..." : "Crear lectura"}
                </button>

                <Link to="/" className="btn btn-secondary ms-3">
                  Volver
                </Link>
            

              </form>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
};