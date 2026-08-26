import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import {
  FileText, MessageSquare, Layout, Plus, Search,
  Settings, Share2, BarChart2, Copy, File, Link, X,
  Mic, Video, BookOpen, Layers, Lightbulb, PieChart,
  ArrowRight, ArrowLeft, Sparkles, BrainCircuit, PlayCircle, MoreVertical
} from 'lucide-react';

const YoutubeIcon = () => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
    <path d="M21.58 7.19c-.23-.86-.91-1.54-1.77-1.77C18.25 5 12 5 12 5s-6.25 0-7.81.42c-.86.23-1.54.91-1.77 1.77C2 8.75 2 12 2 12s0 3.25.42 4.81c.23.86.91 1.54 1.77 1.77C5.75 19 12 19 12 19s6.25 0 7.81-.42c.86-.23 1.54-.91 1.77-1.77C22 15.25 22 12 22 12s0-3.25-.42-4.81zM10 15V9l5.2 3-5.2 3z"/>
  </svg>
);

const NoteTubeLogo = () => (
  <div className="relative flex items-center justify-center w-8 h-8 bg-gradient-to-br from-indigo-500 to-rose-500 rounded-lg shadow-lg shadow-indigo-500/20">
    <PlayCircle className="w-5 h-5 text-slate-900 dark:text-white" fill="currentColor" strokeWidth={1} />
  </div>
);

function Workspace() {
  const { id: notebookId } = useParams();
  const navigate = useNavigate();

  const [sources, setSources] = useState([]);
  const [input, setInput] = useState("");
  const [chat, setChat] = useState([]);
  const [selectedSources, setSelectedSources] = useState([]);
  const [initialLoad, setInitialLoad] = useState(true);
  const [showAddSource, setShowAddSource] = useState(false);
  const [newSourceUrl, setNewSourceUrl] = useState("");
  const [newSourceType, setNewSourceType] = useState("youtube");
  const [loading, setLoading] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  const [voiceA, setVoiceA] = useState("en-US-ChristopherNeural");
  const [voiceB, setVoiceB] = useState("en-US-JennyNeural");
  const [podcastInstruction, setPodcastInstruction] = useState("");
  const [isLivePodcastMode, setIsLivePodcastMode] = useState(false);
  const [showNotification, setShowNotification] = useState(true);
  const [isHeaderVisible, setIsHeaderVisible] = useState(true);
  const lastScrollY = useRef(0);

  const handleChatScroll = (e) => {
    if (!isMobile) return;
    const { scrollTop, scrollHeight, clientHeight } = e.target;

    // Prevent infinite loop when layout changes near the bottom
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;

    if (scrollTop > 60 && scrollTop > lastScrollY.current + 5) {
      if (isHeaderVisible) setIsHeaderVisible(false);
    } else if (scrollTop < lastScrollY.current - 15 || scrollTop < 10) {
      // Only show header on scroll up if we are NOT pinned to the bottom.
      // (Because shrinking the header increases clientHeight, which forces scrollTop to decrease when at the bottom, creating a fake "scroll up" event).
      if (!isHeaderVisible && !isAtBottom) setIsHeaderVisible(true);
      if (!isHeaderVisible && scrollTop < 10) setIsHeaderVisible(true);
    }
    lastScrollY.current = scrollTop;
  };

  const isMobile = typeof window !== 'undefined' && window.innerWidth < 1024;
  const [showLeftSidebar, setShowLeftSidebar] = useState(!isMobile);
  const [showRightSidebar, setShowRightSidebar] = useState(!isMobile);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const fetchChatHistory = async () => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/notebooks/${notebookId}/chat_history`);
      if (res.data && res.data.length > 0) {
        setChat(res.data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setInitialLoad(false);
    }
  };

  useEffect(() => {
    fetchSources();
    fetchChatHistory();
  }, []);

  useEffect(() => {
    if (!initialLoad) {
      axios.post(`http://127.0.0.1:8000/notebooks/${notebookId}/chat_history`, { messages: chat }).catch(console.error);
    }
  }, [chat, initialLoad, notebookId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chat]);

  const [isDarkMode, setIsDarkMode] = useState(true);

  // Apply dark mode to document body
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const fetchSources = async () => {
    const res = await axios.get(`http://127.0.0.1:8000/notebooks/${notebookId}/sources`);
    setSources(res.data);
  };

  const handleNewWorkspace = () => {
    navigate('/');
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await axios.post(`http://127.0.0.1:8000/notebooks/${notebookId}/sources/file`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setShowAddSource(false);
      fetchSources();
    } catch (err) {
      alert("Failed to upload file");
    }
    setLoading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleMockAction = (action) => {
    alert(`${action} feature coming soon!`);
  };

  const handleAddSource = async (e) => {
    e.preventDefault();
    if (!newSourceUrl) return;

    setLoading(true);
    try {
      if (newSourceType === "pdf") {
        const formData = new FormData();
        formData.append("file", newSourceUrl);
        await axios.post(`http://127.0.0.1:8000/notebooks/${notebookId}/sources/file`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        await axios.post(`http://127.0.0.1:8000/notebooks/${notebookId}/sources`, { url: newSourceUrl, type: newSourceType });
      }
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
    setSources(sources.filter(s => s.id !== id));
    setSelectedSources(prev => prev.filter(sid => sid !== id));
    try {
      await axios.delete(`http://127.0.0.1:8000/notebooks/${notebookId}/sources/${id}`);
    } catch (err) {
      console.error(err);
      fetchSources();
    }
  };

  const handleChat = async (presetText = null) => {
    const userMsg = presetText || input;
    if (!userMsg) return;

    setChat(prev => [...prev, { role: "user", text: userMsg }]);
    if (!presetText) setInput("");

    if (isLivePodcastMode) {
      setChat(prev => [...prev, { role: "ai", text: "*Hosts are tuning in...*" }]);

      const getHostName = (voiceStr) => {
        const match = voiceStr.match(/-(.+)Neural/);
        return match ? match[1] : "Host";
      };

      const hostA = getHostName(voiceA);
      const hostB = getHostName(voiceB);

      const recentHistory = chat.slice(-6).map(m => `${m.role === 'user' ? 'User' : 'Hosts'}: ${m.text}`).join('\n');

      try {
        const res = await axios.post(`http://127.0.0.1:8000/notebooks/${notebookId}/studio/podcast/interact`, {
          message: userMsg,
          chat_history: recentHistory,
          host_a_name: hostA,
          host_b_name: hostB,
          voice_a: voiceA,
          voice_b: voiceB
        });

        let content = res.data.content;
        let transcript = "";
        content.forEach(line => {
          transcript += `**${line.speaker}:** ${line.text}\n\n`;
        });

        setChat(prev => {
          const newChat = [...prev];
          newChat[newChat.length - 1] = { role: "ai", text: `*Generating Studio Audio...*` };
          return newChat;
        });

        const audioRes = await axios.post(`http://127.0.0.1:8000/notebooks/${notebookId}/studio/podcast/audio`, {
          script: content,
          voice_a: voiceA,
          voice_b: voiceB,
          host_a_name: hostA,
          host_b_name: hostB
        }, { responseType: 'blob' });

        const audioUrl = URL.createObjectURL(audioRes.data);

        setChat(prev => {
          const newChat = [...prev];
          newChat[newChat.length - 1] = { role: "ai", text: transcript, audioUrl };
          return newChat;
        });

      } catch (e) {
        setChat(prev => {
          const newChat = [...prev];
          newChat[newChat.length - 1] = { role: "ai", text: "Error interacting with live podcast." };
          return newChat;
        });
      }
    } else {
      try {
        const res = await axios.post(`http://127.0.0.1:8000/notebooks/${notebookId}/chat`, { query: userMsg, source_ids: selectedSources });
        setChat(prev => [...prev, { role: "ai", text: res.data.answer }]);
      } catch (e) {
        setChat(prev => [...prev, { role: "ai", text: "Error connecting to AI." }]);
      }
    }
  };

  const handleGenerateStudio = async (format) => {
    setLoading(true);
    const formatName = format === 'podcast' ? 'Audio Overview' : format === 'briefing' ? 'Briefing Doc' : format === 'study_guide' ? 'Study Guide' : format === 'timeline' ? 'Timeline' : format === 'toc' ? 'Table of Contents' : 'FAQ';

    const getHostName = (voiceStr) => {
      const match = voiceStr.match(/-(.+)Neural/);
      return match ? match[1] : "Host";
    };

    const hostA = getHostName(voiceA);
    const hostB = getHostName(voiceB);

    const requestText = format === 'podcast' && podcastInstruction
      ? `Generate an ${formatName}. Focus on: ${podcastInstruction}`
      : `Generate a ${formatName}`;

    setChat(prev => [...prev, { role: "user", text: requestText }, { role: "ai", text: `Generating your ${formatName}... please wait (this might take a few seconds).` }]);

    try {
      // Mapping the NotebookLM requests to our backend generator functions
      let backendFormat = format;
      if (format === 'study_guide') backendFormat = 'flashcards'; // We'll re-use flashcards prompt logic for Study Guide internally or just use text
      if (format === 'timeline' || format === 'toc') backendFormat = 'human_notes';

      const res = await axios.post(`http://127.0.0.1:8000/notebooks/${notebookId}/studio/generate`, {
        format: backendFormat,
        instruction: podcastInstruction,
        host_a_name: hostA,
        host_b_name: hostB,
        source_ids: selectedSources
      });
      let content = res.data.content;

      let markdownText = "";

      if (backendFormat === 'flashcards' && Array.isArray(content)) {
        markdownText = "### Study Guide\n\n";
        content.forEach((c, i) => {
          markdownText += `**Topic: ${c.front}**\n\n*Details: ${c.back}*\n\n---\n\n`;
        });
      } else if (format === 'podcast') {
        let transcript = "";
        content.forEach(line => {
          transcript += `**${line.speaker}:** ${line.text}\n\n`;
        });

        setChat(prev => {
          const newChat = [...prev];
          newChat[newChat.length - 1] = { role: "ai", text: `*Generating Audio... (This takes about 15-30 seconds, do not close!)*` };
          return newChat;
        });

        const audioRes = await axios.post(`http://127.0.0.1:8000/notebooks/${notebookId}/studio/podcast/audio`, {
          script: content,
          voice_a: voiceA,
          voice_b: voiceB,
          host_a_name: hostA,
          host_b_name: hostB
        }, { responseType: 'blob' });

        const audioUrl = URL.createObjectURL(audioRes.data);

        setChat(prev => {
          const newChat = [...prev];
          newChat[newChat.length - 1] = { role: "ai", text: transcript, audioUrl };
          return newChat;
        });

        setLoading(false);
        return;
      } else {
        markdownText = content;
      }

      setChat(prev => {
        const newChat = [...prev];
        newChat[newChat.length - 1] = { role: "ai", text: markdownText };
        return newChat;
      });
    } catch (e) {
      console.error(e);
      let errMsg = "Error generating content. Make sure you have sources added!";
      if (e.response && e.response.data && e.response.data.detail) {
        errMsg = `Error: ${e.response.data.detail}`;
      } else if (e.message) {
        errMsg = `Network/Client Error: ${e.message}`;
      }

      setChat(prev => {
        const newChat = [...prev];
        newChat[newChat.length - 1] = { role: "ai", text: errMsg };
        return newChat;
      });
    }
    setLoading(false);
  };

  return (
    <div className={`fixed inset-0 h-screen w-full flex flex-col font-sans select-none overflow-hidden transition-colors duration-300 ${isDarkMode ? 'bg-[#131314] text-[#E3E3E3] selection:bg-[#A8C7FA]/30' : 'bg-[#F0F4F9] text-[#1F1F1F] selection:bg-[#0B57D0]/30'}`}>

      {/* HEADER */}
      <header className="h-[64px] flex items-center justify-between px-5 shrink-0 border-b border-slate-200/40 dark:border-[#2D2E30]/60 bg-slate-50 dark:bg-black/80 backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <NoteTubeLogo />
          <h1 className="text-[16px] hidden sm:block font-semibold text-slate-900 dark:text-white tracking-wide">NoteTube Workspace</h1>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleNewWorkspace} className="flex items-center gap-2 px-2 sm:px-4 py-1.5 bg-indigo-500 text-white font-medium text-sm rounded-full hover:bg-indigo-400 transition-colors mr-1 sm:mr-2 shadow-lg shadow-indigo-500/20">
            <ArrowLeft className="w-4 h-4" /> <span className="hidden sm:inline">Dashboard</span></button>

          {/* Theme Toggle Button */}
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 dark:bg-[#2D2E30] dark:bg-neutral-700/50 hover:bg-slate-200 dark:hover:bg-[#3C3D3F] transition-colors sm:mr-1 border border-slate-200 dark:border-[#3C3D3F]/50"
            title="Toggle Light/Dark Mode"
          >
            {isDarkMode ? (
              <svg className="w-4 h-4 text-amber-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>

          <div className="hidden md:flex items-center gap-2">
            <button onClick={() => handleMockAction("Clone Workspace")} className="flex items-center gap-2 px-3 py-1.5 text-sm text-indigo-300 hover:bg-slate-100 dark:bg-[#2D2E30] rounded-full transition-colors border border-slate-200 dark:border-[#3C3D3F]/50" title="Clone"><Copy className="w-4 h-4" /> <span>Clone</span></button>
            <button onClick={() => handleMockAction("Analytics")} className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-700 dark:text-neutral-300 hover:bg-slate-100 dark:bg-[#2D2E30] rounded-full transition-colors" title="Stats"><BarChart2 className="w-4 h-4" /> <span>Stats</span></button>
            <button onClick={() => handleMockAction("Share")} className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-700 dark:text-neutral-300 hover:bg-slate-100 dark:bg-[#2D2E30] rounded-full transition-colors" title="Share"><Share2 className="w-4 h-4" /> <span>Share</span></button>
            <button onClick={() => handleMockAction("Settings")} className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-700 dark:text-neutral-300 hover:bg-slate-100 dark:bg-[#2D2E30] rounded-full transition-colors" title="Settings"><Settings className="w-4 h-4" /> <span>Settings</span></button>
          </div>

          <div className="relative md:hidden">
            <button onClick={() => setShowMobileMenu(!showMobileMenu)} className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-slate-200 dark:hover:bg-[#3C3D3F] transition-colors text-slate-600 dark:text-neutral-400">
              <MoreVertical className="w-5 h-5" />
            </button>
            {showMobileMenu && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-[#252628] rounded-xl shadow-xl border border-slate-200 dark:border-[#3C3D3F] py-2 z-50">
                <button onClick={() => { setShowMobileMenu(false); handleMockAction("Clone Workspace"); }} className="w-full text-left px-4 py-2.5 text-sm text-indigo-500 hover:bg-slate-50 dark:hover:bg-[#2D2E30] flex items-center gap-3 font-medium"><Copy className="w-4 h-4" /> Clone</button>
                <button onClick={() => { setShowMobileMenu(false); handleMockAction("Analytics"); }} className="w-full text-left px-4 py-2.5 text-sm text-slate-700 dark:text-neutral-300 hover:bg-slate-50 dark:hover:bg-[#2D2E30] flex items-center gap-3"><BarChart2 className="w-4 h-4" /> Stats</button>
                <button onClick={() => { setShowMobileMenu(false); handleMockAction("Share"); }} className="w-full text-left px-4 py-2.5 text-sm text-slate-700 dark:text-neutral-300 hover:bg-slate-50 dark:hover:bg-[#2D2E30] flex items-center gap-3"><Share2 className="w-4 h-4" /> Share</button>
                <button onClick={() => { setShowMobileMenu(false); handleMockAction("Settings"); }} className="w-full text-left px-4 py-2.5 text-sm text-slate-700 dark:text-neutral-300 hover:bg-slate-50 dark:hover:bg-[#2D2E30] flex items-center gap-3"><Settings className="w-4 h-4" /> Settings</button>
              </div>
            )}
          </div>
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-rose-500 to-orange-500 flex items-center justify-center text-slate-900 dark:text-white text-sm font-medium ml-2 cursor-pointer shadow-md" onClick={() => handleMockAction("Profile")}>
            P
          </div>
        </div>
      </header>

      {/* MAIN LAYOUT */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-y-auto scrollbar-hide lg:overflow-hidden p-3 gap-3 bg-slate-50 dark:bg-black">

        {/* LEFT SIDEBAR: SOURCES */}
        {/* LEFT SIDEBAR: SOURCES */}
        <>
          <div className={`fixed inset-y-0 left-0 z-50 w-full sm:w-[320px] lg:static lg:w-[300px] bg-slate-50 dark:bg-[#1E1F20] lg:bg-white/80 lg:dark:bg-[#1E1F20]/80 border-r border-slate-200/40 dark:border-[#2D2E30]/30 lg:border lg:rounded-[24px] flex flex-col overflow-hidden shrink-0 shadow-2xl lg:shadow-lg transition-transform duration-300 ease-in-out ${showLeftSidebar ? 'translate-x-0' : '-translate-x-full lg:hidden pointer-events-none'}`}>
            <div className="p-5 flex items-center justify-between border-b border-slate-200/40 dark:border-[#2D2E30]/30">
              <h2 className="text-[15px] font-semibold text-slate-900 dark:text-white">Knowledge Base</h2>
              <button onClick={() => setShowLeftSidebar(false)} className="p-1.5 hover:bg-slate-100 dark:bg-[#2D2E30] rounded-lg transition-colors"><Layout className="w-4 h-4 text-slate-400 dark:text-neutral-500 dark:text-neutral-400" /></button>
            </div>

            <div className="p-4">
              <button
                onClick={() => setShowAddSource(true)}
                className="w-full py-2.5 px-4 border border-dashed border-slate-300 dark:border-neutral-600 hover:border-indigo-400 hover:bg-indigo-500/10 rounded-xl flex items-center justify-center gap-2 text-sm text-slate-700 dark:text-neutral-300 hover:text-indigo-300 font-medium transition-all"
              >
                <Plus className="w-4 h-4" />
                Add Sources
              </button>
            </div>

            <div className="flex-1 overflow-y-auto scrollbar-hide px-3">
              {sources.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center p-6 opacity-60">
                  <File className="w-10 h-10 mb-4 text-indigo-400 opacity-50" />
                  <p className="text-sm font-medium text-slate-700 dark:text-neutral-300">Your vault is empty</p>
                  <p className="text-xs mt-2 text-slate-400 dark:text-neutral-500 leading-relaxed">Add YouTube videos, PDFs, or web links to start generating notes.</p>
                </div>
              ) : (
                <div className="space-y-2 pb-4">
                  {sources.map(s => (
                    <div key={s.id} onClick={() => {
                      if (selectedSources.includes(s.id)) setSelectedSources(selectedSources.filter(id => id !== s.id));
                      else setSelectedSources([...selectedSources, s.id]);
                    }} className="group flex flex-col p-3 rounded-xl bg-slate-50/50 dark:bg-[#2D2E30]/50 border border-slate-200 dark:border-[#3C3D3F]/50 cursor-pointer hover:bg-slate-100 dark:bg-[#2D2E30] hover:border-indigo-500/30 transition-all">
                      <div className="flex items-center gap-3">
                        <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer shrink-0 mr-2" checked={selectedSources.includes(s.id)} onChange={(e) => { if (e.target.checked) setSelectedSources([...selectedSources, s.id]); else setSelectedSources(selectedSources.filter(id => id !== s.id)); }} onClick={(e) => e.stopPropagation()} />
                          {(() => {
                            const t = s.type;
                            if (t === 'youtube') return <YoutubeIcon className="text-rose-500 w-5 h-5" />;
                            if (t === 'pdf') return <File className="w-5 h-5 text-red-400" />;
                            if (t === 'docx') return <FileText className="w-5 h-5 text-blue-500" />;
                            if (t === 'pptx') return <PieChart className="w-5 h-5 text-orange-500" />;
                            if (t === 'txt' || t === 'md') return <FileText className="w-5 h-5 text-slate-400" />;
                            if (t === 'audio' || t === 'mp3' || t === 'wav') return <Mic className="w-5 h-5 text-emerald-500" />;
                            return <Link className="w-5 h-5 text-emerald-400" />;
                        })()}
                        <span className="text-[13px] truncate font-medium flex-1 text-slate-800 dark:text-neutral-200">{s.title || s.url}</span>
                        <button onClick={(e) => handleDeleteSource(s.id, e)} className="opacity-100 lg:opacity-0 lg:group-hover:opacity-100 p-1.5 hover:bg-slate-200 dark:hover:bg-[#3C3D3F] rounded-md transition-all ml-auto shrink-0 z-10" aria-label="Delete source">
                          <X className="w-3.5 h-3.5 text-slate-400 dark:text-neutral-500 dark:text-neutral-400 hover:text-rose-400" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          {!isMobile && !showLeftSidebar && (
            <div className="hidden lg:flex w-14 bg-white/80 dark:bg-[#1E1F20]/80 border border-slate-200/40 dark:border-[#2D2E30]/30 rounded-[20px] flex-col items-center py-5 shrink-0 shadow-lg cursor-pointer hover:bg-slate-100 dark:bg-[#2D2E30] transition-all" onClick={() => setShowLeftSidebar(true)}>
              <Layout className="w-5 h-5 text-slate-400 dark:text-neutral-500 dark:text-neutral-400" />
            </div>
          )}
        </>

        {/* MIDDLE: CHAT */}
        <div className="flex-1 min-h-0 min-w-0 bg-white/80 dark:bg-[#1E1F20]/80 border border-slate-200/40 dark:border-[#2D2E30]/30 lg:rounded-[24px] flex flex-col relative overflow-x-hidden overflow-y-hidden shadow-lg">
          <div className={`flex items-center justify-between shrink-0 transition-all duration-300 ease-in-out overflow-hidden ${isMobile ? (isHeaderVisible ? 'p-5 max-h-[80px] opacity-100 border-b border-slate-200/40 dark:border-[#2D2E30]/30' : 'p-0 max-h-0 opacity-0 border-transparent') : 'p-5 max-h-[80px] opacity-100 border-b border-slate-200/40 dark:border-[#2D2E30]/30'}`}>
            <button onClick={() => setShowLeftSidebar(true)} className="lg:hidden p-1.5 hover:bg-slate-100 dark:hover:bg-[#2D2E30] rounded-lg transition-colors"><Layout className="w-5 h-5 text-slate-500" /></button>
              <h2 className="text-[15px] font-semibold text-slate-900 dark:text-white">Interactive Session</h2>
              <button onClick={() => setShowRightSidebar(true)} className="lg:hidden p-1.5 hover:bg-slate-100 dark:hover:bg-[#2D2E30] rounded-lg transition-colors"><Settings className="w-5 h-5 text-slate-500" /></button>
          </div>

          <div className="flex-1 overflow-y-auto scrollbar-hide p-4 md:p-8 select-text flex flex-col" onScroll={handleChatScroll}>
            {chat.length === 0 ? (
              <div className="flex flex-col max-w-2xl mx-auto py-8 md:py-16">
                <div className="w-16 h-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center mb-6 border border-indigo-500/20">
                  <PlayCircle className="w-8 h-8 text-indigo-400" />
                </div>
                <h1 className="text-[32px] font-semibold mb-4 text-slate-900 dark:text-white tracking-tight">Welcome to NoteTube.</h1>
                <p className="text-slate-400 dark:text-neutral-500 dark:text-neutral-400 mb-10 text-[16px] max-w-xl leading-relaxed">
                  Your intelligent workspace for YouTube videos, PDFs, and web articles.
                  Drop in your sources and let NoteTube help you summarize, learn, and create.
                </p>
                <p className="font-medium text-sm mb-5 text-slate-700 dark:text-neutral-300">What would you like to explore today?</p>
                <div className="flex flex-col sm:flex-row flex-wrap gap-3 items-start">
                  <button onClick={() => handleChat("Summarize the key takeaways from my sources")} className="px-5 py-2.5 rounded-full bg-slate-50 dark:bg-[#252628] hover:bg-slate-100 dark:hover:bg-[#2D2E30] border border-slate-200/60 dark:border-[#3C3D3F]/30 text-[13.5px] font-medium text-slate-700 dark:text-neutral-300 transition-colors">
                    Summarize key takeaways
                  </button>
                  <button onClick={() => handleChat("Create a study guide from these videos")} className="px-5 py-2.5 rounded-full bg-slate-50 dark:bg-[#252628] hover:bg-slate-100 dark:hover:bg-[#2D2E30] border border-slate-200/60 dark:border-[#3C3D3F]/30 text-[13.5px] font-medium text-slate-700 dark:text-neutral-300 transition-colors">
                    Generate a study guide
                  </button>
                  <button onClick={() => handleChat("Test my knowledge with a quick quiz")} className="px-5 py-2.5 rounded-full bg-slate-50 dark:bg-[#252628] hover:bg-slate-100 dark:hover:bg-[#2D2E30] border border-slate-200/60 dark:border-[#3C3D3F]/30 text-[13.5px] font-medium text-slate-700 dark:text-neutral-300 transition-colors">
                    Test my knowledge
                  </button>
                </div>
              </div>
            ) : (
              <div className="max-w-3xl mx-auto space-y-8 pb-40">
                {chat.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    {msg.role === "user" ? (
                      <div className="bg-indigo-600 px-5 py-3.5 rounded-2xl rounded-tr-sm max-w-[80%] text-[15px] leading-relaxed text-white shadow-md">
                        {msg.text}
                      </div>
                    ) : (
                      <div className="flex gap-4 w-full">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-rose-500 flex items-center justify-center shrink-0 mt-1 shadow-lg shadow-indigo-500/20">
                          <Sparkles className="w-4 h-4 text-slate-900 dark:text-white" />
                        </div>
                        {msg.audioUrl ? (
                          <div className="flex-1 mt-1.5 w-full">
                            <p className="font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                              <Mic className="w-4 h-4 text-rose-400" /> Deep Dive Podcast Ready
                            </p>
                            <audio controls src={msg.audioUrl} className="w-full max-w-md outline-none rounded-xl h-12 mb-4 bg-slate-100 dark:bg-[#2D2E30] shadow-inner" />
                            <details className="text-xs text-indigo-400 cursor-pointer w-full group">
                              <summary className="font-medium hover:text-indigo-300 mb-2 outline-none select-none">View Transcript</summary>
                              <div className="text-slate-700 dark:text-neutral-300 prose prose-sm dark:prose-invert max-w-none mt-3 p-5 bg-slate-100/80 dark:bg-[#2D2E30]/80 rounded-xl border border-slate-200 dark:border-[#3C3D3F]/50 leading-relaxed">
                                <ReactMarkdown>{msg.text}</ReactMarkdown>
                              </div>
                            </details>
                          </div>
                        ) : (
                          <div className="text-slate-800 dark:text-neutral-200 prose dark:prose-invert max-w-none flex-1 mt-1 break-words leading-relaxed text-[15px]">
                            <ReactMarkdown>{msg.text}</ReactMarkdown>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* CHAT INPUT BLOCK */}
          <div className="p-4 w-full max-w-3xl mx-auto shrink-0 z-20">

            {/* Notification Bubble */}
            {showNotification && (
              <div className="mb-4 mx-auto w-fit max-w-[95%] bg-indigo-50 dark:bg-indigo-500/10 text-indigo-800 dark:text-indigo-300 border border-indigo-500/20 rounded-2xl sm:rounded-full px-4 sm:px-5 py-2.5 flex items-center gap-2 sm:gap-3 text-xs shadow-lg font-medium cursor-pointer transition-opacity backdrop-blur-md" onClick={() => setShowNotification(false)}>
                <Sparkles className="w-4 h-4 text-rose-400" />
                <span className="flex-1 text-center sm:text-left leading-relaxed">NoteTube 2.0 is here! Try out the new Interactive Live Podcast mode.</span>
                <button className="ml-2 hover:text-slate-900 dark:text-white"><X className="w-3 h-3" /></button>
              </div>
            )}

            {/* The Input Pill */}
            <div className="bg-slate-100 dark:bg-[#2D2E30]/90 backdrop-blur-xl border border-slate-200/60 dark:border-[#3C3D3F]/40 rounded-[32px] shadow-xl sm:shadow-2xl flex flex-col focus-within:bg-slate-100 dark:bg-[#2D2E30] transition-colors relative">
              {isLivePodcastMode && (
                 <div className="px-5 pb-2 pt-3 flex justify-between items-center border-b border-slate-200 dark:border-[#3C3D3F]/50">
                    <span className="text-[11px] uppercase tracking-wider font-bold text-rose-400 flex items-center gap-2">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                      </span>
                      Live Podcast Session Active
                    </span>
                 </div>
              )}
              <div className="flex items-center px-2 py-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleChat()}
                  placeholder={isLivePodcastMode ? "Join the conversation..." : "Ask a question or create something from your notes"}
                  className="flex-1 min-w-0 bg-transparent px-2 sm:px-4 py-2 outline-none text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-neutral-500 text-[14px] sm:text-[15px]"
                />
                <div className="flex items-center gap-3 pr-2">
                  <span className="text-xs text-slate-400 dark:text-neutral-500 font-medium hidden sm:block">{(selectedSources.length === 0 ? sources.length : selectedSources.length)} sources active</span>
                  <button
                    onClick={() => handleChat()}
                    disabled={!input.trim()}
                    className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-slate-900 dark:text-white hover:bg-indigo-500 disabled:opacity-30 disabled:bg-slate-700 transition-all shadow-md"
                  >
                    <ArrowRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT SIDEBAR: STUDIO */}
        {/* RIGHT SIDEBAR: STUDIO */}
        <>
          <div className={`fixed inset-y-0 right-0 z-50 w-full sm:w-[340px] lg:static lg:w-[340px] bg-slate-50 dark:bg-[#1E1F20] lg:bg-white/80 lg:dark:bg-[#1E1F20]/80 border-l border-slate-200/40 dark:border-[#2D2E30]/30 lg:border lg:rounded-[24px] flex flex-col min-h-0 overflow-hidden shrink-0 shadow-2xl lg:shadow-lg transition-transform duration-300 ease-in-out ${showRightSidebar ? 'translate-x-0' : 'translate-x-full lg:hidden pointer-events-none'}`}>
            <div className={`flex items-center justify-between shrink-0 transition-all duration-300 ease-in-out overflow-hidden ${isMobile ? (isHeaderVisible ? 'p-5 max-h-[80px] opacity-100 border-b border-slate-200/40 dark:border-[#2D2E30]/30' : 'p-0 max-h-0 opacity-0 border-transparent') : 'p-5 max-h-[80px] opacity-100 border-b border-slate-200/40 dark:border-[#2D2E30]/30'}`}>
              <h2 className="text-[15px] font-semibold text-slate-900 dark:text-white">NoteTube Studio</h2>
              <button onClick={() => setShowRightSidebar(false)} className="p-1.5 hover:bg-slate-100 dark:bg-[#2D2E30] rounded-lg transition-colors"><Layout className="w-4 h-4 text-slate-400 dark:text-neutral-500 dark:text-neutral-400" /></button>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto scrollbar-hide px-4 pb-8 space-y-4">

              {/* Audio Overview Gradient Card */}
              <div onClick={() => handleGenerateStudio('podcast')} className="w-full mt-4 bg-gradient-to-br from-indigo-100 to-rose-50 dark:from-indigo-900/40 dark:to-rose-900/20 border border-indigo-500/20 rounded-2xl p-5 cursor-pointer hover:border-indigo-500/40 transition-all shadow-md relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-full blur-2xl -mr-10 -mt-10 transition-transform group-hover:scale-150"></div>
                <h3 className="text-[15px] font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                  <Mic className="w-4 h-4 text-rose-400" /> Deep Dive Podcast
                </h3>
                  <p className="text-[13px] text-indigo-900/70 dark:text-indigo-200/70 leading-relaxed">
                    Turn your sources into a lifelike two-person conversation.
                  </p>
              </div>

              {/* Studio Action Grid */}
              <div className="grid grid-cols-2 gap-3 mt-4">

                <button onClick={() => handleGenerateStudio('faq')} className="flex flex-col bg-slate-50/50 dark:bg-[#2D2E30]/50 hover:bg-slate-100 dark:bg-[#2D2E30] border border-slate-200 dark:border-[#3C3D3F]/50 hover:border-purple-500/30 rounded-2xl p-4 text-left transition-all relative overflow-hidden group">
                  <BookOpen className="w-6 h-6 text-purple-400 mb-5" />
                  <span className="text-[13px] font-semibold text-slate-800 dark:text-neutral-200">FAQ</span>
                  <ArrowRight className="w-4 h-4 absolute bottom-4 right-4 text-slate-600 group-hover:text-purple-400 transition-colors" />
                </button>

                <button onClick={() => handleGenerateStudio('study_guide')} className="flex flex-col bg-slate-50/50 dark:bg-[#2D2E30]/50 hover:bg-slate-100 dark:bg-[#2D2E30] border border-slate-200 dark:border-[#3C3D3F]/50 hover:border-rose-500/30 rounded-2xl p-4 text-left transition-all relative overflow-hidden group">
                  <Layers className="w-6 h-6 text-rose-400 mb-5" />
                  <span className="text-[13px] font-semibold text-slate-800 dark:text-neutral-200">Study Guide</span>
                  <ArrowRight className="w-4 h-4 absolute bottom-4 right-4 text-slate-600 group-hover:text-rose-400 transition-colors" />
                </button>

                <button onClick={() => handleGenerateStudio('toc')} className="flex flex-col bg-slate-50/50 dark:bg-[#2D2E30]/50 hover:bg-slate-100 dark:bg-[#2D2E30] border border-slate-200 dark:border-[#3C3D3F]/50 hover:border-cyan-500/30 rounded-2xl p-4 text-left transition-all relative overflow-hidden group">
                  <Layout className="w-6 h-6 text-cyan-400 mb-5" />
                  <span className="text-[13px] font-semibold text-slate-800 dark:text-neutral-200">Table of Contents</span>
                  <ArrowRight className="w-4 h-4 absolute bottom-4 right-4 text-slate-600 group-hover:text-cyan-400 transition-colors" />
                </button>

                <button onClick={() => handleGenerateStudio('timeline')} className="flex flex-col bg-slate-50/50 dark:bg-[#2D2E30]/50 hover:bg-slate-100 dark:bg-[#2D2E30] border border-slate-200 dark:border-[#3C3D3F]/50 hover:border-amber-500/30 rounded-2xl p-4 text-left transition-all relative overflow-hidden group">
                  <PieChart className="w-6 h-6 text-amber-400 mb-5" />
                  <span className="text-[13px] font-semibold text-slate-800 dark:text-neutral-200">Timeline</span>
                  <ArrowRight className="w-4 h-4 absolute bottom-4 right-4 text-slate-600 group-hover:text-amber-400 transition-colors" />
                </button>

                <button onClick={() => handleGenerateStudio('briefing')} className="flex flex-col bg-slate-50/50 dark:bg-[#2D2E30]/50 hover:bg-slate-100 dark:bg-[#2D2E30] border border-slate-200 dark:border-[#3C3D3F]/50 hover:border-emerald-500/30 rounded-2xl p-4 text-left transition-all relative overflow-hidden group">
                  <FileText className="w-6 h-6 text-emerald-400 mb-5" />
                  <span className="text-[13px] font-semibold text-slate-800 dark:text-neutral-200">Briefing Doc</span>
                  <ArrowRight className="w-4 h-4 absolute bottom-4 right-4 text-slate-600 group-hover:text-emerald-400 transition-colors" />
                </button>

              </div>

              <div className="mt-8 text-center px-4">
                <p className="text-[11px] text-slate-400 dark:text-neutral-500 leading-relaxed uppercase tracking-widest font-medium">
                  NoteTube Studio Engine
                </p>
              </div>

              {/* Custom Settings / Live Podcast Mode */}
              <div className="mt-6 border-t border-slate-200 dark:border-[#2D2E30]/80 pt-6">
                <h4 className="text-[12px] font-semibold text-slate-700 dark:text-neutral-300 mb-5 flex items-center gap-2">
                  <Settings className="w-4 h-4 text-slate-400 dark:text-neutral-500 dark:text-neutral-400" /> Podcast Configuration
                </h4>
                <div className="space-y-4 bg-slate-50/30 dark:bg-[#2D2E30]/30 p-4 rounded-2xl border border-slate-300 dark:border-[#3C3D3F]/30">
                  <label className="flex items-center justify-between cursor-pointer group">
                    <span className="text-sm font-medium text-slate-700 dark:text-neutral-300 group-hover:text-slate-900 dark:text-white transition-colors">Live Podcast Mode</span>
                    <div className={`w-11 h-6 rounded-full relative transition-colors shadow-inner ${isLivePodcastMode ? 'bg-indigo-500' : 'bg-slate-700'}`} onClick={() => setIsLivePodcastMode(!isLivePodcastMode)}>
                      <div className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform shadow-sm ${isLivePodcastMode ? 'translate-x-5' : 'translate-x-0'}`}></div>
                    </div>
                  </label>

                  <div className="pt-2 border-t border-slate-200 dark:border-[#3C3D3F]/50">
                    <label className="text-[11px] font-medium text-slate-400 dark:text-neutral-500 uppercase tracking-wider mb-2 block">Host 1 Voice</label>
                    <select value={voiceA} onChange={(e) => setVoiceA(e.target.value)} className="w-full bg-slate-100 dark:bg-[#2D2E30] text-[13px] text-slate-800 dark:text-neutral-200 p-2.5 rounded-xl outline-none border border-slate-300 dark:border-[#3C3D3F] focus:border-indigo-500 hover:bg-slate-200 dark:hover:bg-[#3C3D3F] transition-colors appearance-none shadow-sm cursor-pointer">
                      <option value="en-US-ChristopherNeural">Christopher (Professional)</option>
                      <option value="en-US-GuyNeural">Guy (Casual)</option>
                      <option value="en-US-SteffanNeural">Steffan (Deep)</option>
                      <option value="en-US-JennyNeural">Jenny (Clear)</option>
                      <option value="en-US-AriaNeural">Aria (Soft)</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] font-medium text-slate-400 dark:text-neutral-500 uppercase tracking-wider mb-2 block">Host 2 Voice</label>
                    <select value={voiceB} onChange={(e) => setVoiceB(e.target.value)} className="w-full bg-slate-100 dark:bg-[#2D2E30] text-[13px] text-slate-800 dark:text-neutral-200 p-2.5 rounded-xl outline-none border border-slate-300 dark:border-[#3C3D3F] focus:border-indigo-500 hover:bg-slate-200 dark:hover:bg-[#3C3D3F] transition-colors appearance-none shadow-sm cursor-pointer">
                      <option value="en-US-JennyNeural">Jenny (Clear)</option>
                      <option value="en-US-AriaNeural">Aria (Soft)</option>
                      <option value="en-US-MichelleNeural">Michelle (Bright)</option>
                      <option value="en-US-ChristopherNeural">Christopher (Professional)</option>
                      <option value="en-US-GuyNeural">Guy (Casual)</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] font-medium text-slate-400 dark:text-neutral-500 uppercase tracking-wider mb-2 block">Director's Notes</label>
                    <input
                      type="text"
                      placeholder="E.g., Explain it to a 5-year old"
                      value={podcastInstruction}
                      onChange={(e) => setPodcastInstruction(e.target.value)}
                      className="w-full bg-slate-100 dark:bg-[#2D2E30] text-[13px] text-slate-800 dark:text-neutral-200 p-2.5 rounded-xl outline-none border border-slate-300 dark:border-[#3C3D3F] focus:border-indigo-500 hover:bg-slate-200 dark:hover:bg-[#3C3D3F] placeholder-slate-400 dark:placeholder-neutral-500 transition-colors shadow-sm"
                    />
                  </div>
                </div>
              </div>

            </div>
          </div>
          {!isMobile && !showRightSidebar && (
            <div className="hidden lg:flex w-14 bg-white/80 dark:bg-[#1E1F20]/80 border border-slate-200/40 dark:border-[#2D2E30]/30 rounded-[24px] flex-col items-center py-4 shrink-0 shadow-lg transition-all space-y-3">
              <button onClick={() => handleGenerateStudio('podcast')} className="p-2 hover:bg-slate-100 dark:hover:bg-[#2D2E30] rounded-xl transition-colors group relative" title="Deep Dive Podcast">
                <Mic className="w-5 h-5 text-rose-400 group-hover:text-rose-500" />
              </button>
              <button onClick={() => handleGenerateStudio('faq')} className="p-2 hover:bg-slate-100 dark:hover:bg-[#2D2E30] rounded-xl transition-colors group relative" title="FAQ">
                <BookOpen className="w-5 h-5 text-purple-400 group-hover:text-purple-500" />
              </button>
              <button onClick={() => handleGenerateStudio('study_guide')} className="p-2 hover:bg-slate-100 dark:hover:bg-[#2D2E30] rounded-xl transition-colors group relative" title="Study Guide">
                <Layers className="w-5 h-5 text-rose-400 group-hover:text-rose-500" />
              </button>
              <button onClick={() => handleGenerateStudio('toc')} className="p-2 hover:bg-slate-100 dark:hover:bg-[#2D2E30] rounded-xl transition-colors group relative" title="Table of Contents">
                <Layout className="w-5 h-5 text-cyan-400 group-hover:text-cyan-500" />
              </button>
              <button onClick={() => handleGenerateStudio('timeline')} className="p-2 hover:bg-slate-100 dark:hover:bg-[#2D2E30] rounded-xl transition-colors group relative" title="Timeline">
                <PieChart className="w-5 h-5 text-amber-400 group-hover:text-amber-500" />
              </button>
              <button onClick={() => handleGenerateStudio('briefing')} className="p-2 hover:bg-slate-100 dark:hover:bg-[#2D2E30] rounded-xl transition-colors group relative" title="Briefing Doc">
                <FileText className="w-5 h-5 text-emerald-400 group-hover:text-emerald-500" />
              </button>
              <div className="w-8 border-t border-slate-200/40 dark:border-[#2D2E30]/50 my-1"></div>
              <button onClick={() => setShowRightSidebar(true)} className="p-2 hover:bg-slate-100 dark:hover:bg-[#2D2E30] rounded-xl transition-colors group relative" title="Studio Settings">
                <Settings className="w-5 h-5 text-slate-400 dark:text-neutral-500 group-hover:text-slate-600 dark:group-hover:text-neutral-300" />
              </button>
            </div>
          )}
        </>

      </div>

      {/* ADD SOURCE MODAL OVERLAY */}
      {showAddSource && (
        <div className="fixed inset-0 bg-slate-50 dark:bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#1E1F20] w-full max-w-2xl rounded-[24px] border border-slate-300 dark:border-[#3C3D3F] shadow-2xl flex flex-col overflow-hidden">
            <div className="flex justify-end p-4 pb-0">
              <button onClick={() => setShowAddSource(false)} className="p-2 hover:bg-slate-100 dark:bg-[#2D2E30] rounded-full text-slate-400 dark:text-neutral-500 dark:text-neutral-400 hover:text-slate-900 dark:text-white transition-colors"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-10 pt-4 text-center">
              <div className="w-16 h-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-indigo-500/20">
                <PlayCircle className="w-8 h-8 text-indigo-400" />
              </div>
              <h2 className="text-[26px] font-semibold mb-2 text-slate-900 dark:text-white">
                Import to NoteTube
              </h2>
              <p className="text-slate-400 dark:text-neutral-500 dark:text-neutral-400 mb-10">Transform your videos and documents into interactive study material.</p>

              <form onSubmit={handleAddSource} className="max-w-lg mx-auto">
                <div className="bg-slate-50/50 dark:bg-[#2D2E30]/50 border border-slate-300 dark:border-[#3C3D3F] rounded-2xl p-2 mb-6 shadow-sm">
                  <div className="text-left px-3 py-2 text-xs font-medium text-slate-400 dark:text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">Add via URL</div>
                  <div className="flex items-center bg-white dark:bg-[#1E1F20] rounded-xl px-4 py-3 border border-slate-200 dark:border-[#3C3D3F]/50 focus-within:border-indigo-500 transition-colors">
                    <select value={newSourceType} onChange={(e)=>setNewSourceType(e.target.value)} className="bg-transparent text-sm font-medium outline-none text-indigo-400 border-r border-slate-300 dark:border-[#3C3D3F] pr-3 mr-3 appearance-none cursor-pointer">
                      <option value="youtube">YouTube ▾</option>
                      <option value="pdf">Web / PDF ▾</option>
                    </select>
                    <input
                      type="text"
                      placeholder="Paste your link here..."
                      value={newSourceUrl}
                      onChange={(e) => setNewSourceUrl(e.target.value)}
                      className="flex-1 bg-transparent text-[15px] outline-none text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-neutral-500"
                    />
                    <button type="submit" disabled={loading} className="p-2 bg-indigo-600 rounded-lg text-slate-900 dark:text-white hover:bg-indigo-500 transition-colors disabled:opacity-50 shadow-md">
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="border-2 border-dashed border-slate-300 dark:border-[#3C3D3F] hover:border-indigo-500/50 transition-colors rounded-[24px] p-10 flex flex-col items-center justify-center gap-4 bg-slate-50/20 dark:bg-[#2D2E30]/20">
                  <div className="text-[17px] font-medium text-slate-800 dark:text-neutral-200">Upload Local Files</div>
                  <div className="text-sm text-slate-400 dark:text-neutral-500">PDFs, Word Docs, Text files, and more</div>
                  <div className="flex gap-3 mt-4">
                    <input
                      type="file"
                      accept=".pdf,.txt,.md,.docx,.pptx,.mp3,.wav"
                      className="hidden"
                      ref={fileInputRef}
                      onChange={handleFileUpload}
                    />
                    <button type="button" onClick={() => fileInputRef.current?.click()} className="px-5 py-2.5 bg-slate-100 dark:bg-[#2D2E30] border border-slate-300 dark:border-[#3C3D3F] rounded-full text-[13px] font-semibold flex items-center gap-2 hover:bg-slate-200 dark:hover:bg-[#3C3D3F] text-slate-800 dark:text-neutral-200 transition-all shadow-sm">
                      <File className="w-4 h-4 text-indigo-400" /> Choose Files
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}



class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  render() {
    if (this.state.hasError) {
      return <div className="p-10 text-red-500 bg-white min-h-screen"><h1>Error:</h1><pre>{this.state.error.toString()}</pre></div>;
    }
    return this.props.children;
  }
}

export default function WorkspaceWrapper() {
  return <ErrorBoundary><Workspace /></ErrorBoundary>;
}
