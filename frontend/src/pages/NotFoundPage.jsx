import { Link } from 'react-router-dom'
import { ROUTES } from '../constants/routes'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center px-4">
      <p className="text-6xl font-bold text-gray-200 mb-4">404</p>
      <h1 className="text-xl font-semibold text-gray-800 mb-2">Page not found</h1>
      <p className="text-gray-500 mb-8">The page you are looking for does not exist.</p>
      <Link to={ROUTES.HOME} className="btn-primary">Back to Home</Link>
    </div>
  )
}
