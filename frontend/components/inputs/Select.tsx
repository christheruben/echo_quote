type Option<T> = {
  value: T;
  label: string;
};

type SelectProps<T> = {
  label: string;
  value: T;
  onChange: (value: T) => void;
  options: readonly Option<T>[];
};

export default function Select<T>({
  label,
  value,
  onChange,
  options,
}: SelectProps<T>) {
  return (
    <div className="flex flex-col gap-1 flex-1 min-w-0">
      <label className="text-xs text-gray-500">
        {label}
      </label>

      <select
        value={String(value)}
        onChange={(e) => {
          const selected = options.find(
            (o) => String(o.value) === e.target.value
          );
          if (selected) onChange(selected.value);
        }}
        className="
          w-full
          px-3 py-2
          border border-gray-300
          rounded-lg
          text-sm
          bg-white
          focus:outline-none
          focus:ring-2 focus:ring-blue-500
        "
      >
        {options.map((o) => (
          <option key={String(o.value)} value={String(o.value)}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}