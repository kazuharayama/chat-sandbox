import { useState, useEffect, useRef } from 'react';
import { apiService } from '../services/api';
import type { Task } from '../services/api';
import { Plus, X, GripVertical, Trash2, Edit3, Check } from 'lucide-react';

type Status = 'todo' | 'in_progress' | 'done';

const COLUMNS: { status: Status; label: string; color: string; bgColor: string }[] = [
  { status: 'todo', label: 'TODO', color: 'text-blue-600', bgColor: 'bg-blue-50' },
  { status: 'in_progress', label: '進行中', color: 'text-yellow-600', bgColor: 'bg-yellow-50' },
  { status: 'done', label: '完了', color: 'text-green-600', bgColor: 'bg-green-50' },
];

export default function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTaskTitle, setNewTaskTitle] = useState<Record<Status, string>>({ todo: '', in_progress: '', done: '' });
  const [addingTo, setAddingTo] = useState<Status | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [draggedTask, setDraggedTask] = useState<Task | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<Status | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadTasks(); }, []);
  useEffect(() => { if (addingTo && inputRef.current) inputRef.current.focus(); }, [addingTo]);

  const loadTasks = async () => {
    const list = await apiService.listTasks();
    setTasks(list);
  };

  const getTasksByStatus = (status: Status) =>
    tasks.filter(t => t.status === status).sort((a, b) => a.sort_order - b.sort_order);

  const addTask = async (status: Status) => {
    const title = newTaskTitle[status].trim();
    if (!title) return;
    await apiService.createTask({ title, status });
    setNewTaskTitle({ ...newTaskTitle, [status]: '' });
    setAddingTo(null);
    await loadTasks();
  };

  const startEdit = (task: Task) => {
    setEditingId(task.id);
    setEditTitle(task.title);
  };

  const saveEdit = async (taskId: string) => {
    if (!editTitle.trim()) return;
    await apiService.updateTask(taskId, { title: editTitle.trim() });
    setEditingId(null);
    await loadTasks();
  };

  const deleteTask = async (taskId: string) => {
    await apiService.deleteTask(taskId);
    await loadTasks();
  };

  const moveTask = async (taskId: string, newStatus: Status) => {
    await apiService.updateTask(taskId, { status: newStatus });
    await loadTasks();
  };

  // Drag and drop
  const handleDragStart = (e: React.DragEvent, task: Task) => {
    setDraggedTask(task);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, status: Status) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverColumn(status);
  };

  const handleDragLeave = () => {
    setDragOverColumn(null);
  };

  const handleDrop = async (e: React.DragEvent, status: Status) => {
    e.preventDefault();
    setDragOverColumn(null);
    if (draggedTask && draggedTask.status !== status) {
      await moveTask(draggedTask.id, status);
    }
    setDraggedTask(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent, status: Status) => {
    if (e.key === 'Enter') addTask(status);
    if (e.key === 'Escape') setAddingTo(null);
  };

  return (
    <div className="flex-1 overflow-hidden flex flex-col bg-gray-50">
      <div className="px-6 py-4 border-b border-gray-200 bg-white">
        <h1 className="text-lg font-semibold text-gray-900">タスク管理</h1>
        <p className="text-sm text-gray-500">ドラッグ&ドロップでステータスを変更</p>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="flex gap-4 min-h-full">
          {COLUMNS.map(col => {
            const columnTasks = getTasksByStatus(col.status);
            const isOver = dragOverColumn === col.status;

            return (
              <div
                key={col.status}
                className={`flex-1 min-w-[280px] max-w-[400px] flex flex-col rounded-xl transition-colors ${
                  isOver ? 'bg-blue-50 ring-2 ring-blue-300' : 'bg-gray-100'
                }`}
                onDragOver={e => handleDragOver(e, col.status)}
                onDragLeave={handleDragLeave}
                onDrop={e => handleDrop(e, col.status)}
              >
                {/* Column header */}
                <div className="px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-semibold ${col.color}`}>{col.label}</span>
                    <span className="text-xs text-gray-400 bg-white rounded-full px-2 py-0.5">
                      {columnTasks.length}
                    </span>
                  </div>
                  <button
                    onClick={() => setAddingTo(col.status)}
                    className="p-1 text-gray-400 hover:text-gray-600 hover:bg-white rounded-lg transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>

                {/* Tasks */}
                <div className="flex-1 px-3 pb-3 space-y-2 overflow-y-auto">
                  {/* Add task input */}
                  {addingTo === col.status && (
                    <div className="bg-white border-2 border-blue-300 rounded-lg p-3 shadow-sm">
                      <input
                        ref={inputRef}
                        type="text"
                        value={newTaskTitle[col.status]}
                        onChange={e => setNewTaskTitle({ ...newTaskTitle, [col.status]: e.target.value })}
                        onKeyDown={e => handleKeyDown(e, col.status)}
                        className="w-full text-sm text-gray-800 focus:outline-none"
                        placeholder="タスク名を入力..."
                      />
                      <div className="flex items-center gap-2 mt-2">
                        <button
                          onClick={() => addTask(col.status)}
                          className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                        >
                          追加
                        </button>
                        <button
                          onClick={() => setAddingTo(null)}
                          className="p-1 text-gray-400 hover:text-gray-600"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Task cards */}
                  {columnTasks.map(task => (
                    <div
                      key={task.id}
                      draggable
                      onDragStart={e => handleDragStart(e, task)}
                      className={`group bg-white border border-gray-200 rounded-lg p-3 cursor-grab active:cursor-grabbing shadow-sm hover:shadow transition-shadow ${
                        draggedTask?.id === task.id ? 'opacity-50' : ''
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <GripVertical className="w-4 h-4 text-gray-300 mt-0.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="flex-1 min-w-0">
                          {editingId === task.id ? (
                            <div className="flex items-center gap-1">
                              <input
                                type="text"
                                value={editTitle}
                                onChange={e => setEditTitle(e.target.value)}
                                onKeyDown={e => { if (e.key === 'Enter') saveEdit(task.id); if (e.key === 'Escape') setEditingId(null); }}
                                className="flex-1 text-sm text-gray-800 border-b border-blue-300 focus:outline-none"
                                autoFocus
                              />
                              <button onClick={() => saveEdit(task.id)} className="p-0.5 text-green-500 hover:text-green-700">
                                <Check className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          ) : (
                            <p className="text-sm text-gray-800">{task.title}</p>
                          )}
                          {task.description && (
                            <p className="text-xs text-gray-400 mt-1 line-clamp-2">{task.description}</p>
                          )}
                        </div>
                        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => startEdit(task)} className="p-1 text-gray-400 hover:text-gray-600 rounded">
                            <Edit3 className="w-3 h-3" />
                          </button>
                          <button onClick={() => deleteTask(task.id)} className="p-1 text-gray-400 hover:text-red-500 rounded">
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
