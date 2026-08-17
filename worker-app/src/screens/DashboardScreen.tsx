import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { SOSButton } from '../components/SOSButton';

export const DashboardScreen = ({ navigation }: any) => {
  const [stats] = useState({ rating: 4.9, earnings: '4 200 000 UZS', tasksToday: 3 });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Xush kelibsiz, Alisher</Text>
        <Text style={styles.subtitle}>Bugungi buyurtmalar: {stats.tasksToday} ta</Text>
      </View>

      <View style={styles.statsCard}>
        <View style={styles.statBox}>
          <Text style={styles.statLabel}>Reyting</Text>
          <Text style={styles.statValue}>⭐ {stats.rating}</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statLabel}>Daromad</Text>
          <Text style={styles.statValue}>{stats.earnings}</Text>
        </View>
      </View>

      <View style={styles.grid}>
        <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('Map')}>
          <Text style={styles.buttonText}>🗺️ Jonli Xarita / Navigatsiya</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('PhotoAudit')}>
          <Text style={[styles.buttonText, { color: '#2563eb' }]}>📸 Sifat Nazorati (Oldin/Keyin Foto)</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('Scanner')}>
          <Text style={styles.buttonText}>📱 QR Kod Skaner</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.sosContainer}>
        <SOSButton />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f3f4f6', padding: 20 },
  header: { marginBottom: 20, marginTop: 40 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#1f2937' },
  subtitle: { fontSize: 16, color: '#4b5563', marginTop: 5 },
  statsCard: { flexDirection: 'row', backgroundColor: 'white', borderRadius: 15, padding: 20, marginBottom: 30, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 10, elevation: 5 },
  statBox: { flex: 1, alignItems: 'center' },
  statLabel: { fontSize: 14, color: '#6b7280' },
  statValue: { fontSize: 18, fontWeight: 'bold', color: '#3b82f6', marginTop: 5 },
  grid: { gap: 15 },
  button: { backgroundColor: 'white', padding: 20, borderRadius: 12, alignItems: 'center', shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 5, elevation: 2 },
  buttonText: { fontSize: 16, fontWeight: '600', color: '#374151' },
  sosContainer: { marginTop: 'auto', alignItems: 'center', paddingBottom: 20 }
});
