import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, PlaySquare, Video, Trash2, Calendar, Loader2 } from 'lucide-react';
import useClipStore from '../store/useClipStore';
import Logo from '../components/Logo';

export default function Projects() {
  const navigate = useNavigate();
  const { getRecentProjects, removeRecentProject } = useClipStore();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate network delay to give a SaaS feel
    setTimeout(() => {
      setProjects(getRecentProjects());
      setLoading(false);
    }, 400);
  }, []);

  const handleDelete = (e, id) => {
    e.preventDefault();
    e.stopPropagation();
    removeRecentProject(id);
    setProjects(getRecentProjects());
  };

  return (
    <div className="min-h-screen bg-base relative flex flex-col">
      {/* Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-4 md:px-6 py-5 flex justify-between items-center border-b border-border">
        <div className="flex items-center gap-3">
          <Logo size={32} showWordmark={true} />
        </div>
        <button
          onClick={() => navigate('/')}
          className="btn-secondary py-2 border-transparent hover:border-border"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">New Clip</span>
        </button>
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex-grow w-full max-w-5xl mx-auto px-4 md:px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-text-primary">Your Projects</h1>
            <p className="text-sm text-text-muted mt-1">Manage and view your previously processed videos.</p>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 text-accent-1 animate-spin" />
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-20 rounded-2xl border border-dashed border-border bg-card/30 backdrop-blur">
            <PlaySquare className="w-12 h-12 text-text-muted mx-auto mb-3 opacity-50" />
            <h3 className="text-lg font-medium text-text-primary">No projects yet</h3>
            <p className="text-sm text-text-muted mt-1 max-w-md mx-auto">
              You haven't generated any clips yet. Go back to the home page to start your first viral project.
            </p>
            <button onClick={() => navigate('/')} className="mt-6 btn-primary">
              Create New Project
            </button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project, i) => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: i * 0.05 }}
              >
                <Link
                  to={`/dashboard/${project.id}`}
                  className="group block h-full rounded-2xl border border-border bg-card/60 p-5 text-left transition-all hover:border-accent-1/40 hover:bg-card backdrop-blur"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-accent-1/15 text-accent-1">
                      {project.source === 'youtube' ? <Video className="w-5 h-5" /> : <PlaySquare className="w-5 h-5" />}
                    </div>
                    <button 
                      onClick={(e) => handleDelete(e, project.id)}
                      className="p-1.5 rounded-lg text-text-muted hover:text-danger hover:bg-danger/10 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <h3 className="text-base font-semibold text-text-primary line-clamp-2 mb-2" title={project.title}>
                    {project.title || "Untitled Project"}
                  </h3>
                  
                  <div className="flex items-center gap-4 mt-auto pt-4 border-t border-border/50">
                    <div className="flex items-center gap-1.5 text-xs text-text-muted">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(project.date).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs font-medium text-accent-1">
                      View Clips →
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
