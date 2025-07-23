/*
 * ChatRichTextarea.tsx
 * Rich chat input with a left‑hand image‑attach button and right‑hand arrow‑send button.
 */
import React, {
  useState,
  useRef,
  useEffect,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import { Paperclip, ArrowRight } from "lucide-react";

interface ChatRichTextareaProps {
  /** Initial value */
  value?: string;
  /** Minimum rows to display (default: 1) */
  minRows?: number;
  /** Maximum rows before scrolling (default: 8) */
  maxRows?: number;
  /** Placeholder text */
  placeholder?: string;
  /** Disable input */
  disabled?: boolean;
  /** Callback when the user submits (Enter) or clicks the arrow button */
  onSend?: (text: string) => void;
  /** Callback when the attach button is clicked */
  onAttach?: () => void;
  /** Allow arbitrary React nodes above / below the textarea */
  headerSlot?: ReactNode;
  footerSlot?: ReactNode;
}

const ChatRichTextarea: React.FC<ChatRichTextareaProps> = ({
  value = "",
  minRows = 1,
  maxRows = 8,
  placeholder = "Write a message…",
  disabled = false,
  onSend,
  onAttach,
  headerSlot,
  footerSlot,
}) => {
  const [text, setText] = useState(value);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // ----- Auto‑resize -------------------------------------------------------
  const resize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const lineHeight = parseFloat(getComputedStyle(el).lineHeight) || 24;
    const nextHeight = Math.min(el.scrollHeight, lineHeight * maxRows);
    el.style.height = `${nextHeight}px`;
  };

  useEffect(() => {
    resize();
  }, [text, maxRows]);

  // ----- Handlers ----------------------------------------------------------
  const handleSubmit = () => {
    if (text.trim()) {
      onSend?.(text.trim());
      setText("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // ------------------------------------------------------------------------
  return (
    <div className="space-y-1">
      {headerSlot}
      <div className="relative flex w-full rounded-2xl border bg-white p-3 shadow-sm transition-shadow focus-within:shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
        {/* Attach (left) */}
        <button
          type="button"
          aria-label="Attach image"
          onClick={onAttach}
          disabled={disabled}
          className="absolute bottom-3 left-3 inline-flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-200 p-1 shadow-sm transition hover:bg-zinc-300 focus-visible:outline-none dark:bg-zinc-700 dark:hover:bg-zinc-600 disabled:pointer-events-none disabled:opacity-50"
        >
          <Paperclip className="h-4 w-4" />
        </button>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          className="peer w-full resize-none overflow-hidden bg-transparent px-12 text-base text-zinc-900 placeholder-zinc-400 focus:outline-none dark:text-zinc-100"
          rows={minRows}
          placeholder={placeholder}
          disabled={disabled}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
        />

        {/* Send (right) */}
        <button
          type="button"
          onClick={handleSubmit}
          aria-label="Send message"
          disabled={disabled || !text.trim()}
          className="absolute bottom-3 right-3 inline-flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 p-1 transition-opacity hover:bg-blue-700 focus-visible:outline-none peer-focus:opacity-100 dark:bg-blue-500 disabled:pointer-events-none disabled:opacity-50"
        >
          <ArrowRight className="h-4 w-4 stroke-[2.5] text-white" />
        </button>
      </div>
      {footerSlot}
    </div>
  );
};

export default ChatRichTextarea;
