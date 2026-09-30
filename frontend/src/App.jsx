import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ROUTES } from "./constants/routes";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./layouts/AppLayout";

import LandingPage       from "./pages/LandingPage";
import LoginPage         from "./pages/LoginPage";
import RegisterPage      from "./pages/RegisterPage";
import DashboardPage     from "./pages/DashboardPage";
import MarketsPage       from "./pages/MarketsPage";
import PredictionPage    from "./pages/PredictionPage";
import RecommendationsPage from "./pages/RecommendationsPage";
import BuyersPage        from "./pages/BuyersPage";
import ProfilePage       from "./pages/ProfilePage";
import NotFoundPage      from "./pages/NotFoundPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public pages — no app shell */}
          <Route path={ROUTES.HOME}     element={<LandingPage />} />
          <Route path="/login"          element={<LoginPage />} />
          <Route path="/register"       element={<RegisterPage />} />

          {/* App shell — requires authentication */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path={ROUTES.DASHBOARD}       element={<DashboardPage />} />
            <Route path={ROUTES.MARKETS}         element={<MarketsPage />} />
            <Route path={ROUTES.PREDICTION}      element={<PredictionPage />} />
            <Route path={ROUTES.RECOMMENDATIONS} element={<RecommendationsPage />} />
            <Route path={ROUTES.BUYERS}          element={<BuyersPage />} />
            <Route path={ROUTES.PROFILE}         element={<ProfilePage />} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
