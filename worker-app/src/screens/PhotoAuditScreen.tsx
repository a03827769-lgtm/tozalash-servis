import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert, Image, ScrollView } from 'react-native';

export const PhotoAuditScreen = ({ navigation }: any) => {
  const [photosBefore, setPhotosBefore] = useState<string[]>([]);
  const [photosAfter, setPhotosAfter] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const takePhoto = (type: 'before' | 'after') => {
    // Mock camera capture
    const mockUri = `https://picsum.photos/400/300?random=${Date.now()}`;
    if (type === 'before') {
      setPhotosBefore([...photosBefore, mockUri]);
    } else {
      setPhotosAfter([...photosAfter, mockUri]);
    }
    Alert.alert('Rasm saqlandi', `${type === 'before' ? 'Ishdan oldingi' : 'Ishdan keyingi'} rasm muvaffaqiyatli yuklandi.`);
  };

  const submitQualityReport = () => {
    if (photosBefore.length === 0 || photosAfter.length === 0) {
      Alert.alert('Ogohlantirish', 'Tozalashni yakunlash uchun kamida 1 ta ISHDAN OLDIN va 1 ta ISHDAN KEYIN rasm yuklash shart!');
      return;
    }

    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      Alert.alert('✅ Qabul qilindi', 'Sifat nazorati fotohisoboti tasdiqlandi. Buyurtma muvaffaqiyatli yakunlandi!', [
        { text: 'OK', onPress: () => navigation.navigate('Dashboard') }
      ]);
    }, 1500);
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>📸 Sifat Nazorati (Photo Audit)</Text>
        <Text style={styles.subtitle}>Tozalashdan oldingi va keyingi holatni tasdiqlang</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>1. Ishni boshlashdan OLDIN ({photosBefore.length} ta)</Text>
        <TouchableOpacity style={styles.captureBtn} onPress={() => takePhoto('before')}>
          <Text style={styles.captureBtnText}>📷 Oldingi rasmni olish</Text>
        </TouchableOpacity>
        <ScrollView horizontal style={styles.imageRow}>
          {photosBefore.map((uri, idx) => (
            <Image key={idx} source={{ uri }} style={styles.thumbnail} />
          ))}
        </ScrollView>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>2. Ishni yakunlagandan KEYIN ({photosAfter.length} ta)</Text>
        <TouchableOpacity style={[styles.captureBtn, { backgroundColor: '#10b981' }]} onPress={() => takePhoto('after')}>
          <Text style={styles.captureBtnText}>✨ Yakuniy toza holatni olish</Text>
        </TouchableOpacity>
        <ScrollView horizontal style={styles.imageRow}>
          {photosAfter.map((uri, idx) => (
            <Image key={idx} source={{ uri }} style={styles.thumbnail} />
          ))}
        </ScrollView>
      </View>

      <TouchableOpacity
        style={[styles.submitBtn, isSubmitting && { opacity: 0.6 }]}
        onPress={submitQualityReport}
        disabled={isSubmitting}
      >
        <Text style={styles.submitBtnText}>
          {isSubmitting ? 'AI Sifat Tahlili Qilinmoqda...' : '✅ Ishni Yakunlash va Hisobotni Yuborish'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb', padding: 20 },
  header: { marginTop: 40, marginBottom: 20 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#111827' },
  subtitle: { fontSize: 14, color: '#6b7280', marginTop: 4 },
  section: { backgroundColor: '#fff', padding: 15, borderRadius: 12, marginBottom: 20, elevation: 2 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#374151', marginBottom: 10 },
  captureBtn: { backgroundColor: '#3b82f6', padding: 12, borderRadius: 8, alignItems: 'center', marginBottom: 10 },
  captureBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  imageRow: { flexDirection: 'row', marginTop: 5 },
  thumbnail: { width: 90, height: 90, borderRadius: 8, marginRight: 10 },
  submitBtn: { backgroundColor: '#1e40af', padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 10, marginBottom: 40 },
  submitBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 }
});
