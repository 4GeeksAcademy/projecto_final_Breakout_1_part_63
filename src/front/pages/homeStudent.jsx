import React, { useEffect } from "react";
import { TodoCard } from "../components/todoCard";
import useGlobalReducer from "../hooks/useGlobalReducer";
import { ReadingCards } from "../components/ReadingCards";

export const HomeStudent = () => {
	const { store, dispatch } = useGlobalReducer();
	const todos = store.todos || [];

	useEffect(() => {
		const fetchTodos = async () => {
			try {
				const backend = import.meta.env.VITE_BACKEND_URL;
				const resp = await fetch(`${backend}/todos`, {
					headers: {
						"Content-Type": "application/json",
						Authorization: `Bearer ${localStorage.getItem("token")}`,
					},
				});

				const data = await resp.json();

				dispatch({
					type: "SET_TODOS",
					payload: data,
				});

			} catch (error) {
				console.error("Error fetching tasks:", error);
			}
		};

		fetchTodos();
	}, [dispatch]);

	const fetchReadings = async () => {
		try {
			const backend = import.meta.env.VITE_BACKEND_URL;
			const resp = await fetch(`${backend}/readings`, {
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${localStorage.getItem("token")}`,
				},
			});

			const data = await resp.json();

			dispatch({
				type: "GET_READINGS_SUCCESS",
				payload: data,
			});

		} catch (error) {
			console.error("Error fetching readings:", error);
		}
	};

	useEffect(() => {
		fetchReadings();
	}, [dispatch]);

	 useEffect(() => {
				const fetchMe = async () => {
					try {
						const backend = import.meta.env.VITE_BACKEND_URL;
						const resp = await fetch(`${backend}/me`, {
							headers: {
								"Content-Type": "application/json",
								Authorization: `Bearer ${localStorage.getItem("token")}`,
							},
						});
		
						if (!resp.ok) throw new Error("Error obteniendo usuario");
		
						const data = await resp.json();
		
						dispatch({
							type: "SET_CURRENT_USER",
							payload: data,
						});
					} catch (error) {
						console.error("Error fetching current user:", error);
					}
				};
		
				fetchMe();
			}, [dispatch]);
	
	return (
		<div className="bg-light pb-5">
			<div className="g-color-bg hero-home text-white">
				<div className="container">
					<div className="row align-items-center">
						<div className="col-md-6">
							<h1 className="display-5 fw-bold mb-4 g-color">
                                Bienvenido  <span className="text-primary">{store.user?.name || "Estudiante"}</span>
                            </h1>
							<p className="fs-5">
								Aquí podrás gestionar tus tareas, lecturas y calificaciones
								de forma simple y rápida.
							</p>
						</div>

						<div className="col-md-6 text-center my-3">
							<img
								src="https://fastly.picsum.photos/id/3/5000/3333.jpg?hmac=GDjZ2uNWE3V59PkdDaOzTOuV3tPWWxJSf4fNcxu4S2g"
								className="img-fluid rounded-5"
								alt="novedades"
							/>
						</div>
					</div>
				</div>
			</div>

			<div className="container mt-5">
				<h2 className="fw-bold mb-4">Mis Tareas</h2>

				{todos.length === 0 && (
					<p>No hay tareas asignadas</p>
				)}

				<div className="d-flex gap-3 overflow-auto px-3 pb-3">
					{todos.map(todo => (
						<TodoCard key={todo.id} todo={todo} />
					))}
				</div>
			</div>

			<div className="container mt-5">
				<h2 className="fw-bold mb-4">Mis Lecturas</h2>

				{store.readings.length === 0 && (
					<p>No hay lecturas disponibles</p>
				)}

				<div className="d-flex gap-3 overflow-auto px-3 pb-3">
					{store.readings.map(reading => (
						<ReadingCards key={reading.id} reading={reading} />
					))}
				</div>
			</div>
		</div>
	);
};