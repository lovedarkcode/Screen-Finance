import { Button } from '@/components/ui/button'
import { Moon } from 'lucide-react'

const ThemeToggle = () => {
  return (
    <Button variant="ghost" size="sm"
      type="button"
      className="p-2 rounded-md text-gray-400 hover:text-gray-200 hover:bg-[#1a1c23] transition-colors"
      aria-label="Toggle theme"
    >
      <Moon className="w-4 h-4" />
    </Button>
  )
}

export default ThemeToggle
