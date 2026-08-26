import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Book, Plus, Trash2, Sun, Moon } from 'lucide-react';

export default function Dashboard() {
  const [notebooks, setNotebooks] = useState([]);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchNotebooks();
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const fetchNotebooks = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/notebooks");
      setNotebooks(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const createNotebook = async () => {
    const title = prompt("Enter Notebook Title:");
    if (!title) return;
    try {
      await axios.post("http://127.0.0.1:8000/notebooks", { title, description: "" });
      fetchNotebooks();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteNotebook = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this notebook?")) return;
    try {
      await axios.delete(`http://127.0.0.1:8000/notebooks/${id}`);
      fetchNotebooks();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#131314] text-gray-900 dark:text-gray-100 flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-[#2D2E30] bg-white dark:bg-[#1E1F20]">
        <div className="flex items-center gap-2">
          <Book className="w-6 h-6 text-blue-500" />
          <h1 className="text-xl font-semibold">NoteTube</h1>
        </div>
        <button onClick={() => setIsDarkMode(!isDarkMode)} className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800">
          {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </header>

      <main className="flex-1 p-8 max-w-6xl mx-auto w-full">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-bold">My Notebooks</h2>
          <button
            onClick={createNotebook}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            <Plus className="w-5 h-5" />
            New Notebook
          </button>
        </div>

        {notebooks.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <Book className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg">No notebooks yet. Create your first workspace!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {notebooks.map(nb => (
              <div
                key={nb.id}
                onClick={() => navigate(`/notebook/${nb.id}`)}
                className="bg-white dark:bg-[#1E1F20] border border-gray-200 dark:border-[#2D2E30] rounded-xl p-6 cursor-pointer hover:border-blue-500 transition group flex flex-col h-48"
              >
                <div className="flex justify-between items-start mb-4">
                  <Book className="w-8 h-8 text-blue-500" />
                  <button
                    onClick={(e) => deleteNotebook(nb.id, e)}
                    className="text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
                <h3 className="font-semibold text-lg line-clamp-2">{nb.title}</h3>
                <p className="text-sm text-gray-500 mt-auto">
                  {new Date(nb.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
