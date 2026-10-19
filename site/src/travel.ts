// Airport codes and money formatting: the small details that make the plan
// read like a trip. Hubs are each country's main international airport.
import type { Lang } from "./types";

export const HUB: Record<string, string> = {
  JP: "HND", IE: "DUB", AU: "SYD", NL: "AMS", FI: "HEL", GB: "LHR", DE: "FRA", SE: "ARN", DK: "CPH", NO: "OSL",
  LU: "LUX", EE: "TLL", AE: "DXB", NZ: "AKL", CA: "YYZ", SG: "SIN", TW: "TPE", KR: "ICN", US: "JFK", CH: "ZRH",
  PT: "LIS", ES: "MAD", FR: "CDG", IT: "FCO", BE: "BRU", AT: "VIE", PL: "WAW", CZ: "PRG", GR: "ATH", TR: "IST",
  BR: "GRU", AR: "EZE", CL: "SCL", CO: "BOG", MX: "MEX", PE: "LIM", UY: "MVD", VE: "CCS", EC: "UIO", BO: "VVI",
  PY: "ASU", IN: "DEL", PK: "KHI", BD: "DAC", LK: "CMB", NP: "KTM", CN: "PEK", HK: "HKG", PH: "MNL", VN: "SGN",
  TH: "BKK", MY: "KUL", ID: "CGK", NG: "LOS", KE: "NBO", ZA: "JNB", EG: "CAI", MA: "CMN", GH: "ACC", ET: "ADD",
  UA: "KBP", RU: "SVO", IL: "TLV", SA: "RUH", QA: "DOH", IR: "IKA", RO: "OTP", HU: "BUD", RS: "BEG", HR: "ZAG",
};

export const hub = (code: string) => HUB[code] ?? code;

export function money(amount: number, currency: string, lang: Lang): string {
  try {
    return new Intl.NumberFormat(lang === "pt" ? "pt-BR" : "en", {
      style: "currency", currency, maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${amount.toLocaleString()} ${currency}`;
  }
}

/** A stable, plane-ticket-like flight number for a country (e.g. "VJA 0451"). */
export function flightNo(code: string, i = 0): string {
  const n = ((code.charCodeAt(0) * 31 + code.charCodeAt(1) * 7 + i * 13) % 900) + 100;
  return `VJA ${String(n).padStart(4, "0")}`;
}
