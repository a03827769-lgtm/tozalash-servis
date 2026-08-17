import React, { useState } from 'react';
import { View, StyleSheet, SafeAreaView, StatusBar } from 'react-native';
import { DashboardScreen } from './src/screens/DashboardScreen';
import { MapScreen } from './src/screens/MapScreen';
import { ScannerScreen } from './src/screens/ScannerScreen';
import { PhotoAuditScreen } from './src/screens/PhotoAuditScreen';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState('Dashboard');

  const navigation = {
    navigate: (screen: string) => setCurrentScreen(screen),
    goBack: () => setCurrentScreen('Dashboard')
  };

  const renderScreen = () => {
    switch (currentScreen) {
      case 'Map':
        return <MapScreen navigation={navigation} />;
      case 'Scanner':
        return <ScannerScreen navigation={navigation} />;
      case 'PhotoAudit':
        return <PhotoAuditScreen navigation={navigation} />;
      case 'Dashboard':
      default:
        return <DashboardScreen navigation={navigation} />;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      {renderScreen()}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6'
  },
});
