import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatKw(val: number | undefined | null): string {
  if (val === undefined || val === null) return "0.0 kW";
  return `${val.toFixed(1)} kW`;
}

export function formatKwh(val: number | undefined | null): string {
  if (val === undefined || val === null) return "0.0 kWh";
  return `${val.toFixed(1)} kWh`;
}

export function formatCurrency(val: number | undefined | null): string {
  if (val === undefined || val === null) return "$0.00";
  return `$${val.toFixed(2)}`;
}

export function formatPct(val: number | undefined | null): string {
  if (val === undefined || val === null) return "0.0%";
  return `${val.toFixed(1)}%`;
}

export function formatTime(ts: string | Date | undefined): string {
  if (!ts) return "";
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
}

export function formatDate(ts: string | Date | undefined): string {
  if (!ts) return "";
  const d = new Date(ts);
  return d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
}
