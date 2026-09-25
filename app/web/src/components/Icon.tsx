export function Icon({ name }: { name: string }) {
  const paths: Record<string, string> = {
    book: 'M12 6c-3-3-7-3-10-1v15c3-2 7-2 10 1 3-3 7-3 10-1V5c-3-2-7-2-10 1zm0 0v15',
    mic: 'M9 5a3 3 0 0 1 6 0v7a3 3 0 0 1-6 0zm-3 6v1a6 6 0 0 0 12 0v-1m-6 7v4m-4 0h8',
    audio: 'M3 10v4m4-8v12m5-16v20m5-16v12m4-8v4',
    grid: 'M3 3h7v7H3zm11 0h7v7h-7zM3 14h7v7H3zm11 0h7v7h-7z',
    pause: 'M7 4v16M17 4v16',
    play: 'M7 3l14 9-14 9z',
    stop: 'M5 5h14v14H5z',
    download: 'M12 3v12m-5-5l5 5 5-5M4 16v5h16v-5',
    shield: 'M12 2l9 4v6c0 5-6 9-9 10-3-1-9-5-9-10V6zm-5 10l3 3 7-7',
    arrow: 'M4 12h16m-6-6l6 6-6 6',
  }
  return <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name] || paths.book} /></svg>
}
