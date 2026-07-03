import LLMNode from '../components/nodes/LLMNode';
import ToolNode from '../components/nodes/ToolNode';
import MemoryNode from '../components/nodes/MemoryNode';
import InputNode from '../components/nodes/InputNode';
import OutputNodeComp from '../components/nodes/OutputNode';
import ConditionNode from '../components/nodes/ConditionNode';
import LoopNode from '../components/nodes/LoopNode';
import TransformNode from '../components/nodes/TransformNode';
import MergeNode from '../components/nodes/MergeNode';
import DelayNode from '../components/nodes/DelayNode';
import SwitchNode from '../components/nodes/SwitchNode';
import WebhookNode from '../components/nodes/WebhookNode';
import GuardrailsNode from '../components/nodes/GuardrailsNode';
import VariableNode from '../components/nodes/VariableNode';
import SubWorkflowNode from '../components/nodes/SubWorkflowNode';
import BatchNode from '../components/nodes/BatchNode';
import CustomNodeComp from '../components/nodes/CustomNode';
import WebhookOutputNode from '../components/nodes/WebhookOutputNode';

export const nodeTypes = {
  input: InputNode,
  llm: LLMNode,
  tool: ToolNode,
  memory: MemoryNode,
  condition: ConditionNode,
  loop: LoopNode,
  output: OutputNodeComp,
  transform: TransformNode,
  merge: MergeNode,
  delay: DelayNode,
  switch: SwitchNode,
  webhook: WebhookNode,
  guardrails: GuardrailsNode,
  variable: VariableNode,
  subworkflow: SubWorkflowNode,
  batch: BatchNode,
  custom: CustomNodeComp,
  webhook_output: WebhookOutputNode,
};

export const NODE_COLORS = {
  input: '#3B82F6',
  llm: '#8B5CF6',
  tool: '#F97316',
  memory: '#22C55E',
  condition: '#EAB308',
  loop: '#EC4899',
  output: '#6B7280',
  transform: '#06B6D4',
  merge: '#A78BFA',
  delay: '#6366F1',
  switch: '#F59E0B',
  webhook: '#10B981',
  guardrails: '#F43F5E',
  variable: '#D946EF',
  subworkflow: '#0EA5E9',
  batch: '#F472B6',
  custom: '#A3E635',
  webhook_output: '#F97316',
};

export function getDefaultConfig(type) {
  const defaults = {
    input: { prompt: '', input_type: 'text', file_path: '' },
    llm: { model: 'llama3.1:8b', system_prompt: 'You are a helpful assistant.', temperature: 0.7, max_tokens: 2000 },
    tool: { tool_name: 'web_search', params: {} },
    memory: { namespace: 'default', memory_type: 'long_term', action: 'remember', search_query: '' },
    condition: { condition: 'if output contains error' },
    loop: { max_iterations: 5, stop_condition: '' },
    output: {},
    transform: { transform_type: 'trim', pattern: '', replacement: '', template: '{{input}}' },
    merge: { merge_mode: 'concat', separator: '\n\n' },
    delay: { delay_seconds: 5 },
    switch: { switch_field: '', cases: '', default_case: 'default' },
    webhook: { webhook_url: '', method: 'POST', auth_token: '' },
    guardrails: { validation_type: 'not_empty', pattern: '', max_length: 5000, retry_on_fail: false, max_retries: 3 },
    variable: { variable_name: 'my_var', variable_value: '', variable_type: 'string', mode: 'set', default_value: '' },
    subworkflow: { subworkflow_json: '', pass_input: true },
    batch: { subworkflow_json: '', batch_mode: 'split_newline' },
    custom: { custom_code: 'def process(input, context):\n    return input', handler_name: 'process' },
    webhook_output: { webhook_url: '', method: 'POST', auth_token: '', auth_header: 'Authorization', content_type: 'application/json', custom_headers: '', include_context: false, retry_count: 3, retry_delay: 1 },
  };
  return defaults[type] || {};
}

let nodeId = 0;
export const getId = () => `node_${++nodeId}_${Date.now()}`;
export const setNodeId = (val) => { nodeId = val; };
