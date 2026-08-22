import { useState, useEffect } from "react";
import axios from "axios";
import { BookOpen, Plus, FileText, Link as LinkIcon, Video, MessageSquare, Layout, Sparkles, Send, Brain, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

function App() {
  const [sources, setSources] = useState([]);
  const [chat, setChat] = useState([]);
  const [input, setInput] = useState("");
  const [showAddSource, setShowAddSource] = useState(false);
  const [newSourceUrl, setNewSourceUrl] = useState("");
  const [newSourceType, setNewSourceType] = useState("youtube");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/sources");
      setSources(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddSource = async (e) => {
    e.preventDefault();
    if (!newSourceUrl) return;
    
    setLoading(true);
    try {
      await axios.post("http://127.0.0.1:8000/sources", { url: newSourceUrl, type: newSourceType });
      setNewSourceUrl("");
      setShowAddSource(false);
      fetchSources();
    } catch (e) {
      alert("Failed to add source");
    }
    setLoading(false);
  };

  const handleDeleteSource = async (id, e) => {
    e.stopPropagation();
    try {
      await axios.delete(`http://127.0.0.1:8000/sources/${id}`);
      fetchSources();
    } catch (e) {
      alert("Failed to delete source");
    }
  };

  const handleChat = async () => {
    if (!input) return;
    const userMsg = input;
    setChat([...chat, { role: "user", text: userMsg }]);
    setInput("");
    
    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", { query: userMsg });
      setChat(prev => [...prev, { role: "ai", text: res.data.answer }]);
    } catch (e) {
      setChat(prev => [...prev, { role: "ai", text: "Error connecting to AI." }]);
    }
  };

  return (
    <div className="flex h-screen bg-[#f3f3f3] text-slate-900 font-sans overflow-hidden">
      
      {/* LEFT SIDEBAR: SOURCES */}
      <div className="w-80 bg-white border-r border-slate-200 flex flex-col shadow-sm z-10">
        <div className="p-6 border-b border-slate-100 flex items-center gap-3">
          <BookOpen className="w-8 h-8 text-indigo-600" />
          <h1 className="text-2xl font-bold tracking-tight">NoteTube</h1>
        </div>
        
        <div className="p-4 flex-1 overflow-y-auto">
          <div className="flex items-center justify-between mb-4 px-2">
            <h2 className="text-sm font-bold text-slate-500 uppercase tracking-wider">Sources ({sources.length})</h2>
            <button onClick={() => setShowAddSource(!showAddSource)} className="p-1 hover:bg-slate-100 rounded-full text-slate-500 transition-colors">
              <Plus className="w-5 h-5" />
            </button>
          </div>

          {showAddSource && (
            <div className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-200 shadow-inner">
              <div className="flex gap-2 mb-3">
                <button onClick={() => setNewSourceType("youtube")} className={`flex-1 py-1.5 text-xs font-bold rounded-md ${newSourceType === "youtube" ? "bg-white shadow border border-slate-200 text-indigo-600" : "text-slate-500"}`}>YouTube</button>
                <button onClick={() => setNewSourceType("url")} className={`flex-1 py-1.5 text-xs font-bold rounded-md ${newSourceType === "url" ? "bg-white shadow border border-slate-200 text-indigo-600" : "text-slate-500"}`}>Website</button>
                <button onClick={() => setNewSourceType("pdf")} className={`flex-1 py-1.5 text-xs font-bold rounded-md ${newSourceType === "pdf" ? "bg-white shadow border border-slate-200 text-indigo-600" : "text-slate-500"}`}>PDF</button>
              </div>
              <form onSubmit={handleAddSource}>
                <input 
                  type="text" 
                  placeholder={newSourceType === "pdf" ? "Upload PDF coming soon..." : "Paste link here..."} 
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 mb-2"
                  value={newSourceUrl}
                  onChange={(e) => setNewSourceUrl(e.target.value)}
                  disabled={newSourceType === "pdf"}
                />
                <button type="submit" disabled={newSourceType === "pdf"} className="w-full py-2 bg-indigo-600 text-white text-sm font-bold rounded-lg hover:bg-indigo-700 disabled:opacity-50">Add Source</button>
              </form>
            </div>
          )}

          <div className="space-y-2">
            {sources.length === 0 ? (
              <div className="text-center p-6 text-slate-400 border-2 border-dashed border-slate-200 rounded-xl mt-4">
                <Plus className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm font-medium">Add sources to create your notebook.</p>
              </div>
            ) : (
              sources.map(s => (
                <div key={s.id} className="group flex items-center gap-3 p-3 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer relative">
                  <div className="p-2 bg-slate-50 rounded-lg text-slate-500">
                    {s.type === "youtube" ? <Video className="w-5 h-5 text-red-500" /> : s.type === "url" ? <LinkIcon className="w-5 h-5 text-blue-500" /> : <FileText className="w-5 h-5 text-orange-500" />}
                  </div>
                  <div className="flex-1 min-w-0 pr-8">
                    <p className="text-sm font-bold text-slate-800 truncate">{s.title}</p>
                    <p className="text-xs text-slate-400 truncate">{s.url}</p>
                  </div>
                  <button onClick={(e) => handleDeleteSource(s.id, e)} className="absolute right-3 opacity-0 group-hover:opacity-100 p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-all">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col relative min-w-0 min-h-0">
        <header className="h-16 border-b border-slate-200 bg-white/50 backdrop-blur-sm flex items-center px-8 shrink-0">
          <h2 className="text-lg font-bold text-slate-700 flex items-center gap-2">
            <Layout className="w-5 h-5" /> Notebook Guide
          </h2>
        </header>

        {sources.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 min-h-0">
            <Sparkles className="w-16 h-16 text-indigo-200 mb-6" />
            <h2 className="text-3xl font-bold text-slate-800 mb-4">Welcome to NoteTube</h2>
            <p className="text-lg text-slate-500 max-w-lg text-center mb-8">
              Upload documents, paste web links, or drop YouTube videos into the Sources panel to start chatting, generating podcasts, and building your study guide.
            </p>
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0 max-w-4xl w-full mx-auto p-4 md:p-8">
            <div className="flex-1 overflow-y-auto bg-white border border-slate-200 rounded-2xl shadow-sm p-6 mb-6 space-y-6">
              {chat.length === 0 ? (
                <div className="p-4">
                  <h3 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2"><Sparkles className="w-6 h-6 text-indigo-500"/> Notebook Guide</h3>
                  
                  <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 mb-8">
                    <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">Audio Overview</h4>
                    <div className="flex items-center justify-between">
                      <p className="text-slate-700 text-sm">Two-person deep dive podcast about your sources.</p>
                      <button className="px-4 py-2 bg-indigo-600 text-white text-sm font-bold rounded-lg hover:bg-indigo-700">Generate Podcast</button>
                    </div>
                  </div>

                  <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">Suggested Formats</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <button className="p-4 bg-white border border-slate-200 rounded-xl hover:border-indigo-500 hover:shadow-md transition-all text-left group">
                      <FileText className="w-6 h-6 text-blue-500 mb-3 group-hover:scale-110 transition-transform" />
                      <h5 className="font-bold text-slate-800">Briefing Doc</h5>
                      <p className="text-xs text-slate-500 mt-1">A structured summary of all sources.</p>
                    </button>
                    <button className="p-4 bg-white border border-slate-200 rounded-xl hover:border-indigo-500 hover:shadow-md transition-all text-left group">
                      <BookOpen className="w-6 h-6 text-green-500 mb-3 group-hover:scale-110 transition-transform" />
                      <h5 className="font-bold text-slate-800">Flashcards</h5>
                      <p className="text-xs text-slate-500 mt-1">Key terms and definitions to study.</p>
                    </button>
                    <button className="p-4 bg-white border border-slate-200 rounded-xl hover:border-indigo-500 hover:shadow-md transition-all text-left group">
                      <Layout className="w-6 h-6 text-orange-500 mb-3 group-hover:scale-110 transition-transform" />
                      <h5 className="font-bold text-slate-800">Quiz</h5>
                      <p className="text-xs text-slate-500 mt-1">Multiple choice questions.</p>
                    </button>
                    <button className="p-4 bg-white border border-slate-200 rounded-xl hover:border-indigo-500 hover:shadow-md transition-all text-left group">
                      <MessageSquare className="w-6 h-6 text-purple-500 mb-3 group-hover:scale-110 transition-transform" />
                      <h5 className="font-bold text-slate-800">FAQ</h5>
                      <p className="text-xs text-slate-500 mt-1">Frequently asked questions.</p>
                    </button>
                  </div>
                </div>
              ) : (
                chat.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`p-4 max-w-[80%] rounded-2xl ${msg.role === "user" ? "bg-indigo-100 text-indigo-900 rounded-br-none" : "bg-slate-100 text-slate-800 rounded-bl-none"}`}>
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* CHAT INPUT */}
            <div className="bg-white border border-slate-200 rounded-2xl p-2 shadow-lg flex items-center shrink-0 relative focus-within:ring-2 focus-within:ring-indigo-500">
              <input 
                type="text" 
                placeholder="Ask a question about your sources, or type '/' for formats (Podcast, Quiz, etc)..." 
                className="flex-1 px-4 py-3 outline-none text-slate-700 bg-transparent"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleChat()}
              />
              <button onClick={handleChat} className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors">
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}

export default App;
