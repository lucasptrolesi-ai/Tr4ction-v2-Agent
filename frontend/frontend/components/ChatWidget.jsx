"use client";

import { useState } from "react";
import axios from "axios";
import { MessageCircle, X } from "lucide-react";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  async function sendMessage() {
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await axios.post(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/chat`,
        { question: input }
      );

      const botMsg = { sender: "bot", text: res.data.answer };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Erro ao conectar ao agente." }
      ]);
    }

    setInput("");
  }

  return (
    <>
      {/* BOTÃO FLUTUANTE */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-xl transition-all z-50"
        >
          <MessageCircle size={28} />
        </button>
      )}

      {/* JANELA DO CHAT */}
      {open && (
        <div className="fixed bottom-6 right-6 w-96 h-[450px] bg-white shadow-xl rounded-lg flex flex-col border z-50">

          {/* HEADER */}
          <div className="bg-blue-600 text-white px-4 py-3 flex justify-between items-center rounded-t-lg">
            <h2 className="font-semibold">TR4CTION Agent</h2>
            <button onClick={() => setOpen(false)}>
              <X size={22} />
            </button>
          </div>

          {/* MENSAGENS */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`p-2 rounded-md max-w-[80%] ${
                  m.sender === "user"
                    ? "bg-blue-100 self-end ml-auto"
                    : "bg-gray-200"
                }`}
              >
                {m.text}
              </div>
            ))}
          </div>

          {/* INPUT */}
          <div className="border-t p-3 flex items-center gap-2">
            <input
              className="flex-1 border rounded px-3 py-2"
              placeholder="Escreva uma mensagem…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button
              onClick={sendMessage}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
            >
              Enviar
            </button>
          </div>

        </div>
      )}
    </>
  );
}
