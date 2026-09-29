import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ROUTES } from './constants/routes'
import AppLayout from './layouts/AppLayout'
import LandingPage from './pages/LandingPage'
import DashboardPage from './pages/DashboardPage'
import MarketsPage from './pages/MarketsPage'
import PredictionPage from './pages/PredictionPage'
import RecommendationsPage from './pages/RecommendationsPage'
import BuyersPage from './pages/BuyersPage'
import ProfilePage from './pages/ProfilePage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing page — full screen, no app shell */}
        <Route path={ROUTES.HOME} element={<LandingPage />} />

        {/* App shell — sidebar + main content */}
        <Route element={<AppLayout />}>
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
    </BrowserRouter>
  )
}
