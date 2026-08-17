import React, { useState } from 'react'
import { DayPicker } from 'react-day-picker'
import 'react-day-picker/dist/style.css'
import { useAppStore } from '@/store/useAppStore'
import { format } from 'date-fns'
import { uz } from 'date-fns/locale'

const upcomingEvents = [
  { id: 1, date: new Date(), title: 'Umumiy tozalash: A-blok', time: '10:00' },
  { id: 2, date: new Date(new Date().setDate(new Date().getDate() + 1)), title: 'Yangi ishchilar bilan uchrashuv', time: '14:30' },
  { id: 3, date: new Date(new Date().setDate(new Date().getDate() + 2)), title: 'Vip mijoz xizmati: Chilonzor', time: '09:00' },
]

export const Calendar = () => {
  const [selected, setSelected] = useState<Date | undefined>(new Date())
  const theme = useAppStore((state) => state.theme)
  const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

  // Filter events for selected day
  const dayEvents = selected 
    ? upcomingEvents.filter(e => e.date.toDateString() === selected.toDateString())
    : []

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold tracking-tight mb-6">Taqvim va Rejalar</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Calendar Widget */}
        <div className="col-span-1 glass p-6 rounded-xl flex justify-center items-start">
          <style>
            {`
              .rdp {
                --rdp-cell-size: 40px;
                --rdp-accent-color: #3b82f6; /* primary blue */
                --rdp-background-color: ${isDark ? '#1e40af' : '#dbeafe'};
                margin: 0;
              }
              .dark .rdp-day_selected, .dark .rdp-day_selected:focus-visible, .dark .rdp-day_selected:hover {
                background-color: var(--rdp-accent-color);
                color: white;
              }
            `}
          </style>
          <DayPicker
            mode="single"
            selected={selected}
            onSelect={setSelected}
            locale={uz}
            className={isDark ? 'dark' : ''}
            modifiers={{
              hasEvent: upcomingEvents.map(e => e.date)
            }}
            modifiersStyles={{
              hasEvent: { fontWeight: 'bold', borderBottom: '2px solid #3b82f6' }
            }}
          />
        </div>

        {/* Events List */}
        <div className="col-span-1 md:col-span-2 glass p-6 rounded-xl">
          <h2 className="text-xl font-semibold mb-4 border-b border-border pb-2">
            {selected ? format(selected, 'd MMMM, yyyy', { locale: uz }) : 'Kun tanlanmagan'} - Rejalar
          </h2>
          
          {dayEvents.length > 0 ? (
            <ul className="space-y-4">
              {dayEvents.map((event) => (
                <li key={event.id} className="flex items-start p-4 bg-white/5 dark:bg-black/10 rounded-lg border border-white/10 shadow-sm transition-all hover:bg-white/10">
                  <div className="bg-primary/20 text-primary p-2 rounded-md font-bold w-16 text-center shrink-0">
                    {event.time}
                  </div>
                  <div className="ml-4">
                    <h3 className="font-semibold text-lg">{event.title}</h3>
                    <p className="text-sm text-muted-foreground">Belgilangan vazifa</p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-10 text-muted-foreground">
              <p>Bu kun uchun rejalar yo'q.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
