export default function Textarea({ label, rows = 4, style, ...props }) {
  return (
    <label style={{ display: 'block', marginBottom: 14 }}>
      {label && (
        <span style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-dim)', marginBottom: 6 }}>{label}</span>
      )}
      <textarea className="field" rows={rows} style={{ resize: 'vertical', ...style }} {...props} />
    </label>
  )
}
