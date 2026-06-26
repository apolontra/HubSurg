// Átomo (Atomic Design): indicador de status reutilizável. Ver ADR-0005.
export type Status = "ok" | "pending" | "error";

const LABELS: Record<Status, string> = {
  ok: "Operacional",
  pending: "Pendente",
  error: "Erro",
};

export function StatusBadge({ status }: { status: Status }) {
  return <span data-status={status}>{LABELS[status]}</span>;
}
