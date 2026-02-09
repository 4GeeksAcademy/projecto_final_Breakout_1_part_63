export const initialStore = () => {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const role =
    typeof window !== "undefined" ? localStorage.getItem("role") : null;

  return {
    message: null,
    todos: [],
    user: null,
    role: role ? role : null,
    isAuthenticated: !!token,
    readings: [],
    students: [],
    groups: [],
    staff: [],
  };
};

export default function storeReducer(store, action = {}) {
  switch (action.type) {
    case "REGISTER_STAFF_SUCCESS":  
      return {
        ...store,
        user: action.payload.user,
        role: action.payload.role,
        isAuthenticated: true,
        message: "Staff registrado correctamente",
      };

    case "LOGIN_SUCCESS":

      return {
        ...store,
        user: action.payload.user,
        role: action.payload.role,
        isAuthenticated: true,
        message: "Inicio de sesión exitoso",
      };

    case "LOGOUT":
      return {
        ...store,
        user: null,
        role: null,
        isAuthenticated: false,
      };

    case "set_hello":
      return {
        ...store,
        message: action.payload,
      };

    case "SET_TODOS":
      return {
        ...store,
        todos: action.payload,
      };

    case "add_task":
      const { id, color } = action.payload;
      return {
        ...store,
        todos: store.todos.map((todo) =>
          todo.id === id ? { ...todo, background: color } : todo
        ),
      };



    case "GET_TODOS_SUCCESS":
      return {
        ...store,
        todos: action.payload,
      };

    case "CREATE_READING_SUCCESS":
      return {
        ...store,
        readings: [...store.readings, action.payload],
        message: "Lectura creada correctamente",
      };

    case "GET_READINGS_SUCCESS":
      return {
        ...store,
        readings: action.payload,
      };

    case "REGISTER_STUDENTS_SUCCESS":
      return {
        ...store,
        students: [...store.students, action.payload],
        message: "Alumno registrado correctamente",
      };

      case "GET_STAFF_SUCCESS":
        return {
          ...store,
          staff: action.payload,
        };
      
      case "SET_GROUPS":
        return {
          ...store,
          groups: action.payload,
        };

      case "SET_CURRENT_USER":
            return {
                ...store,
                user: action.payload,
            };

    default:
      throw Error("Unknown action.");
  }
}