import React from 'react'
import { YMaps, Map as YandexMap, Placemark, ZoomControl } from '@pbe/react-yandex-maps'
import { useAppStore } from '@/store/useAppStore'

const orders = [
  { id: 1, coordinates: [41.311081, 69.240562], title: 'Buyurtma #1021', status: 'pending' },
  { id: 2, coordinates: [41.299496, 69.240073], title: 'Buyurtma #1022', status: 'in-progress' },
  { id: 3, coordinates: [41.328325, 69.261271], title: 'Buyurtma #1023', status: 'completed' }
]

export const Map = () => {
  const theme = useAppStore((state) => state.theme)
  const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

  return (
    <div className="p-6 space-y-6 h-full flex flex-col">
      <h1 className="text-3xl font-bold tracking-tight">Xarita & Jonli Kuzatuv</h1>
      
      <div className="flex-1 glass rounded-xl overflow-hidden min-h-[500px] relative border-4 border-transparent">
        {/* Yandex Map wrapper */}
        <YMaps query={{ lang: 'uz_UZ' }}>
          <YandexMap
            defaultState={{ center: [41.311081, 69.240562], zoom: 12 }}
            width="100%"
            height="100%"
          >
            <ZoomControl options={{ float: 'right' }} />
            {orders.map((order) => {
              const iconColor = order.status === 'completed' ? '#10b981' : order.status === 'in-progress' ? '#f59e0b' : '#ef4444'
              return (
                <Placemark
                  key={order.id}
                  geometry={order.coordinates}
                  properties={{
                    hintContent: order.title,
                    balloonContent: `<b>${order.title}</b><br/>Holati: ${order.status}`
                  }}
                  options={{
                    preset: 'islands#circleIcon',
                    iconColor: iconColor
                  }}
                />
              )
            })}
          </YandexMap>
        </YMaps>

        {isDark && (
          <div className="absolute inset-0 pointer-events-none mix-blend-color z-10 bg-slate-900/50" />
        )}
      </div>
    </div>
  )
}
