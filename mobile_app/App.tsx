import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, SafeAreaView, ScrollView, Alert, ActivityIndicator } from 'react-native';

// MOCK API URL
const API_URL = 'http://192.168.1.100:8000'; // Change to local IP during testing

export default function App() {
  const [token, setToken] = useState<string | null>(null);
  
  if (!token) {
    return <LoginScreen onLogin={setToken} />;
  }
  
  return <DashboardScreen token={token} onLogout={() => setToken(null)} />;
}

function LoginScreen({ onLogin }: { onLogin: (token: string) => void }) {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    if (!phone || !password) {
      Alert.alert('Xatolik', "Telefon va parolni kiriting");
      return;
    }
    
    setIsLoading(true);
    try {
      // Mocked login logic since this is MVP
      // In production: fetch token from /bot/telegram/login (or create specific auth route)
      if (phone === '998901234567' && password === 'admin') {
        onLogin('mock_jwt_token_123');
      } else {
        Alert.alert('Xato', "Noto'g'ri login yoki parol");
      }
    } catch (error) {
      Alert.alert('Xatolik', "Tarmoq xatosi");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.loginContainer}>
        <Text style={styles.title}>Tozalash Servis</Text>
        <Text style={styles.subtitle}>Ishchilar uchun portal</Text>
        
        <TextInput 
          style={styles.input}
          placeholder="Telefon raqam (+998...)"
          value={phone}
          onChangeText={setPhone}
          keyboardType="phone-pad"
        />
        <TextInput 
          style={styles.input}
          placeholder="Parol"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        
        <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={isLoading}>
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Tizimga kirish</Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

function DashboardScreen({ token, onLogout }: { token: string, onLogout: () => void }) {
  // Mock data for MVP
  const [orders, setOrders] = useState([
    { id: 1, address: 'Toshkent, Yunusobod', service: 'Standart Tozalash', status: 'yangi', time: '14:00 - Bugun' },
    { id: 2, address: 'Toshkent, Chilonzor', service: 'Oyna yuvish', status: 'jarayonda', time: '16:00 - Bugun' }
  ]);

  const updateStatus = (id: number, newStatus: string) => {
    setOrders(orders.map(o => o.id === id ? { ...o, status: newStatus } : o));
    Alert.alert('Muvaffaqiyatli', "Holat o'zgartirildi: " + newStatus);
    // In production, send POST to API
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Mening Buyurtmalarim</Text>
        <TouchableOpacity onPress={onLogout}>
          <Text style={styles.logoutText}>Chiqish</Text>
        </TouchableOpacity>
      </View>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {orders.map(order => (
          <View key={order.id} style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.orderId}>#00{order.id}</Text>
              <View style={[styles.badge, order.status === 'yangi' ? styles.badgeNew : styles.badgeProgress]}>
                <Text style={styles.badgeText}>{order.status}</Text>
              </View>
            </View>
            
            <Text style={styles.serviceText}>{order.service}</Text>
            <Text style={styles.addressText}>{order.address}</Text>
            <Text style={styles.timeText}>{order.time}</Text>
            
            {order.status === 'yangi' && (
              <TouchableOpacity style={styles.actionBtn} onPress={() => updateStatus(order.id, 'jarayonda')}>
                <Text style={styles.actionBtnText}>Ishni boshlash</Text>
              </TouchableOpacity>
            )}
            
            {order.status === 'jarayonda' && (
              <TouchableOpacity style={[styles.actionBtn, {backgroundColor: '#10b981'}]} onPress={() => updateStatus(order.id, 'bajarildi')}>
                <Text style={styles.actionBtnText}>Yakunlash</Text>
              </TouchableOpacity>
            )}
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  loginContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#0f172a',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    marginBottom: 32,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  logoutText: {
    color: '#ef4444',
    fontWeight: '600',
  },
  scrollContent: {
    padding: 16,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  orderId: {
    fontWeight: 'bold',
    color: '#64748b',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeNew: {
    backgroundColor: '#eff6ff',
  },
  badgeProgress: {
    backgroundColor: '#fef3c7',
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#0f172a',
  },
  serviceText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0f172a',
    marginBottom: 8,
  },
  addressText: {
    fontSize: 14,
    color: '#475569',
    marginBottom: 4,
  },
  timeText: {
    fontSize: 14,
    color: '#3b82f6',
    marginBottom: 16,
    fontWeight: '600',
  },
  actionBtn: {
    backgroundColor: '#3b82f6',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionBtnText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});
