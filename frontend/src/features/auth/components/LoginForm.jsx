import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Card from '@/components/ui/Card'
import { ROUTES } from '@/config/routes'
import { APP_NAME } from '@/config/constants'
import { useLogin } from '../hooks/useAuth'

export default function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { submit, loading, error } = useLogin()
  const navigate = useNavigate()

  const handleSubmit = async () => {
    const user = await submit(email, password)
    if (user) navigate(ROUTES.dashboard)
  }

  return (
    <Card style={{ width: 372, padding: 28 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginBottom: 20 }}>
        <div style={{ width: 38, height: 38, borderRadius: 10, background: '#25D366', display: 'grid', placeItems: 'center', color: '#fff', fontSize: 20 }}>✆</div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 17 }}>{APP_NAME}</div>
          <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Masuk ke dashboard</div>
        </div>
      </div>
      <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <Input
        label="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
      />
      {error && <p style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>{error}</p>}
      <Button onClick={handleSubmit} disabled={loading} style={{ width: '100%' }}>
        {loading ? 'Memproses…' : 'Masuk'}
      </Button>
    </Card>
  )
}
