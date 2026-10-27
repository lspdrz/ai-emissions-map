/** A labelled search box: square, ink-bordered, white. Used by the routes table and the organization cards. */
export function SearchInput({ id, label, placeholder, value, onChange }: {
  id: string; label: string; placeholder: string; value: string; onChange: (value: string) => void;
}) {
  return (
    <div className="flex w-full max-w-[360px] flex-col gap-1.5">
      <label htmlFor={id} className="font-mono text-[11px] text-muted">
        {label}
      </label>
      <input
        id={id}
        type="search"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete="off"
        className="box-border min-h-11 w-full rounded-none border border-ink bg-input px-3.5 font-sans text-[15px] text-ink"
      />
    </div>
  );
}
