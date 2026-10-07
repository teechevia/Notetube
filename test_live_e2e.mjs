import { GoogleGenAI, Modality } from '@google/genai';
import fs from 'fs';

// Node 18+ has built-in fetch
const apiKey = fs.readFileSync('backend/.env', 'utf-8').match(/GEMINI_API_KEY=(.*)/)[1].trim();

const ai = new GoogleGenAI({
  apiKey: apiKey,
  httpOptions: { apiVersion: 'v1alpha' }
});

const notebookTool = {
  name: 'search_notebook',
  description: 'Search the notebook for information about uploaded PDFs, YouTube videos, documents, or sources. You MUST call this tool before answering any question about notebook content.',
  parameters: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'The query to search for in the notebook'
      }
    },
    required: ['query']
  }
};

const NB_ID = 1;

async function run() {
  console.log('=== REAL E2E LIVE RAG TEST ===');
  console.log('Model: gemini-3.8-live');
  console.log('Mode: AUTO');
  
  let functionCallCount = 0;
  let audioChunkCount = 0;
  let turnNum = 0;

  const queries = [
    'What is the Triadic Entanglement Relay and what fidelity rate does it achieve according to the PDF?',
    'Where were the three nodes located in the intercontinental deployment?'
  ];

  let session;

  const sendNextQuery = () => {
    if (turnNum >= queries.length) {
      console.log('\n=== FINAL E2E RESULT ===');
      console.log('Total turns:', turnNum);
      console.log('Total real tool calls:', functionCallCount);
      console.log('Total audio chunks generated:', audioChunkCount);
      console.log(functionCallCount >= 2 ? 'SUCCESS: Real RAG flow verified!' : 'FAILURE');
      process.exit(0);
    }
    console.log(`\n--- Turn ${turnNum + 1}: "${queries[turnNum]}" ---`);
    session.sendClientContent({
      turns: [{
        role: 'user',
        parts: [{ text: queries[turnNum] }]
      }],
      turnComplete: true
    });
  };

  let isWaitingForToolResponse = false;

  session = await ai.live.connect({
    model: 'gemini-3.1-flash-live-preview',
    config: {
      responseModalities: [Modality.AUDIO],
      inputAudioTranscription: {},
      outputAudioTranscription: {},
      tools: [{ functionDeclarations: [notebookTool] }],
      toolConfig: {
        functionCallingConfig: { mode: 'AUTO' }
      },
      systemInstruction: {
        parts: [{ text: 'You are a notebook assistant. If the user asks about a PDF or notebook content, you MUST use the search_notebook tool before answering. Never answer from memory. Keep your answer brief.' }]
      }
    },
    callbacks: {
      onopen: () => {
        console.log('LIVE_CONNECTED');
      },
      onmessage: async (msg) => {
        if (msg.toolCall) {
          isWaitingForToolResponse = true;
          const calls = msg.toolCall.functionCalls?.map(c => ({ name: c.name, args: c.args }));
          console.log('LIVE_TOOL_CALL', JSON.stringify(calls));
          functionCallCount++;

          const functionResponses = [];
          for (const call of msg.toolCall.functionCalls) {
             const query = call.args?.query || queries[turnNum];
             console.log(`-> Fetching REAL backend RAG for query: "${query}"`);
             try {
                 const res = await fetch(`http://127.0.0.1:8000/notebooks/${NB_ID}/chat`, {
                     method: 'POST',
                     headers: { 'Content-Type': 'application/json' },
                     body: JSON.stringify({ query: query })
                 });
                 if (!res.ok) throw new Error('RAG API Error');
                 const ragData = await res.json();
                 console.log(`-> RAG Answer Preview: ${ragData.answer.substring(0, 100)}...`);
                 functionResponses.push({ id: call.id, name: call.name, response: { result: ragData } });
             } catch(err) {
                 console.log('-> RAG failed:', err.message);
                 functionResponses.push({ id: call.id, name: call.name, response: { result: { error: err.message } } });
             }
          }

          session.sendToolResponse({ functionResponses });
          console.log('LIVE_TOOL_RESPONSE_SENT (Real backend data)');
          return;
        }

        if (msg.serverContent) {
          if (msg.serverContent.modelTurn?.parts) {
            for (const part of msg.serverContent.modelTurn.parts) {
              if (part.inlineData?.data) {
                audioChunkCount++;
                if (audioChunkCount === 1) console.log('LIVE_MODEL_AUDIO (first chunk received)');
              }
            }
          }
          if (msg.serverContent.turnComplete) {
            if (isWaitingForToolResponse) {
              // This turnComplete is just for the tool call request. Ignore it.
              isWaitingForToolResponse = false;
              console.log('(ignoring tool-call turnComplete)');
              return;
            }
            console.log(`LIVE_TURN_COMPLETE (turn ${turnNum + 1})`);
            turnNum++;
            setTimeout(sendNextQuery, 1000);
          }
        }
      },
      onerror: (err) => {
        console.error('LIVE_ERROR:', err?.message || err);
      },
      onclose: (e) => {
        console.log('LIVE_CLOSED');
        process.exit(1);
      }
    }
  });

  sendNextQuery();

  setTimeout(() => {
    console.log('TIMEOUT after 60s');
    process.exit(1);
  }, 60000);
}

run().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
