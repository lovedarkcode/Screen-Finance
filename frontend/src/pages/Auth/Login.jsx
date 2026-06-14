import { useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { Loader2 } from 'lucide-react'

import { clearAuthError, loginUser, selectAuth } from '@/store/authSlice'
import GoogleButton from '@/components/auth/GoogleButton'

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

const Login = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const location = useLocation()
  const { status, error } = useSelector(selectAuth)
  const isSubmitting = status === 'loading'

  const redirectTo = '/feed'

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ resolver: zodResolver(schema), defaultValues: { email: '', password: '' } })

  useEffect(() => () => { dispatch(clearAuthError()) }, [dispatch])

  const onSubmit = async (values) => {
    const result = await dispatch(loginUser(values))
    if (loginUser.fulfilled.match(result)) {
      toast.success(`Welcome back, ${result.payload.user.name}`)
      navigate(redirectTo, { replace: true })
    } else {
      toast.error(result.payload || 'Login failed')
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center flex flex-col items-center">
        <span className="w-16 h-16 rounded-xl mb-3 shadow-lg bg-white border border-[#2a2d36] overflow-hidden flex items-center justify-center">
          <img
            src="/assest-hunter.png"
            alt="Asset Hunter Logo"
            className="w-full h-full object-cover scale-[2.8]"
            style={{ objectPosition: '50% 34%' }}
          />
        </span>
        <h1 className="text-2xl font-semibold text-gray-100">Welcome back</h1>
        <p className="mt-1 text-sm text-gray-400">Sign in to your Assest Hunter account</p>
      </div>

      <GoogleButton onSuccess={() => navigate(redirectTo, { replace: true })} />

      <div className="flex items-center gap-3 text-xs text-gray-500">
        <div className="flex-1 h-px bg-[#1f2129]" />
        <span>or continue with email</span>
        <div className="flex-1 h-px bg-[#1f2129]" />
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <Field
          label="Email"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          error={errors.email?.message}
          {...register('email')}
        />
        <Field
          label="Password"
          type="password"
          placeholder="••••••••"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
          rightSlot={
            <Link to="/forgot-password" className="text-xs text-indigo-400 hover:text-indigo-300">
              Forgot?
            </Link>
          }
        />

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-indigo-500 hover:bg-indigo-400 disabled:opacity-60 disabled:cursor-not-allowed px-4 py-2.5 text-sm font-medium text-white transition-colors"
        >
          {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
          Sign in
        </button>
      </form>

      <p className="text-center text-sm text-gray-400">
        Don&apos;t have an account?{' '}
        <Link to="/register" className="text-indigo-400 hover:text-indigo-300 font-medium">
          Create one
        </Link>
      </p>
    </div>
  )
}

const Field = ({ label, error, rightSlot, ...inputProps }) => (
  <label className="block">
    <div className="flex items-center justify-between mb-1.5">
      <span className="text-xs font-medium text-gray-300">{label}</span>
      {rightSlot}
    </div>
    <input
      {...inputProps}
      className="w-full rounded-md border border-[#2a2d36] bg-[#15171c] px-3 py-2 text-sm text-gray-100 placeholder-gray-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40 transition"
    />
    {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
  </label>
)

export default Login
