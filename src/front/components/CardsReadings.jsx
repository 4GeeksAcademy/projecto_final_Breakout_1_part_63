// src/components/CardsReadings.jsx
import { Link } from "react-router-dom";
import lecturaslogo from "../assets/img/lecturaslogo.png";

export const CardsReadings = ({
    readings,
    statusMap,
    toggleStatus
}) => {
    return (
        <div className="row">
            {readings.map((reading) => (
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

                            <Link
                                to={`/reading/${reading.id}`}
                                className="btn btn-primary me-2"
                            >
                                Revisar lectura
                            </Link>

                            <button
                                className={`btn ${
                                    statusMap[reading.id]
                                        ? "btn-success"
                                        : "btn-outline-secondary"
                                }`}
                                onClick={() => toggleStatus(reading.id)}
                            >
                                {statusMap[reading.id]
                                    ? "Completada"
                                    : "Pendiente"}
                            </button>

                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};
