import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useGlobalReducer from "../hooks/useGlobalReducer";

export const Login = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [err, setErr] = useState(null);

    const navigate = useNavigate();
    const { store, dispatch } = useGlobalReducer();
    const { role } = store;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setErr(null);

        try {
            const backend = import.meta.env.VITE_BACKEND_URL;

            const resp = await fetch(`${backend}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await resp.json();

            if (!resp.ok) {
                throw new Error(data.msg || "Error de Inicio de Sesión");
            }
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("role", data.role);
            localStorage.setItem("user_name", data.user?.name || "");
            localStorage.setItem("user_id", String(data.user?.id || ""));

            console.log("GUARDADO:", {
                token: localStorage.getItem("token"),
                role: localStorage.getItem("role"),
            });

            dispatch({
                type: "LOGIN_SUCCESS",
                payload: {
                    user: null,
                    role: data.role
                }
            });

            if (data.role === "STUDENT") {
                navigate("/homeStudent");
            } else if (data.role === "TEACHER") {
                navigate("/homeTeacher");
            } else if (data.role === "ADMIN") {
                navigate("/homeAdmin");
            } else {
                navigate("/");
            }

        } catch (error) {
            setErr(error.message);
        }
    };

    return (
        <div className="container col-5 mt-5 mx-auto">
            <h1>Login</h1>

            {err && <div className="alert alert-danger mt-3">{err}</div>}

            <form onSubmit={handleSubmit} className="mt-3">
                <div className="mb-3">
                    <label className="form-label">Dirección de Email</label>
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

                <button type="submit" className="btn btn-info">
                    Login
                </button>
            </form>
        </div>
    );
};
