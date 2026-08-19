/**
 * GeoPulse — Geofence Management Screen
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  Alert,
  ActivityIndicator,
  RefreshControl,
  Modal,
} from 'react-native';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme';
import { geofenceApi } from '../../api/endpoints';
import { useLocation } from '../../store/LocationContext';

const GeofenceScreen = () => {
  const { myLocation } = useLocation();
  const [geofences, setGeofences] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);

  // Form states
  const [zoneName, setZoneName] = useState('');
  const [radius, setRadius] = useState('200');

  useEffect(() => {
    loadGeofences();
  }, []);

  const loadGeofences = async () => {
    setIsLoading(true);
    try {
      const { data } = await geofenceApi.getGeofences();
      setGeofences(data || []);
    } catch (e) {
      console.warn('Failed to load geofences:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadGeofences();
    setIsRefreshing(false);
  }, []);

  const handleCreate = async () => {
    if (!zoneName.trim()) {
      Alert.alert('Name Required', 'Please enter a name for the zone');
      return;
    }

    if (!myLocation) {
      Alert.alert('Location Required', 'Current location is needed to create a geofence zone');
      return;
    }

    try {
      await geofenceApi.createGeofence({
        name: zoneName.trim(),
        latitude: myLocation.latitude,
        longitude: myLocation.longitude,
        radius_meters: parseInt(radius, 10) || 200,
      });
      setModalVisible(false);
      setZoneName('');
      setRadius('200');
      Alert.alert('Zone Created', `Geofence "${zoneName}" has been activated.`);
      loadGeofences();
    } catch (e) {
      Alert.alert('Error', 'Failed to create geofence');
    }
  };

  const handleDelete = (id, name) => {
    Alert.alert('Delete Zone', `Delete geofence "${name}"?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await geofenceApi.deleteGeofence(id);
            loadGeofences();
          } catch (e) {
            Alert.alert('Error', 'Failed to delete geofence');
          }
        },
      },
    ]);
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardLeft}>
        <View style={styles.iconCircle}>
          <Text style={styles.icon}>📍</Text>
        </View>
        <View>
          <Text style={styles.cardTitle}>{item.name}</Text>
          <Text style={styles.cardSubtitle}>
            Radius: {item.radius_meters}m • {item.is_active ? 'Active' : 'Inactive'}
          </Text>
        </View>
      </View>
      <TouchableOpacity
        style={styles.deleteButton}
        onPress={() => handleDelete(item.id, item.name)}>
        <Text style={styles.deleteText}>🗑️</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={geofences}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          !isLoading && (
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>🌐</Text>
              <Text style={styles.emptyTitle}>No Geofence Zones</Text>
              <Text style={styles.emptyDesc}>
                Add safe zones like Home, Office, or School to receive automatic arrival and departure alerts.
              </Text>
            </View>
          )
        }
      />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => setModalVisible(true)}>
        <Text style={styles.fabIcon}>＋</Text>
        <Text style={styles.fabText}>Add Zone</Text>
      </TouchableOpacity>

      {/* Create Modal */}
      <Modal
        visible={modalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Create Safe Zone</Text>
            <Text style={styles.modalDesc}>
              Creates a circular geofence around your current location.
            </Text>

            <TextInput
              style={styles.input}
              placeholder="Zone name (e.g. Home, Office)"
              placeholderTextColor={colors.text.tertiary}
              value={zoneName}
              onChangeText={setZoneName}
              autoFocus
            />

            <TextInput
              style={styles.input}
              placeholder="Radius in meters (e.g. 200)"
              placeholderTextColor={colors.text.tertiary}
              value={radius}
              onChangeText={setRadius}
              keyboardType="number-pad"
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.cancelBtn}
                onPress={() => setModalVisible(false)}>
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.createBtn}
                onPress={handleCreate}>
                <Text style={styles.createBtnText}>Create</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg.primary,
  },
  list: {
    padding: spacing.md,
    flexGrow: 1,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    ...shadows.sm,
  },
  cardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  iconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.brand.accent + '22',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  icon: {
    fontSize: 18,
  },
  cardTitle: {
    ...typography.bodyBold,
    color: colors.text.primary,
  },
  cardSubtitle: {
    ...typography.small,
    color: colors.text.tertiary,
    marginTop: 2,
  },
  deleteButton: {
    padding: spacing.sm,
  },
  deleteText: {
    fontSize: 18,
  },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 100,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  emptyTitle: {
    ...typography.h3,
    color: colors.text.secondary,
    marginBottom: spacing.xs,
  },
  emptyDesc: {
    ...typography.caption,
    color: colors.text.tertiary,
    textAlign: 'center',
    maxWidth: 280,
  },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.brand.primary,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.full,
    ...shadows.glow(colors.brand.primary),
  },
  fabIcon: {
    color: colors.text.primary,
    fontSize: 18,
    fontWeight: 'bold',
    marginRight: spacing.xs,
  },
  fabText: {
    ...typography.bodyBold,
    color: colors.text.primary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  modalContent: {
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    ...shadows.md,
  },
  modalTitle: {
    ...typography.h3,
    color: colors.text.primary,
    marginBottom: spacing.xs,
  },
  modalDesc: {
    ...typography.caption,
    color: colors.text.secondary,
    marginBottom: spacing.lg,
  },
  input: {
    backgroundColor: colors.bg.secondary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    color: colors.text.primary,
    fontSize: 16,
    borderWidth: 1,
    borderColor: colors.bg.tertiary,
    marginBottom: spacing.md,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  cancelBtn: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  cancelBtnText: {
    color: colors.text.secondary,
    fontWeight: '600',
  },
  createBtn: {
    backgroundColor: colors.brand.primary,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.md,
  },
  createBtnText: {
    color: colors.text.primary,
    fontWeight: '700',
  },
});

export default GeofenceScreen;
