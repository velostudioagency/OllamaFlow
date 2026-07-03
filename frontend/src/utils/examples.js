const examples = {
  'Web Research Agent': {
    name: 'Web Research Agent',
    nodes: [
      { id: 'wr1', type: 'input', position: { x: 50, y: 200 }, data: { label: 'Input', config: { prompt: 'Research the latest developments in AI agents', input_type: 'text' } } },
      { id: 'wr2', type: 'tool', position: { x: 350, y: 200 }, data: { label: 'Web Search', config: { tool_name: 'web_search', params: {} } } },
      { id: 'wr3', type: 'llm', position: { x: 650, y: 200 }, data: { label: 'Research Analyst', config: { model: 'llama3.1:8b', system_prompt: 'You are a research analyst. Analyze the search results and identify the most relevant URLs worth scraping for deeper information. Return a list of the top 2-3 most relevant URLs, one per line.', temperature: 0.2, max_tokens: 500 } } },
      { id: 'wr4', type: 'tool', position: { x: 950, y: 200 }, data: { label: 'Web Scraper', config: { tool_name: 'web_scraper', params: {} } } },
      { id: 'wr5', type: 'llm', position: { x: 1250, y: 200 }, data: { label: 'Summarizer', config: { model: 'llama3.1:8b', system_prompt: 'You are a research assistant. Synthesize the following research into a clear, concise summary with key findings.', temperature: 0.3, max_tokens: 2000 } } },
      { id: 'wr6', type: 'output', position: { x: 1550, y: 200 }, data: { label: 'Output', config: {} } },
    ],
    edges: [
      { source: 'wr1', target: 'wr2' },
      { source: 'wr2', target: 'wr3' },
      { source: 'wr3', target: 'wr4' },
      { source: 'wr4', target: 'wr5' },
      { source: 'wr5', target: 'wr6' },
    ],
  },
  'File Summarizer': {
    name: 'File Summarizer',
    nodes: [
      { id: 'fs1', type: 'input', position: { x: 50, y: 200 }, data: { label: 'Input', config: { prompt: 'Summarize the document', input_type: 'file_upload', file_path: '' } } },
      { id: 'fs2', type: 'tool', position: { x: 350, y: 200 }, data: { label: 'Read File', config: { tool_name: 'read_file', params: {} } } },
      { id: 'fs3', type: 'llm', position: { x: 650, y: 200 }, data: { label: 'Summarizer', config: { model: 'llama3.1:8b', system_prompt: 'Summarize the following document concisely.', temperature: 0.3, max_tokens: 1000 } } },
      { id: 'fs4', type: 'output', position: { x: 950, y: 200 }, data: { label: 'Output', config: {} } },
    ],
    edges: [
      { source: 'fs1', target: 'fs2' },
      { source: 'fs2', target: 'fs3' },
      { source: 'fs3', target: 'fs4' },
    ],
  },
  'Multi-Step Research Report': {
    name: 'Multi-Step Research Report',
    nodes: [
      { id: 'ms1', type: 'input', position: { x: 50, y: 200 }, data: { label: 'Input', config: { prompt: 'Write a report on renewable energy trends', input_type: 'text' } } },
      { id: 'ms2', type: 'tool', position: { x: 350, y: 200 }, data: { label: 'Web Search', config: { tool_name: 'web_search', params: {} } } },
      { id: 'ms3', type: 'llm', position: { x: 650, y: 200 }, data: { label: 'Report Writer', config: { model: 'llama3.1:8b', system_prompt: 'Write a detailed, well-structured report based on the research.', temperature: 0.5, max_tokens: 3000 } } },
      { id: 'ms4', type: 'tool', position: { x: 950, y: 200 }, data: { label: 'Save Report', config: { tool_name: 'write_file', params: { file_path: 'report.txt' } } } },
      { id: 'ms5', type: 'output', position: { x: 1250, y: 200 }, data: { label: 'Output', config: {} } },
    ],
    edges: [
      { source: 'ms1', target: 'ms2' },
      { source: 'ms2', target: 'ms3' },
      { source: 'ms3', target: 'ms4' },
      { source: 'ms4', target: 'ms5' },
    ],
  },
  'Data Pipeline': {
    name: 'Data Pipeline',
    nodes: [
      { id: 'dp1', type: 'input', position: { x: 50, y: 200 }, data: { label: 'Input', config: { prompt: 'Process and analyze the following data', input_type: 'text' } } },
      { id: 'dp2', type: 'tool', position: { x: 350, y: 200 }, data: { label: 'Read CSV', config: { tool_name: 'csv_analyze', params: { operation: 'summary' } } } },
      { id: 'dp3', type: 'llm', position: { x: 650, y: 200 }, data: { label: 'Data Analyst', config: { model: 'llama3.1:8b', system_prompt: 'Analyze the CSV data summary. Identify trends, anomalies, and key insights. Provide a clear analysis.', temperature: 0.3, max_tokens: 2000 } } },
      { id: 'dp4', type: 'transform', position: { x: 950, y: 200 }, data: { label: 'Format Output', config: { transform_type: 'template', template: '## Data Analysis Report\n\n{{input}}' } } },
      { id: 'dp5', type: 'output', position: { x: 1250, y: 200 }, data: { label: 'Output', config: {} } },
    ],
    edges: [
      { source: 'dp1', target: 'dp2' },
      { source: 'dp2', target: 'dp3' },
      { source: 'dp3', target: 'dp4' },
      { source: 'dp4', target: 'dp5' },
    ],
  },
  'RAG Agent': {
    name: 'RAG Agent',
    nodes: [
      { id: 'rag1', type: 'input', position: { x: 50, y: 200 }, data: { label: 'Question', config: { prompt: 'What are the key benefits of using local AI models?', input_type: 'text' } } },
      { id: 'rag2', type: 'memory', position: { x: 350, y: 200 }, data: { label: 'Store Knowledge', config: { namespace: 'rag_kb', memory_type: 'long_term', action: 'remember' } } },
      { id: 'rag3', type: 'tool', position: { x: 350, y: 350 }, data: { label: 'Web Search', config: { tool_name: 'web_search', params: {} } } },
      { id: 'rag4', type: 'merge', position: { x: 650, y: 275 }, data: { label: 'Merge Context', config: { merge_mode: 'concat', separator: '\n\n---\n\n' } } },
      { id: 'rag5', type: 'llm', position: { x: 950, y: 275 }, data: { label: 'RAG Responder', config: { model: 'llama3.1:8b', system_prompt: 'You are a RAG assistant. Answer the question using the provided context from memory and web search. Cite your sources.', temperature: 0.3, max_tokens: 2000 } } },
      { id: 'rag6', type: 'output', position: { x: 1250, y: 275 }, data: { label: 'Output', config: {} } },
    ],
    edges: [
      { source: 'rag1', target: 'rag2' },
      { source: 'rag1', target: 'rag3' },
      { source: 'rag2', target: 'rag4' },
      { source: 'rag3', target: 'rag4' },
      { source: 'rag4', target: 'rag5' },
      { source: 'rag5', target: 'rag6' },
    ],
  },
  'Text Summarizer': {
    name: 'Text Summarizer',
    nodes: [
      { id: 'ts1', type: 'input', position: { x: 50, y: 200 }, data: { label: 'Input Text', config: { prompt: 'Paste text to summarize', input_type: 'text' } } },
      { id: 'ts2', type: 'guardrails', position: { x: 350, y: 200 }, data: { label: 'Validate', config: { validation_type: 'min_length', max_length: 50 } } },
      { id: 'ts3', type: 'llm', position: { x: 650, y: 200 }, data: { label: 'Summarizer', config: { model: 'llama3.1:8b', system_prompt: 'Provide a concise 3-bullet summary of the following text. Focus on key points.', temperature: 0.3, max_tokens: 500 } } },
      { id: 'ts4', type: 'transform', position: { x: 950, y: 200 }, data: { label: 'Format', config: { transform_type: 'template', template: '# Summary\n\n{{input}}' } } },
      { id: 'ts5', type: 'output', position: { x: 1250, y: 200 }, data: { label: 'Output', config: {} } },
    ],
    edges: [
      { source: 'ts1', target: 'ts2' },
      { source: 'ts2', target: 'ts3', sourceHandle: 'handle-valid' },
      { source: 'ts3', target: 'ts4' },
      { source: 'ts4', target: 'ts5' },
    ],
  },
};

export default examples;
