// A small Markdown renderer for Claude's answer: headings, lists, bold, italics,
// inline code and links. It builds React elements (no raw HTML), so model output
// can't inject markup.
import { Fragment, type ReactNode } from "react";

function inline(text: string, key = 0): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\((https?:\/\/[^)\s]+)\)|_[^_\s][^_]*_|\*[^*\s][^*]*\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = key;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(<strong key={i++}>{tok.slice(2, -2)}</strong>);
    else if (tok.startsWith("`")) out.push(<code key={i++}>{tok.slice(1, -1)}</code>);
    else if (tok.startsWith("[")) {
      const label = tok.slice(1, tok.indexOf("]"));
      out.push(<a key={i++} href={m[2]} target="_blank" rel="noopener noreferrer">{label}</a>);
    } else out.push(<em key={i++}>{tok.slice(1, -1)}</em>);
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export default function Markdown({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  const lines = text.split(/\r?\n/);
  let list: { ordered: boolean; items: string[] } | null = null;
  let para: string[] = [];
  const flush = () => {
    if (para.length) blocks.push(<p key={blocks.length}>{inline(para.join(" "))}</p>);
    para = [];
    if (list) {
      const items = list.items.map((it, i) => <li key={i}>{inline(it.replace(/^\[[ x]\]\s*/, ""))}</li>);
      blocks.push(list.ordered ? <ol key={blocks.length}>{items}</ol> : <ul key={blocks.length}>{items}</ul>);
      list = null;
    }
  };
  for (const raw of lines) {
    const line = raw.trimEnd();
    const h = /^(#{1,4})\s+(.*)$/.exec(line);
    const ul = /^\s*[-*+]\s+(.*)$/.exec(line);
    const ol = /^\s*\d+[.)]\s+(.*)$/.exec(line);
    if (h) {
      flush();
      const level = Math.min(4, h[1].length + 1);
      const Tag = (`h${level}` as "h2" | "h3" | "h4");
      blocks.push(<Tag key={blocks.length}>{inline(h[2])}</Tag>);
    } else if (ul || ol) {
      if (para.length) { blocks.push(<p key={blocks.length}>{inline(para.join(" "))}</p>); para = []; }
      const ordered = !!ol;
      if (!list || list.ordered !== ordered) { flush(); list = { ordered, items: [] }; }
      list.items.push((ul ?? ol)![1]);
    } else if (!line.trim()) flush();
    else if (/^-{3,}$/.test(line.trim())) { flush(); blocks.push(<hr key={blocks.length} />); }
    else {
      if (list) flush();
      para.push(line.trim());
    }
  }
  flush();
  return <Fragment>{blocks}</Fragment>;
}
