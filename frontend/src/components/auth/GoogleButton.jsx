import { Button } from '@/components/ui/button'
import { useEffect, useRef } from 'react'
import { useDispatch } from 'react-redux'
import { useToast } from '@/components/ui/toast'
import { googleLogin } from '@/store/authSlice'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

const waitForGoogleScript = (timeout = 5000) =>
  new Promise((resolve, reject) => {
    const start = Date.now()
    const tick = () => {
      if (window.google?.accounts?.id) return resolve(window.google.accounts.id)
      if (Date.now() - start > timeout) return reject(new Error('Google script not loaded'))
      setTimeout(tick, 100)
    }
    tick()
  })

const GoogleButton = ({ onSuccess, label = 'Continue with Google' }) => {
  const toast = useToast()
  const dispatch = useDispatch()
  const buttonRef = useRef(null)
  const onSuccessRef = useRef(onSuccess)
  const initializedRef = useRef(false)

  useEffect(() => {
    onSuccessRef.current = onSuccess
  }, [onSuccess])

  const configured = Boolean(GOOGLE_CLIENT_ID)

  useEffect(() => {
    if (!configured || !buttonRef.current) return
    let cancelled = false
    const container = buttonRef.current

    waitForGoogleScript()
      .then((gid) => {
        if (cancelled) return

        if (!initializedRef.current) {
          gid.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: async (response) => {
              if (!response?.credential) return
              const result = await dispatch(googleLogin(response.credential))
              if (googleLogin.fulfilled.match(result)) {
                toast('Signed in with Google', { tone: 'success' })
                onSuccessRef.current?.(result.payload)
              } else {
                toast(result.payload || 'Google sign-in failed', { tone: 'danger' })
              }
            },
          })
          initializedRef.current = true
        }

        container.innerHTML = ''
        gid.renderButton(container, {
          theme: 'filled_black',
          size: 'large',
          shape: 'rectangular',
          text: 'continue_with',
          width: 320,
        })
      })
      .catch(() => {
        // Script blocked or offline — silently fall back to disabled state.
      })

    return () => {
      cancelled = true
    }
  }, [configured, dispatch, toast])

  if (!configured) {
    return (
      <Button variant="ghost" size="sm"
        type="button"
        disabled
        title="Set VITE_GOOGLE_CLIENT_ID in frontend/.env to enable Google sign-in"
        className="w-full flex items-center justify-center gap-2 rounded-md border border-[#2a2d36] bg-[#15171c] px-4 py-2.5 text-sm text-gray-500 cursor-not-allowed"
      >
        <GoogleIcon />
        {label} (configure VITE_GOOGLE_CLIENT_ID)
      </Button>
    )
  }

  return <div ref={buttonRef} className="flex justify-center min-h-[40px]" />
}

const GoogleIcon = () => (
  <svg viewBox="0 0 48 48" className="w-4 h-4" aria-hidden="true">
    <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.4 29.3 35.5 24 35.5c-6.4 0-11.5-5.1-11.5-11.5S17.6 12.5 24 12.5c2.9 0 5.5 1.1 7.5 2.9l5.7-5.7C33.6 6.4 29 4.5 24 4.5 13.2 4.5 4.5 13.2 4.5 24S13.2 43.5 24 43.5 43.5 34.8 43.5 24c0-1.2-.1-2.4-.4-3.5z" />
    <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.6 16 19 12.5 24 12.5c2.9 0 5.5 1.1 7.5 2.9l5.7-5.7C33.6 6.4 29 4.5 24 4.5 16.3 4.5 9.7 8.9 6.3 14.7z" />
    <path fill="#4CAF50" d="M24 43.5c5 0 9.5-1.9 12.9-5l-6-4.9c-2 1.5-4.4 2.4-6.9 2.4-5.3 0-9.7-3.1-11.3-7.5l-6.5 5C9.6 39 16.2 43.5 24 43.5z" />
    <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.2-4.4 5.5l6 4.9c-.4.4 6.5-4.7 6.5-14.4 0-1.2-.1-2.4-.4-3.5z" />
  </svg>
)

export default GoogleButton
