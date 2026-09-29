import { Link } from 'react-router-dom'
import { ArrowLeft, Construction } from 'lucide-react'
import { ROUTES } from '../constants/routes'

/**
 * Reusable placeholder for pages that will be implemented in later phases.
 */
export default function PlaceholderPage({ icon: Icon = Construction, title, description, phase }) {
  return (
    <div className="p-6 sm:p-8 max-w-2xl mx-auto flex flex-col items-center text-center pt-20">
      <span className="flex items-center justify-center w-16 h-16 bg-primary-100 rounded-2xl mb-6">
        <Icon className="w-8 h-8 text-primary-600" />
      </span>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">{title}</h1>
      <p className="text-gray-500 mb-4 max-w-md">{description}</p>
      {phase && (
        <span className="inline-flex items-center text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 px-3 py-1 rounded-full mb-8">
          Planned for {phase}
        </span>
      )}
      <Link to={ROUTES.DASHBOARD} className="btn-secondary text-sm">
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to Dashboard
      </Link>
    </div>
  )
}
