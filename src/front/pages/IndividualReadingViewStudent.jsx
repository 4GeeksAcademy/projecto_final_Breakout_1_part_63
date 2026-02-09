import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import portada from "../assets/img/portada.png";

export const IndividualReadingViewStudent = () => {


    const params = useParams();

    const [reading, setReading] = useState(null);
    const [err, setErr] = useState(null);

    useEffect(() => {
        getReading();
    }, []);

    const getReading = async () => {

        setErr(null);

        try {

            const backend = import.meta.env.VITE_BACKEND_URL;

            const resp = await fetch(`${backend}/reading/${params.id}`);

            const data = await resp.json().catch(() => ({}));

            if (!resp.ok) {
                throw new Error("Error al cargar lectura");
            }

            setReading(data);

        } catch (error) {
            setErr(error.message);
        }
    };

    if (!reading) {
        return <div className="container mt-5">Cargando lectura...</div>;
    }

    return (

        <div className="container mt-1">

            {err && <div className="alert alert-danger">{err}</div>}


            <div className="m-0 p-0">
                <img
                    src={portada}
                    className="img-fluid w-100 rounded"
                    alt="cover"
                    style={{ maxHeight: "250px", objectFit: "cover" }}
                />
            </div>


            <div className="text-center col-8 mx-auto">

                <h2 className="mb-4">
                    Título de lectura: {reading.title}
                </h2>

                <hr />

                <h3>Instrucciones de lectura:</h3>
                <p className="mt-3">
                    {reading.content}
                </p>

                

                <div className="row">
                    <div className="col-4 m-auto">
                <a
                    href={reading.reading_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary mt-4 mb-3"
                >
                    Descargar archivo de lectura
                </a>

                </div>
                </div>

                <p>Haz click en el botón de "Descargar Archivo" para descargar el archivo de la lectura:</p>

                <Link to="/readings/student" className="btn btn-success mt-4 mb-3">
                    Volver a todas las lecturas
                </Link>

            </div>

        </div>
    );
}
