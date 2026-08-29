import './InlineMessage.css';

// Small reusable inline message shown within a page (never a popup/alert).
export default function InlineMessage({ type = 'error', children }) {
  if (!children) return null;
  return <div className={`inline-message ${type}`}>{children}</div>;
}
