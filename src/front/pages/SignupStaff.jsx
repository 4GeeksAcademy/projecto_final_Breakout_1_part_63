import { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import useGlobalReducer from "../hooks/useGlobalReducer.jsx";

export const SignupStaff = () => {
  const { dispatch } = useGlobalReducer();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("");
  const [err, setErr] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErr(null);

    try {
      const resp = await fetch("https://humble-tribble-5gp74r6w9wvxf5gv-3001.app.github.dev/register/staff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, role }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.msg || "Error de registro");
      }

      dispatch({
        type: "REGISTER_STAFF_SUCCESS",
        payload: {
          user: {
            name,
            email
          },
          role
        }
      });

      navigate("/private-staff");

    } catch (error) {
      setErr(error.message);
    }
  };

  return (
    <div className="container col-5 mt-5 mx-auto">
      <h1>Registro Staff</h1>

      {err && <div className="alert alert-danger mt-3">{err}</div>}

      <form onSubmit={handleSubmit} className="mt-3">

        <div className="mb-3">
          <label className="form-label">Nombre Completo</label>
          <input
            type="text"
            className="form-control"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div className="mb-3">
          <label className="form-label">Email</label>
          <input
            type="email"
            className="form-control"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="mb-3">
          <label className="form-label">Password</label>
          <input
            type="password"
            className="form-control"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <div className="mb-3">
          <label className="form-label">Rol</label>
          <select
            className="form-select"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            required
          >
            <option value="">Seleccionar rol</option>
            <option value="ADMIN">Administrador</option>
            <option value="TEACHER">Profesor</option>
          </select>
        </div>

        <button type="submit" className="btn btn-primary">
          Registrar
        </button>
      </form>
    </div>
  );
};