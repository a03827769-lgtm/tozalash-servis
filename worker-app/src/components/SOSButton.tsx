import React from 'react';
import { TouchableOpacity, Text, StyleSheet, Alert, Vibration } from 'react-native';

export const SOSButton = () => {
  const handleSOS = () => {
    Vibration.vibrate([100, 500, 100, 500, 100, 500]);
    Alert.alert(
      'FAVQULODDA HOLAT (SOS)',
      'Barcha rahbarlarga va markazga lokatsiyangiz bilan xabar yuborilmoqda. Tasdiqlaysizmi?',
      [
        { text: 'Bekor qilish', style: 'cancel' },
        { 
          text: 'TASDIQLASH', 
          style: 'destructive',
          onPress: () => {
            // Here: Trigger WebSocket SOS event to backend with current GPS
            Alert.alert('Yuborildi', 'Yordam tez orada yetib keladi.');
          } 
        }
      ]
    );
  };

  return (
    <TouchableOpacity style={styles.sosButton} onLongPress={handleSOS} delayLongPress={1000}>
      <Text style={styles.sosText}>SOS (Ushlab turing)</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  sosButton: {
    backgroundColor: '#ef4444',
    paddingVertical: 15,
    paddingHorizontal: 40,
    borderRadius: 30,
    shadowColor: '#dc2626',
    shadowOpacity: 0.5,
    shadowRadius: 10,
    elevation: 5,
  },
  sosText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
    letterSpacing: 1,
  }
});
