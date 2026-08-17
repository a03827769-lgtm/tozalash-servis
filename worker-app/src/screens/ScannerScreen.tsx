import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

export const ScannerScreen = ({ navigation }: any) => {
  return (
    <View style={styles.container}>
      <View style={styles.scannerArea}>
        <View style={styles.scanBox} />
        <Text style={styles.scanText}>QR kod yoki Barkodni kamera orqali skanerlang</Text>
      </View>
      
      <View style={styles.bottomPanel}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>Orqaga</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  scannerArea: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scanBox: { width: 250, height: 250, borderWidth: 2, borderColor: '#10b981', borderRadius: 10, backgroundColor: 'rgba(255,255,255,0.1)' },
  scanText: { color: 'white', marginTop: 20, fontSize: 16, textAlign: 'center', paddingHorizontal: 40 },
  bottomPanel: { padding: 20, backgroundColor: '#1f2937', borderTopLeftRadius: 20, borderTopRightRadius: 20 },
  backButton: { padding: 15, borderRadius: 10, alignItems: 'center', backgroundColor: '#374151' },
  backText: { color: 'white', fontWeight: 'bold', fontSize: 16 }
});
