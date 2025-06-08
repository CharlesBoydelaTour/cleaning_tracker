import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { PrivateRoute } from "@/components/PrivateRoute";

// Pages
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ResetPassword from "./pages/ResetPassword";
import Households from "./pages/Households";
import HouseholdDetail from "./pages/HouseholdDetail";
import Tasks from "./pages/Tasks";
import TaskForm from "./pages/TaskForm";
import Calendar from "./pages/Calendar";
import OccurrenceDetail from "./pages/OccurrenceDetail";
import Profile from "./pages/Profile";
import Statistics from "./pages/Statistics";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Routes publiques */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/reset-password" element={<ResetPassword />} />

            {/* Routes privées */}
            <Route path="/" element={
              <PrivateRoute>
                <Index />
              </PrivateRoute>
            } />
            <Route path="/home" element={
              <PrivateRoute>
                <Home />
              </PrivateRoute>
            } />
            <Route path="/dashboard" element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            } />
            <Route path="/households" element={
              <PrivateRoute>
                <Households />
              </PrivateRoute>
            } />
            <Route path="/households/:id" element={
              <PrivateRoute>
                <HouseholdDetail />
              </PrivateRoute>
            } />
            <Route path="/tasks" element={
              <PrivateRoute>
                <Tasks />
              </PrivateRoute>
            } />
            <Route path="/tasks/new" element={
              <PrivateRoute>
                <TaskForm />
              </PrivateRoute>
            } />
            <Route path="/tasks/:id/edit" element={
              <PrivateRoute>
                <TaskForm />
              </PrivateRoute>
            } />
            <Route path="/calendar" element={
              <PrivateRoute>
                <Calendar />
              </PrivateRoute>
            } />
            <Route path="/occurrences/:id" element={
              <PrivateRoute>
                <OccurrenceDetail />
              </PrivateRoute>
            } />
            <Route path="/profile" element={
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            } />
            <Route path="/stats" element={
              <PrivateRoute>
                <Statistics />
              </PrivateRoute>
            } />

            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;