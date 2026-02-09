import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import useGlobalReducer from "../hooks/useGlobalReducer.jsx";
import tareaslogo from "../assets/img/tareaslogo.png";
import { RandomImgTarea } from "../components/RandomImgTarea";




export const TodoViewTeacher = () => {

    const { store, dispatch } = useGlobalReducer();

    const [err, setErr] = useState(null);
    const [statusMap, setStatusMap] = useState({});


    const [currentPage, setCurrentPage] = useState(1);


    const todosPerPage = 6;

    useEffect(() => {
        getTodos();
    }, []);

    const getTodos = async () => {

        setErr(null);

        try {

            const backend = import.meta.env.VITE_BACKEND_URL;

            const resp = await fetch(`${backend}/todos`);

            const data = await resp.json().catch(() => ([]));

            if (!resp.ok) {
                throw new Error("Error al cargar tareas");
            }

            dispatch({
                type: "GET_TODOS_SUCCESS",
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


    const indexOfLast = currentPage * todosPerPage;
    const indexOfFirst = indexOfLast - todosPerPage;


    const sortedTodos = [...(store.todos || [])].sort(
        (a, b) => b.id - a.id
    );


    const currentTodos = sortedTodos.slice(indexOfFirst, indexOfLast);

    const totalPages = Math.ceil(sortedTodos.length / todosPerPage);



    return (

        <div className="container mt-5">

            <h1 className="mb-4">Tus tareas para revisión</h1>

            {err && <div className="alert alert-danger">{err}</div>}

            <div className="row">

                {currentTodos?.map((todo) => (

                    <div className="col-md-4 mb-4" key={todo.id}>

                        <div className="card h-100 shadow">

                            <RandomImgTarea
                                seed={todo.id}
                                className="card-img-top"
                                alt="tarea"
                                
                            />

                            <div className="card-body d-flex flex-column w-100">

                                <h5 className="card-title">
                                    {todo.title}
                                </h5>

                                <Link to={`/teachersubmissionslist/${todo.id}`} className="btn btn-primary me-2 w-25  ">
                                    Calificar
                                </Link>

                         {/*       <button
                                    className={`btn ${statusMap[todo.id] ? "btn-success" : "btn-outline-secondary"}`}
                                    onClick={() => toggleStatus(todo.id)}
                                >
                                    {statusMap[todo.id] ? "Completada" : "Pendiente"}
                                </button>*/}

                            </div>

                        </div>

                    </div>

                ))}

            </div>


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