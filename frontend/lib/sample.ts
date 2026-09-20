export const SAMPLE = {
  schemeName: "",
  previous: { url: "/sample/hdfc-2026-07.pdf", name: "HDFC MF Factsheet - July 2026.pdf" },
  current: { url: "/sample/hdfc-2026-08.pdf", name: "HDFC MF Factsheet - August 2026.pdf" },
};

async function toFile(src: { url: string; name: string }): Promise<File> {
  const res = await fetch(src.url);
  if (!res.ok) throw new Error("Could not load the sample factsheets.");
  const blob = await res.blob();
  return new File([blob], src.name, { type: "application/pdf" });
}

export async function loadSample(): Promise<{ previous: File; current: File }> {
  const [previous, current] = await Promise.all([toFile(SAMPLE.previous), toFile(SAMPLE.current)]);
  return { previous, current };
}
