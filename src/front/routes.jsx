// Import necessary components and functions from react-router-dom.

import {
  createBrowserRouter,
  createRoutesFromElements,
  Route,
} from "react-router-dom";
import { Layout } from "./pages/Layout";
import { Home } from "./pages/Home";
import { Single } from "./pages/Single";
import { Demo } from "./pages/Demo";
import { Signup } from "./pages/Signup";
import { Login } from "./pages/Login";
import { CreateTodoForm } from "./pages/CreateTodoForm";
import { SignupStaff } from "./pages/SignupStaff";
import { CreateReadings } from "./pages/CreateReadings";
import { HomeStudent } from "./pages/homeStudent";
import { StudentViewReadings } from "./pages/StudentViewReadings.jsx";
import { IndividualReadingViewStudent } from "./pages/IndividualReadingViewStudent.jsx";
import { HomeTeacher } from "./pages/HomeTeacher.jsx";
import { HomeAdmin } from "./pages/HomeAdmin.jsx";

import { IndividualTodoViewStudent } from "./pages/IndividualTodoViewStudent.jsx"
import { ProtectedRoute } from "./components/ProtectedRoute";
import { TodoViewStudent } from "./pages/TodoViewStudent.jsx";
import { CreateGroupsAdmin } from "./pages/CreateGroupsAdmin";
import { TeacherViewReadings } from "./pages/TeacherViewReadings";
import { TodoDetailTeacher } from "./pages/TodoDetailTeacher.jsx";



export const router = createBrowserRouter(
  createRoutesFromElements(
    // CreateRoutesFromElements function allows you to build route elements declaratively.
    // Create your routes here, if you want to keep the Navbar and Footer in all views, add your new routes inside the containing Route.
    // Root, on the contrary, create a sister Route, if you have doubts, try it!
    // Note: keep in mind that errorElement will be the default page when you don't get a route, customize that page to make your project more attractive.
    // Note: The child paths of the Layout element replace the Outlet component with the elements contained in the "element" attribute of these child paths.

    // Root Route: All navigation will start from here.
    // Root Route: All navigation will start from here.
    <Route path="/" element={<Layout />} errorElement={<h1>Not found!</h1>} >

      {/* Nested Routes: Defines sub-routes within the BaseHome component. */}
      <Route path="/" element={<Home />} />
      <Route path="/single/:theId" element={<Single />} />  {/* Dynamic route for single items */}
      <Route path="/demo" element={<Demo />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/login" element={<Login />} />
      <Route path="/crear-tarea" element={<CreateTodoForm />} />
      <Route path="/signup-staff" element={<SignupStaff />} />
      <Route path="/readings-create" element={<CreateReadings />} />
      <Route path="/homeStudent" element={<HomeStudent />} />
      <Route path="/readings/student" element={<StudentViewReadings />} />
      <Route path="/reading/:id" element={<IndividualReadingViewStudent />} />
      <Route path="/teacher/readings" element={<TeacherViewReadings />} />
      <Route path="/todos/:id" element={<IndividualTodoViewStudent />} />
      <Route path="/todoviewstudent" element={<TodoViewStudent />} />
      <Route path="/homeStudent" element={<ProtectedRoute allowedRoles={["STUDENT"]}> <HomeStudent /> </ProtectedRoute>} />
      <Route path="/admin/groups" element={<ProtectedRoute allowedRoles={["ADMIN"]}> <CreateGroupsAdmin /> </ProtectedRoute>}/>
      <Route path="/homeTeacher" element={<ProtectedRoute allowedRoles={["TEACHER"]}> <HomeTeacher /> </ProtectedRoute>} />
      <Route path="/homeAdmin" element={<ProtectedRoute allowedRoles={["ADMIN"]}> <HomeAdmin /> </ProtectedRoute>} />
      <Route path="/teacher/todos/:id" element={<TodoDetailTeacher />} />


    </Route>
  )
);