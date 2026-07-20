import { useState } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Textarea from '@/components/ui/Textarea'
import { useSessions, useTemplates, waApi } from '@/features/wa'

export default function SendPage() {
  const { items: sessions } = useSessions()
  const { items: templates } = useTemplates()
  const [sessionId, setSessionId] = useState('')
  const [to, setTo] = useState('')
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)

  const connected = sessions.filter((s) => s.status === 'connected')

  const submit = async () => {
    setBusy(true)
    setResult(null)
    try {
      await waApi.send({ session_id: Number(sessionId), to, text })
      setResult({ ok: true, msg: 'Pesan terkirim ✅' })
      setText('')
    } catch (e) {
      setResult({ ok: false, msg: e.response?.data?.detail || 'Gagal kirim' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1 style={{ marginBottom: 18 }}>Kirim Pesan</h1>
      <Card style={{ maxWidth: 560 }}>
        <Select label="Dari nomor" value={sessionId} onChange={(e) => setSessionId(e.target.value)}>
          <option value="">— pilih nomor terhubung —</option>
          {connected.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.phone})</option>)}
        </Select>
        {!connected.length && (
          <p style={{ color: 'var(--danger)', fontSize: 13, marginTop: -6, marginBottom: 12 }}>
            Belum ada nomor terhubung. Tautkan dulu di menu Nomor.
          </p>
        )}
        <Input label="Nomor tujuan (08xx / 62xx)" value={to}
               onChange={(e) => setTo(e.target.value)} placeholder="08123456789" />

        {templates.length > 0 && (
          <Select label="Sisipkan template (opsional)" value=""
                  onChange={(e) => { const t = templates.find((x) => String(x.id) === e.target.value); if (t) setText(t.body) }}>
            <option value="">— pilih template —</option>
            {templates.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </Select>
        )}

        <Textarea label="Isi pesan" value={text} onChange={(e) => setText(e.target.value)}
                  placeholder="Tulis pesan…" />
        <Button onClick={submit} disabled={busy || !sessionId || !to || !text}>
          {busy ? 'Mengirim…' : 'Kirim'}
        </Button>
        {result && (
          <p style={{ marginTop: 14, color: result.ok ? '#2ecc71' : 'var(--danger)' }}>{result.msg}</p>
        )}
      </Card>
    </div>
  )
}
