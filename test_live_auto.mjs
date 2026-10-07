import { GoogleGenAI, Modality } from '@google/genai';
import fs from 'fs';

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

async function run() {
  console.log('=== MULTI-TURN TOOL CALL TEST ===');
  console.log('');

  let turnNum = 0;
  let functionCallCount = 0;
  let audioChunkCount = 0;
  let outputTranscript = '';

  const queries = [
    'What is the main idea of the PDF I just shared?',
    'Can you explain that in simpler terms?',
  ];

  const toolResults = [
    'The PDF discusses machine learning fundamentals including supervised learning, neural networks, and gradient descent optimization.',
    'Machine learning is when computers learn from data. Supervised learning means giving the computer examples with answers. Neural networks are inspired by the brain. Gradient descent helps find the best answer step by step.',
  ];

  let session;

  const sendNextQuery = () => {
    if (turnNum >= queries.length) {
      console.log('');
      console.log('=== FINAL RESULT ===');
      console.log('Total turns:', turnNum);
      console.log('Total tool calls:', functionCallCount);
      console.log('Output transcript:', outputTranscript || '(none - expected for text input)');
      console.log(functionCallCount >= 1 ? 'SUCCESS' : 'FAILURE');
      process.exit(0);
    }
    console.log('');
    console.log(`--- Turn ${turnNum + 1}: "${queries[turnNum]}" ---`);
    session.sendClientContent({
      turns: [{
        role: 'user',
        parts: [{ text: queries[turnNum] }]
      }],
      turnComplete: true
    });
  };

  session = await ai.live.connect({
    model: 'gemini-3.8-live',
    config: {
      responseModalities: [Modality.AUDIO],
      inputAudioTranscription: {},
      outputAudioTranscription: {},
      tools: [{ functionDeclarations: [notebookTool] }],
      toolConfig: {
        functionCallingConfig: {
          mode: 'AUTO',
        }
      },
      systemInstruction: {
        parts: [{
          text: 'You are a notebook assistant. If the user asks about a PDF or notebook content, you MUST use the search_notebook tool before answering. Never answer from memory. Keep your answer brief.'
        }]
      }
    },
    callbacks: {
      onopen: () => {
        console.log('LIVE_CONNECTED');
      },
      onmessage: (msg) => {
        if (msg.toolCall) {
          const calls = msg.toolCall.functionCalls?.map(c => ({ name: c.name, args: c.args }));
          console.log('LIVE_TOOL_CALL', JSON.stringify(calls));
          functionCallCount++;

          session.sendToolResponse({
            functionResponses: msg.toolCall.functionCalls.map(c => ({
              id: c.id,
              name: c.name,
              response: {
                result: {
                  notebook_answer: toolResults[turnNum] || toolResults[0]
                }
              }
            }))
          });
          console.log('LIVE_TOOL_RESPONSE_SENT');
          return;
        }

        if (msg.serverContent) {
          if (msg.serverContent.modelTurn?.parts) {
            for (const part of msg.serverContent.modelTurn.parts) {
              if (part.inlineData?.data) {
                audioChunkCount++;
              }
            }
          }

          if (msg.serverContent.outputTranscription?.text) {
            outputTranscript += msg.serverContent.outputTranscription.text;
          }

          if (msg.serverContent.turnComplete) {
            console.log('LIVE_TURN_COMPLETE (turn', turnNum + 1, ')');
            console.log('  Tool calls so far:', functionCallCount);
            console.log('  Audio chunks so far:', audioChunkCount);
            turnNum++;
            // Small delay before next turn
            setTimeout(sendNextQuery, 500);
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
