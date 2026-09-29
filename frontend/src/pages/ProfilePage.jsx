import { User } from 'lucide-react'
import PlaceholderPage from '../components/PlaceholderPage'

export default function ProfilePage() {
  return (
    <PlaceholderPage
      icon={User}
      title="Farmer Profile"
      description="Manage your profile, farms, crops, and selling history. Authentication and profile management will be available after Phase 3."
      phase="Phase 3"
    />
  )
}
