import { useState, useEffect } from "react";
import { CardsReadings } from "../components/CardsReadings";

export const TeacherViewReadings = () => {

    const [readings, setReadings] = useState([]);
    const [err, setErr] = useState(null);
    const [statusMap, setStatusMap] = useState({});

    const [currentPage, setCurrentPage] = useState(1);
    const readingsPerPage = 6;

    useEffect(() => {
        getTeacherReadings();
    }, []);

    const getTeacherReadings = async () => {
        setErr(null);

        try {
            const backend = import.meta.env.VITE_BACKEND_URL;
            const token = localStorage.getItem("token");

            if (!token) {
                throw new Error("Usuario no autenticado");
            }

            const resp = await fetch(`${backend}/teacher/readings`, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });

            const data = await resp.json().catch(() => ([]));

            if (!resp.ok) {
                throw new Error("Error al cargar lecturas");
            }

            setReadings(data);

        } catch (error) {
            setErr(error.message);
        }
    };

    const toggleStatus = (id) => {
        setStatusMap(prev => ({
            ...prev,
            [id]: !prev[id]
        }));
    };

    //logica paginación 

    const indexOfLast = currentPage * readingsPerPage;
    const indexOfFirst = indexOfLast - readingsPerPage;

    const sortedReadings = [...readings].sort(
        (a, b) => b.id - a.id
    );

    const currentReadings = sortedReadings.slice(
        indexOfFirst,
        indexOfLast
    );

    const totalPages = Math.ceil(
        sortedReadings.length / readingsPerPage
    );

   

    return (
        <div className="container mt-5">

            <h1 className="mb-4">Lecturas que has creado</h1>

            {err && <div className="alert alert-danger">{err}</div>}

            <CardsReadings
                readings={currentReadings}
                statusMap={statusMap}
                toggleStatus={toggleStatus}
            />

            <div className="d-flex justify-content-center mt-3 mb-3">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button
                        key={page}
                        className={`btn me-2 ${
                            page === currentPage
                                ? "btn-dark"
                                : "btn-outline-dark"
                        }`}
                        onClick={() => setCurrentPage(page)}
                    >
                        {page}
                    </button>
                ))}
            </div>

        </div>
    );
};
