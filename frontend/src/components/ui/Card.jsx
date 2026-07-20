export default function Card({ children, style, className = '', ...props }) {
  return (
    <div
      className={`card ${className}`.trim()}
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
        boxShadow: 'var(--shadow)',
        padding: 22,
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  )
}
