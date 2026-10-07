import { GoogleGenAI } from '@google/genai';
import path from 'path';
import fs from 'fs';

const envContent = fs.readFileSync('../backend/.env', 'utf-8');
const keyMatch = envContent.match(/GEMINI_API_KEY=(.*)/);
const apiKey = keyMatch ? keyMatch[1] : '';

const MODEL = 'gemini-2.0-flash-exp';

const ai = new GoogleGenAI({
  apiKey: apiKey,
  httpOptions: { apiVersion: 'v1alpha' }
});

const notebookTool = {
  name: 'search_notebook',
  description: 'MANDATORY NOTEBOOK SEARCH TOOL. Before answering any question that could relate to uploaded PDFs, YouTube videos, documents, sources, or notebook content, you MUST call this tool first. Never answer notebook-content questions from memory or guess. Use the returned notebook evidence to formulate the answer.',
  parameters: {
    type: 'object',
    properties: {
      query: { type: 'string', description: 'The query' }
    },
    required: ['query']
  }
};

async function run() {
  console.log('Connecting...');
  
  let functionCallCount = 0;

  const session = await ai.live.connect({
    model: MODEL,
    config: {
      tools: [{ functionDeclarations: [notebookTool] }],
      toolConfig: {
        functionCallingConfig: {
          mode: 'AUTO'
        }
      },
      systemInstruction: { parts: [{ text: 'If the user asks about a PDF, you MUST use the search_notebook tool.' }] }
    },
    callbacks: {
      onopen: () => {
        console.log('LIVE_CONNECTED');
      },
      onmessage: (msg) => {
        if (msg.toolCall) {
          console.log('LIVE_TOOL_CALL', JSON.stringify(msg.toolCall));
          functionCallCount++;
          session.sendToolResponse({
            functionResponses: msg.toolCall.functionCalls.map(c => ({
              id: c.id,
              name: c.name,
              response: { result: { notebook_answer: 'The PDF is about artificial intelligence.' } }
            }))
          });
          console.log('LIVE_TOOL_RESPONSE_SENT');
        }
        if (msg.serverContent) {
          if (msg.serverContent.modelTurn) {
            console.log('LIVE_MODEL_TURN_RECEIVED');
          }
          if (msg.serverContent.turnComplete) {
            console.log('LIVE_TURN_COMPLETE');
            if (functionCallCount === 0) {
              console.log('FAILURE: Tool was NOT called in AUTO mode.');
            } else {
              console.log('SUCCESS: Tool was called!');
            }
            process.exit(0);
          }
        }
      },
      onerror: (err) => console.error('Error:', err)
    }
  });

  console.log('Sending text: What is the main idea of the PDF I just shared?');
  session.sendRealtimeInput({ text: 'What is the main idea of the PDF I just shared?' });
}
run().catch(console.error);
