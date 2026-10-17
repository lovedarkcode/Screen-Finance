import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Field as ChaiField } from '@/components/ui/field'
import { Spinner } from '@/components/ui/spinner'
import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useToast } from '@/components/ui/toast'

import { clearAuthError, registerUser, selectAuth } from '@/store/authSlice'
import GoogleButton from '@/components/auth/GoogleButton'

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(120),
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'At least 8 characters'),
})

const Register = () => {
  const toast = useToast()
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
      toast(`Welcome, ${result.payload.user.name}!`, { tone: 'success' })
      navigate('/feed', { replace: true })
    } else {
      toast(result.payload || 'Registration failed', { tone: 'danger' })
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

        <Button variant="solid" size="lg" iconRight={null}
          type="submit"
          disabled={isSubmitting}
          className="w-full"
        >
          {isSubmitting && <Spinner label="Creating account" />}
          Create account
        </Button>
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
  <ChaiField label={label} error={error}>
    <Input {...inputProps} />
  </ChaiField>
)

export default Register
