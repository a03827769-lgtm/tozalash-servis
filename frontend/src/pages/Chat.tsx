import React, { useState } from 'react'
import { Send, UserCircle2 } from 'lucide-react'

const initialMessages = [
  { id: 1, text: 'Assalomu alaykum! Buyurtma qachon yetib keladi?', sender: 'client', time: '10:00' },
  { id: 2, text: 'Va alaykum assalom! Xodimimiz 15 daqiqada boradi.', sender: 'admin', time: '10:02' },
]

export const Chat = () => {
  const [messages, setMessages] = useState(initialMessages)
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return
    const newMsg = {
      id: Date.now(),
      text: input,
      sender: 'admin',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    setMessages([...messages, newMsg])
    setInput('')
  }

  return (
    <div className="p-6 h-full flex flex-col max-h-screen">
      <h1 className="text-3xl font-bold tracking-tight mb-6">Jonli Chat</h1>
      
      <div className="flex-1 glass rounded-xl flex flex-col overflow-hidden">
        
        {/* Chat Header */}
        <div className="border-b border-border p-4 flex items-center space-x-3 bg-white/5 dark:bg-black/10">
          <UserCircle2 className="w-10 h-10 text-primary" />
          <div>
            <h3 className="font-semibold text-lg">Mijoz: Alisher Rustamov</h3>
            <p className="text-sm text-green-500 flex items-center">
              <span className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
              Onlayn
            </p>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.sender === 'admin' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[70%] rounded-2xl px-4 py-2 shadow-sm ${
                msg.sender === 'admin' 
                  ? 'bg-primary text-primary-foreground rounded-br-none' 
                  : 'bg-secondary text-secondary-foreground rounded-bl-none'
              }`}>
                <p>{msg.text}</p>
                <p className={`text-xs mt-1 text-right ${msg.sender === 'admin' ? 'text-blue-100' : 'text-gray-400'}`}>
                  {msg.time}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-border bg-white/5 dark:bg-black/10">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Xabar yozing..."
              className="flex-1 bg-background border border-input rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button 
              onClick={handleSend}
              className="bg-primary hover:bg-primary/90 text-primary-foreground rounded-full p-2.5 transition-colors shadow-md"
            >
              <Send className="w-5 h-5 ml-1" />
            </button>
          </div>
        </div>

      </div>
    </div>
  )
}
