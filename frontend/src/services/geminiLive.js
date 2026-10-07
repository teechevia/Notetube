import { GoogleGenAI, Modality } from "@google/genai";

const MODEL = "gemini-3.1-flash-live-preview";

function base64ToInt16(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }

  return new Int16Array(
    bytes.buffer,
    bytes.byteOffset,
    Math.floor(bytes.byteLength / 2)
  );
}

function float32ToInt16(input) {
  const output = new Int16Array(input.length);

  for (let i = 0; i < input.length; i++) {
    const sample = Math.max(-1, Math.min(1, input[i]));
    output[i] = sample < 0
      ? sample * 0x8000
      : sample * 0x7fff;
  }

  return output;
}

function int16ToBase64(input) {
  const bytes = new Uint8Array(input.buffer);
  let binary = "";

  const chunkSize = 0x8000;

  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.subarray(
      i,
      Math.min(i + chunkSize, bytes.length)
    );

    binary += String.fromCharCode(...chunk);
  }

  return btoa(binary);
}

export async function createGeminiLiveSession({
  token,
  systemInstruction,
  tools = [],
  onToolCall,
  onUserTranscript,
  onInputTranscriptComplete,
  onModelTranscript,
  onTurnComplete,
  onError,
  onClose,
}) {
  const ai = new GoogleGenAI({
    apiKey: token,
    httpOptions: {
      apiVersion: "v1alpha",
    },
  });

  const audioContext = new AudioContext({
    sampleRate: 24000,
  });

  let nextPlaybackTime = audioContext.currentTime;
  const activeAudioSources = new Set();
  let microphoneContext = null;
  let microphoneStream = null;
  let microphoneSource = null;
  let processor = null;
  let session = null;

  const playAudioChunk = (base64Audio) => {
    const samples = base64ToInt16(base64Audio);

    const audioBuffer = audioContext.createBuffer(
      1,
      samples.length,
      24000
    );

    const channel = audioBuffer.getChannelData(0);

    for (let i = 0; i < samples.length; i++) {
      channel[i] = samples[i] / 32768;
    }

    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);

    const startTime = Math.max(
      audioContext.currentTime,
      nextPlaybackTime
    );

    activeAudioSources.add(source);
    source.onended = () => activeAudioSources.delete(source);

    source.start(startTime);
    nextPlaybackTime = startTime + audioBuffer.duration;
  };

  const stopPlayback = () => {
    for (const source of activeAudioSources) {
      try { source.stop(); } catch {}
      try { source.disconnect(); } catch {}
    }

    activeAudioSources.clear();
    nextPlaybackTime = audioContext.currentTime;
  };

  let inputTranscriptBuffer = ""; 
  let lastInputTranscript = "";
  let inputTranscriptGeneration = 0;
  let inputTranscriptTimer = null;
  let sessionActive = true;

  session = await ai.live.connect({
    model: MODEL,
    config: {
      responseModalities: [Modality.AUDIO],
      inputAudioTranscription: {},
      outputAudioTranscription: {},
      tools: tools.length > 0 ? [{ functionDeclarations: tools }] : undefined,
      toolConfig: tools.length > 0 ? {
        functionCallingConfig: {
          mode: "AUTO"
        }
      } : undefined,
      systemInstruction: systemInstruction ? {
        parts: [{ text: systemInstruction }]
      } : undefined
    },

    callbacks: {
      onopen: () => {
        console.log("LIVE_CONNECTED");
      },

      onmessage: async (message) => {
        console.debug("Gemini Live message:", {
          toolCall: !!message?.toolCall,
          serverContent: message?.serverContent
            ? Object.keys(message.serverContent)
            : [],
        });
        if (message.toolCall) {
          try {
            const functionResponses = [];

            for (const functionCall of message.toolCall.functionCalls || []) {
              console.log("LIVE_TOOL_CALL", functionCall.name, functionCall.args);

              const result = await onToolCall?.(
                functionCall.name,
                functionCall.args || {}
              );
console.log("LIVE_TOOL_RESULT");

              functionResponses.push({
                id: functionCall.id,
                name: functionCall.name,
                response: {
                  result: result ?? {},
                },
              });
            }

            if (functionResponses.length) {
              session.sendToolResponse({
                functionResponses,
              });
console.log("LIVE_TOOL_RESPONSE_SENT");
            }
          } catch (error) {
            console.error(
              "Gemini Live tool execution failed:",
              error
            );

            const functionResponses = [];

            for (const functionCall of message.toolCall.functionCalls || []) {
              functionResponses.push({
                id: functionCall.id,
                name: functionCall.name,
                response: {
                  result: {
                    error: "Unable to retrieve notebook information.",
                  },
                },
              });
            }

            if (functionResponses.length) {
              session.sendToolResponse({
                functionResponses,
              });
console.log("LIVE_TOOL_RESPONSE_SENT");
            }
          }

          return;
        }

        const content = message.serverContent;

        if (!content) return;

        if (content.interrupted) {
          console.debug(
            "Gemini Live interrupted ? stopping queued audio."
          );
          stopPlayback();
        }

        if (content.modelTurn?.parts) {
          for (const part of content.modelTurn.parts) {
            if (part.inlineData?.data) {
              console.log("LIVE_MODEL_AUDIO"); playAudioChunk(part.inlineData.data);
            }
          }
        }

        if (content.inputTranscription?.text) {
          const transcriptPart =
            content.inputTranscription.text.trim();

          if (
            transcriptPart &&
            transcriptPart !== lastInputTranscript
          ) {
            lastInputTranscript = transcriptPart;

            inputTranscriptBuffer +=
              (inputTranscriptBuffer ? " " : "") +
              transcriptPart;

            onUserTranscript?.(transcriptPart);

            console.debug(
              "Gemini Live input transcript fragment:",
              transcriptPart
            );

            if (inputTranscriptTimer) {
              clearTimeout(inputTranscriptTimer);
            }

            const generation = ++inputTranscriptGeneration;

            inputTranscriptTimer = setTimeout(async () => {
              if (generation !== inputTranscriptGeneration) {
                return;
              }

              const finalTranscript =
                inputTranscriptBuffer.trim();

              inputTranscriptBuffer = "";
              inputTranscriptTimer = null;
              lastInputTranscript = "";

              if (!finalTranscript || !onInputTranscriptComplete) {
                return;
              }

              try {
                console.log(
                  "========== NOTEBOOK RAG REQUEST =========="
                );
                console.log(
                  "Final transcript:",
                  finalTranscript
                );
                console.log(
                  "=========================================="
                );

                const notebookContext =
                  await onInputTranscriptComplete(finalTranscript);

                if (
                  notebookContext?.text &&
                  session &&
                  sessionActive
                ) {
                  console.log(
                    "========== INJECTING NOTEBOOK CONTEXT =========="
                  );

                  session.sendClientContent({
                    turns: [
                      {
                        role: "user",
                        parts: [
                          {
                            text: `The participant asked:

"${finalTranscript}"

Answer that question now using the following NoteTube notebook evidence. The evidence is authoritative for notebook-specific facts. Do not mention retrieval, injected context, RAG, APIs, or implementation details.

NOTEBOOK EVIDENCE:
${notebookContext.text}`,
                          },
                        ],
                      },
                    ],
                    turnComplete: true,
                  });
                }
              } catch (error) {
                console.error(
                  "Notebook RAG bridge failed:",
                  error
                );
              }
            }, 700);
          }
        }

        if (content.outputTranscription?.text) {
          onModelTranscript?.(
            content.outputTranscription.text
          );
        }

        if (content.turnComplete) {
          console.log("LIVE_TURN_COMPLETE"); onTurnComplete?.();
        }
      },

      onerror: (event) => {
        sessionActive = false;

        if (inputTranscriptTimer) {
          clearTimeout(inputTranscriptTimer);
          inputTranscriptTimer = null;
        }

        console.error("Gemini Live error:", event);
        onError?.(event);
      },

      onclose: (event) => {
        sessionActive = false;

        if (inputTranscriptTimer) {
          clearTimeout(inputTranscriptTimer);
          inputTranscriptTimer = null;
        }

        try {
          processor?.disconnect();
        } catch {}

        console.debug(
          "Gemini Live closed:",
          event?.reason || "closed"
        );
        onClose?.(event);
      },
    },

    config: {
      responseModalities: [Modality.AUDIO],

      inputAudioTranscription: {},
      outputAudioTranscription: {},

      tools: tools.length
        ? [{ functionDeclarations: tools }]
        : undefined,
systemInstruction: systemInstruction || undefined,
    },
  });

  const startMicrophone = async () => {
    microphoneStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    microphoneContext = new AudioContext({
      sampleRate: 16000,
    });

    microphoneSource =
      microphoneContext.createMediaStreamSource(
        microphoneStream
      );

    processor = microphoneContext.createScriptProcessor(
      4096,
      1,
      1
    );

    processor.onaudioprocess = (event) => {
      if (!session || !sessionActive) return;

      const inputData =
        event.inputBuffer.getChannelData(0);

      const pcm = float32ToInt16(inputData);
      const base64Audio = int16ToBase64(pcm);

      try {
        session.sendRealtimeInput({
          audio: {
            data: base64Audio,
            mimeType: "audio/pcm;rate=16000",
          },
        });
      } catch (error) {
        console.warn(
          "Live audio send stopped:",
          error?.message || error
        );

        processor?.disconnect();
      }
    };

    microphoneSource.connect(processor);
    processor.connect(microphoneContext.destination);
  };

  const sendText = (text) => {
    if (!session || !sessionActive || !text.trim()) return;

    session.sendRealtimeInput({
      text: text.trim(),
    });
  };

  const stopMicrophone = () => {
    processor?.disconnect();
    microphoneSource?.disconnect();

    microphoneStream?.getTracks().forEach(
      (track) => track.stop()
    );

    microphoneContext?.close();

    processor = null;
    microphoneSource = null;
    microphoneStream = null;
    microphoneContext = null;
  };

  const close = () => {
    sessionActive = false;

    if (inputTranscriptTimer) {
      clearTimeout(inputTranscriptTimer);
      inputTranscriptTimer = null;
    }

    stopMicrophone();
    stopPlayback();

    if (session) {
      session.close();
      session = null;
    }

    audioContext.close();
  };

  await startMicrophone();

  return {
    sendText,
    stopMicrophone,
    close,
  };
}






