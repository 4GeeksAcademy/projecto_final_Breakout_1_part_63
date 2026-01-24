import { Link } from "react-router-dom";

export const Navbar = () => {

	return (
			<nav className="navbar navbar-light bg-light">
			<div className="container col-8">
				
					<span className="navbar-brand mb-0 h1 ">ACADEMICA</span>
				
				<div className="ml-auto">
				
		
					<Link to="/Login">
						<button className="btn btn-info p-2 ms-2 ">Inicio de sesión</button>
					</Link>

					<Link to="/Signup">
						<button className="btn btn-info p-2  ms-2" >Registro</button>
					</Link>


				</div>
			</div>
		</nav>
	);
};