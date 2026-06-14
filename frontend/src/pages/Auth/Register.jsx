import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { Loader2 } from 'lucide-react'

import { clearAuthError, registerUser, selectAuth } from '@/store/authSlice'
import GoogleButton from '@/components/auth/GoogleButton'

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(120),
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'At least 8 characters'),
})

const Register = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { status, error } = useSelector(selectAuth)
  const isSubmitting = status === 'loading'

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { name: '', email: '', password: '' },
  })

  useEffect(() => () => { dispatch(clearAuthError()) }, [dispatch])

  const onSubmit = async (values) => {
    const result = await dispatch(registerUser(values))
    if (registerUser.fulfilled.match(result)) {
      toast.success(`Welcome, ${result.payload.user.name}!`)
      navigate('/feed', { replace: true })
    } else {
      toast.error(result.payload || 'Registration failed')
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-gray-100">Create your account</h1>
        <p className="mt-1 text-sm text-gray-400">Free forever. No credit card required.</p>
      </div>

      <GoogleButton
        onSuccess={() => navigate('/feed', { replace: true })}
        label="Sign up with Google"
      />

      <div className="flex items-center gap-3 text-xs text-gray-500">
        <div className="flex-1 h-px bg-[#1f2129]" />
        <span>or with email</span>
        <div className="flex-1 h-px bg-[#1f2129]" />
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <Field
          label="Name"
          type="text"
          placeholder="Akshay"
          autoComplete="name"
          error={errors.name?.message}
          {...register('name')}
        />
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
          placeholder="At least 8 characters"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register('password')}
        />

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-indigo-500 hover:bg-indigo-400 disabled:opacity-60 disabled:cursor-not-allowed px-4 py-2.5 text-sm font-medium text-white transition-colors"
        >
          {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
          Create account
        </button>
      </form>

      <p className="text-center text-sm text-gray-400">
        Already have an account?{' '}
        <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-medium">
          Sign in
        </Link>
      </p>
    </div>
  )
}

const Field = ({ label, error, ...inputProps }) => (
  <label className="block">
    <span className="block text-xs font-medium text-gray-300 mb-1.5">{label}</span>
    <input
      {...inputProps}
      className="w-full rounded-md border border-[#2a2d36] bg-[#15171c] px-3 py-2 text-sm text-gray-100 placeholder-gray-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40 transition"
    />
    {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
  </label>
)

export default Register
