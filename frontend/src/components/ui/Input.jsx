export default function Input({ label, style, ...props }) {
  return (
    <label style={{ display: 'block', marginBottom: 14 }}>
      {label && <span style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-dim)', marginBottom: 6 }}>{label}</span>}
      <input className="field" style={style} {...props} />
    </label>
  )
}
