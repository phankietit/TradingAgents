import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const plugins = [remarkGfm];
// No raw HTML, remote media, embedded widgets or automatic external requests.
// Source links stay in the separately verified provenance panel.
const components = {
  a: ({ children }: { children?: React.ReactNode }) => <span>{children}</span>,
  img: ({ alt }: { alt?: string }) => <span>{alt}</span>,
  table: ({ children }: { children?: React.ReactNode }) => <div className="table-scroll"><table>{children}</table></div>,
};

export default function ResearchMarkdown({ text, language }: { text: string; language?: string }) {
  return <div className="research-prose" lang={language}>
    <Markdown remarkPlugins={plugins} components={components}>{text}</Markdown>
  </div>;
}
