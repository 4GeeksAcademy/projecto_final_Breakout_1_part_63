import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import useGlobalReducer from "../hooks/useGlobalReducer.jsx";
import lecturaslogo from "../assets/img/lecturaslogo.png";

export const ReadingsViewStudents = () => {

    const { store, dispatch } = useGlobalReducer();
    const navigate = useNavigate();
    const [err, setErr] = useState(null);
    const [statusMap, setStatusMap] = useState({});


    const [currentPage, setCurrentPage] = useState(1);


    const readingsPerPage = 6;

    useEffect(() => {
        getReadings();
    }, []);

    const getReadings = async () => {

        setErr(null);

        try {

            const backend = import.meta.env.VITE_BACKEND_URL;

            const resp = await fetch(`${backend}/readings`);

            const data = await resp.json().catch(() => ([]));

            if (!resp.ok) {
                throw new Error("Error al cargar lecturas");
            }

            dispatch({
                type: "GET_READINGS_SUCCESS",
                payload: data
            });

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


    const indexOfLast = currentPage * readingsPerPage;
    const indexOfFirst = indexOfLast - readingsPerPage;


    const sortedReadings = [...(store.readings || [])].sort(
        (a, b) => b.id - a.id
    );


    const currentReadings = sortedReadings.slice(indexOfFirst, indexOfLast);

    const totalPages = Math.ceil(sortedReadings.length / readingsPerPage);



    return (

        <div className="container mt-5">

            <h1 className="mb-4">Tus lecturas, Vicente</h1>

            {err && <div className="alert alert-danger">{err}</div>}

            <div className="row">

                {currentReadings?.map((reading) => (

                    <div className="col-md-4 mb-4" key={reading.id}>

                        <div className="card h-100 shadow">

                            <img
                                src={lecturaslogo}
                                className="card-img-top"
                                alt="lectura"
                            />

                            <div className="card-body">

                                <h5 className="card-title">
                                    {reading.title}
                                </h5>

                                <Link to={`/reading/${reading.id}`} className="btn btn-primary me-2">
                                    Revisar lectura
                                </Link>

                                <button
                                    className={`btn ${statusMap[reading.id] ? "btn-success" : "btn-outline-secondary"}`}
                                    onClick={() => toggleStatus(reading.id)}
                                >
                                    {statusMap[reading.id] ? "Completada" : "Pendiente"}
                                </button>

                            </div>

                        </div>

                    </div>

                ))}

            </div>
 <button
        type="button"
        className="btn btn-sm btn-outline-secondary mb-3"
        onClick={() => navigate(-1)}
      >
        ← Volver
      </button>

            <div className="d-flex justify-content-center mt-3 mb-3">

                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button
                        key={page}
                        className={`btn me-2 ${page === currentPage ? "btn-dark" : "btn-outline-dark"}`}
                        onClick={() => setCurrentPage(page)}
                    >
                        {page}
                    </button>

                ))}

            </div>

        </div>
    );
};
