import { useEffect, useRef, type ReactNode, type ComponentProps } from "react";
import { Button } from "@alfalab/core-components/button";
import { Input } from "@alfalab/core-components/input";
import { Checkbox } from "@alfalab/core-components/checkbox";
import { Textarea as CoreTextarea } from "@alfalab/core-components/textarea";
import { STATUS, type Status, money, type Doc } from "../domain";
export { Button, Checkbox };
export function Textarea(p: ComponentProps<typeof CoreTextarea>) {
  return (
    <CoreTextarea
      {...p}
      aria-label={typeof p.label === "string" ? p.label : undefined}
    />
  );
}
type FieldProps = Omit<ComponentProps<typeof Input>, "value" | "type"> & {
  value?: string | number;
  type?: ComponentProps<typeof Input>["type"] | "date";
};
export function Field({ value, type, ...p }: FieldProps) {
  if (type === "date")
    return (
      <label className="select-label">
        {p.label}
        <input
          className="native-date"
          type="date"
          value={value}
          onChange={(e) => p.onChange?.(e, { value: e.target.value })}
        />
      </label>
    );
  return (
    <Input
      block
      size={56}
      {...p}
      type={type}
      value={value === undefined ? undefined : String(value)}
    />
  );
}
export function Btn({
  children,
  secondary = false,
  small = false,
  ...p
}: ComponentProps<typeof Button> & { secondary?: boolean; small?: boolean }) {
  return (
    <Button
      size={small ? 40 : 56}
      view={secondary ? "secondary" : "accent"}
      {...p}
    >
      {children}
    </Button>
  );
}
export function Badge({ status }: { status: Status }) {
  return (
    <span className={"badge " + STATUS[status].tone}>
      <span className="status-dot" />
      {STATUS[status].label}
    </span>
  );
}
export function Panel({
  children,
  className = "",
  ...p
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section className={"panel " + className} {...p}>
      {children}
    </section>
  );
}
export function Heading({
  title,
  description,
  action,
  eyebrow,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  eyebrow?: string;
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1 tabIndex={-1}>{title}</h1>
        {description && <p className="muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}
export function Tabs({
  items,
  value,
  onChange,
}: {
  items: string[];
  value: string;
  onChange: (s: string) => void;
}) {
  return (
    <div className="tabs" aria-label="Разделы">
      {items.map((t) => (
        <Button
          key={t}
          view="transparent"
          size={40}
          className={value === t ? "tab active" : "tab"}
          aria-pressed={value === t}
          onClick={() => onChange(t)}
        >
          {t}
        </Button>
      ))}
    </div>
  );
}
export function Empty({
  title,
  text,
  children,
}: {
  title: string;
  text?: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-mark">—</div>
      <h2>{title}</h2>
      {text && <p>{text}</p>}
      {children}
    </div>
  );
}
export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const el = ref.current;
    const prev = document.activeElement as HTMLElement;
    el?.showModal();
    return () => {
      el?.close();
      prev?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="modal"
      aria-labelledby="dialog-title"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <div className="modal-head">
        <h2 id="dialog-title">{title}</h2>
        <Button
          aria-label="Закрыть окно"
          view="transparent"
          size={40}
          onClick={onClose}
        >
          ×
        </Button>
      </div>
      <div className="modal-content">{children}</div>
    </dialog>
  );
}
export function Facts({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="facts">
      {items.map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}
export function Notice({
  children,
  tone = "gray",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <div className={"notice " + tone}>{children}</div>;
}
export function download(
  name: string,
  text: string,
  type = "text/plain;charset=utf-8",
) {
  const u = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = u;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(u), 1000);
}
export function DocumentView({
  doc,
  onClose,
}: {
  doc: Doc;
  onClose: () => void;
}) {
  return (
    <Modal title={doc.name} onClose={onClose}>
      <Notice>Демонстрационный документ. Юридической силы не имеет.</Notice>
      {doc.mime === "application/pdf" ? (
        <iframe title={doc.name} className="doc-frame" src={doc.data} />
      ) : (
        <pre className="document-preview">{doc.data}</pre>
      )}
      <Btn
        onClick={() => {
          if (doc.data.startsWith("data:")) {
            const a = document.createElement("a");
            a.href = doc.data;
            a.download = doc.name;
            a.click();
          } else download(doc.name, doc.data);
        }}
      >
        Скачать документ
      </Btn>
    </Modal>
  );
}
export function Amount({ value, label }: { value: number; label: string }) {
  return (
    <div className="amount">
      <span>{label}</span>
      <strong>{money(value)}</strong>
    </div>
  );
}
