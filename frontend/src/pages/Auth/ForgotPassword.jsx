import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

const ForgotPassword = () => {
  return (
    <div className="space-y-6 text-center">
      <h1 className="text-2xl font-semibold text-gray-100">Forgot your password?</h1>
      <p className="text-sm text-gray-400">
        Password reset emails aren&apos;t hooked up yet. For now, please ask an admin to reset it
        for you, or sign in with Google instead.
      </p>
      <Button asChild variant="solid" iconRight={null}><Link to="/login">
        Back to sign in
      </Link></Button>
    </div>
  )
}

export default ForgotPassword
