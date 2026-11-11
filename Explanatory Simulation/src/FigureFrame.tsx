import { useEffect, useRef, useState } from 'react';
import { usePreferences } from './Preferences';
/** A figure page built by figures/<id>/build.mjs into public/figures/<id>.html. It takes the lab's language and theme, and reports its own height. */
export default function FigureFrame({ id, title }: { id: string; title: string }) {
  const { language, theme } = usePreferences();
  const frame = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(640);
  useEffect(() => {
    const listen = (event: MessageEvent) => {
      if (event.origin !== window.location.origin || event.source !== frame.current?.contentWindow) return;
      const data = event.data;
      if (data?.type === 'supra-figure-height' && data.id === id && Number.isFinite(data.height)) setHeight(Math.max(240, Math.min(4000, data.height)));
    };
    window.addEventListener('message', listen);
    return () => window.removeEventListener('message', listen);
  }, [id]);
  return <iframe ref={frame} className="figure-frame" title={title} src={`/figures/${id}.html?lang=${language}&theme=${theme}`} style={{ height }}/>;
}
