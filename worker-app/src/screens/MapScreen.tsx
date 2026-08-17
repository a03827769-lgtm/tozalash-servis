import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

// In a real app we'd import MapView from 'react-native-maps'
// and *Location from 'expo-location'

export const MapScreen = ({ navigation }: any) => {
  const [isTracking, setIsTracking] = useState(false);

  useEffect(() => {
    // Start background location service when component mounts if isTracking is true
  }, [isTracking]);

  return (
    <View style={styles.container}>
      <View style={styles.mockMap}>
        <Text style={styles.mapText}>Google Maps / Yandex Nav Integratsiyasi</Text>
        <Text style={styles.mapSubText}>GPS kordinatalar: 41.311081, 69.240562</Text>
        
        {isTracking && (
          <View style={styles.trackingIndicator}>
            <View style={styles.trackingDot} />
            <Text style={styles.trackingText}>Fon rejimida kuzatilmoqda...</Text>
          </View>
        )}
      </View>

      <View style={styles.bottomPanel}>
        <TouchableOpacity 
          style={[styles.trackButton, isTracking ? styles.stopButton : styles.startButton]}
          onPress={() => setIsTracking(!isTracking)}
        >
          <Text style={styles.buttonText}>{isTracking ? 'Kuzatuvni To\'xtatish' : 'Kuzatuvni Boshlash'}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>Orqaga</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f3f4f6' },
  mockMap: { flex: 1, backgroundColor: '#d1d5db', justifyContent: 'center', alignItems: 'center' },
  mapText: { fontSize: 20, fontWeight: 'bold', color: '#374151', textAlign: 'center' },
  mapSubText: { fontSize: 14, color: '#4b5563', marginTop: 10 },
  trackingIndicator: { flexDirection: 'row', alignItems: 'center', marginTop: 20, backgroundColor: 'rgba(255,255,255,0.8)', padding: 10, borderRadius: 20 },
  trackingDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#10b981', marginRight: 10 },
  trackingText: { color: '#047857', fontWeight: '600' },
  bottomPanel: { padding: 20, backgroundColor: 'white', borderTopLeftRadius: 20, borderTopRightRadius: 20 },
  trackButton: { padding: 15, borderRadius: 10, alignItems: 'center', marginBottom: 10 },
  startButton: { backgroundColor: '#3b82f6' },
  stopButton: { backgroundColor: '#ef4444' },
  buttonText: { color: 'white', fontWeight: 'bold', fontSize: 16 },
  backButton: { padding: 15, borderRadius: 10, alignItems: 'center', backgroundColor: '#e5e7eb' },
  backText: { color: '#374151', fontWeight: 'bold', fontSize: 16 }
});
