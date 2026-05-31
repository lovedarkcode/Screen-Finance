import { Link } from 'react-router-dom'

const ForgotPassword = () => {
  return (
    <div className="space-y-6 text-center">
      <h1 className="text-2xl font-semibold text-gray-100">Forgot your password?</h1>
      <p className="text-sm text-gray-400">
        Password reset emails aren&apos;t hooked up yet. For now, please ask an admin to reset it
        for you, or sign in with Google instead.
      </p>
      <Link
        to="/login"
        className="inline-block rounded-md bg-indigo-500 hover:bg-indigo-400 px-4 py-2 text-sm font-medium text-white transition-colors"
      >
        Back to sign in
      </Link>
    </div>
  )
}

export default ForgotPassword
