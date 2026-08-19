/**
 * GeoPulse — Contacts Screen
 *
 * Manages sharing relationships — send requests, view active shares.
 */

import React, { useEffect, useState, useCallback } from 'react';
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
} from 'react-native';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme';
import { sharingApi, userApi } from '../../api/endpoints';

const ContactsScreen = ({ navigation }) => {
  const [shares, setShares] = useState({ incoming: [], outgoing: [] });
  const [pendingRequests, setPendingRequests] = useState([]);
  const [searchPhone, setSearchPhone] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('active'); // active | pending | search

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [sharesRes, pendingRes] = await Promise.all([
        sharingApi.getShares(),
        sharingApi.getPendingRequests(),
      ]);
      setShares(sharesRes.data);
      setPendingRequests(pendingRes.data);
    } catch (e) {
      console.warn('Failed to load shares:', e);
    }
  };

  const onRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadData();
    setIsRefreshing(false);
  }, []);

  const handleSearch = async () => {
    if (searchPhone.length < 10) return;
    setIsSearching(true);
    setSearchResult(null);
    try {
      const { data } = await userApi.searchByPhone(searchPhone);
      setSearchResult(data);
    } catch (e) {
      setSearchResult(null);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSendRequest = async (targetId) => {
    try {
      await sharingApi.sendRequest(searchPhone, {
        liveLocation: true,
        locationHistory: false,
      });
      Alert.alert('Request Sent', 'Location sharing request has been sent.');
      setSearchResult(null);
      setSearchPhone('');
      loadData();
    } catch (e) {
      const msg = e.response?.data?.error?.message || 'Failed to send request';
      Alert.alert('Error', msg);
    }
  };

  const handleRespond = async (shareId, action) => {
    try {
      await sharingApi.respondToRequest(shareId, action);
      Alert.alert(
        'Success',
        action === 'accept' ? 'Location sharing is now active!' : 'Request declined.'
      );
      loadData();
    } catch (e) {
      Alert.alert('Error', 'Failed to respond to request');
    }
  };

  const handleStopSharing = async (shareId) => {
    Alert.alert(
      'Stop Sharing',
      'Are you sure you want to stop sharing location?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Stop',
          style: 'destructive',
          onPress: async () => {
            try {
              await sharingApi.stopSharing(shareId);
              loadData();
            } catch (e) {
              Alert.alert('Error', 'Failed to stop sharing');
            }
          },
        },
      ]
    );
  };

  const renderActiveShare = ({ item }) => (
    <View style={styles.shareCard}>
      <View style={styles.shareInfo}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {(item.name || 'U')[0].toUpperCase()}
          </Text>
        </View>
        <View style={styles.shareDetails}>
          <Text style={styles.shareName}>{item.name || 'Unknown'}</Text>
          <Text style={styles.shareStatus}>
            {item.direction === 'outgoing' ? 'You → Them' : 'Them → You'}
          </Text>
        </View>
      </View>
      <TouchableOpacity
        style={styles.stopButton}
        onPress={() => handleStopSharing(item.id)}>
        <Text style={styles.stopText}>Stop</Text>
      </TouchableOpacity>
    </View>
  );

  const renderPendingRequest = ({ item }) => (
    <View style={styles.shareCard}>
      <View style={styles.shareInfo}>
        <View style={[styles.avatar, styles.pendingAvatar]}>
          <Text style={styles.avatarText}>?</Text>
        </View>
        <View style={styles.shareDetails}>
          <Text style={styles.shareName}>Location Request</Text>
          <Text style={styles.shareStatus}>
            Wants to share their location with you
          </Text>
        </View>
      </View>
      <View style={styles.pendingActions}>
        <TouchableOpacity
          style={styles.acceptButton}
          onPress={() => handleRespond(item.id, 'accept')}>
          <Text style={styles.acceptText}>Accept</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.declineButton}
          onPress={() => handleRespond(item.id, 'reject')}>
          <Text style={styles.declineText}>✕</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Tab Bar */}
      <View style={styles.tabBar}>
        {[
          { key: 'active', label: 'Active' },
          { key: 'pending', label: `Pending${pendingRequests.length ? ` (${pendingRequests.length})` : ''}` },
          { key: 'search', label: 'Add' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.tabActive]}
            onPress={() => setActiveTab(tab.key)}>
            <Text
              style={[
                styles.tabText,
                activeTab === tab.key && styles.tabTextActive,
              ]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Active Shares */}
      {activeTab === 'active' && (
        <FlatList
          data={[
            ...shares.outgoing.map((s) => ({ ...s, direction: 'outgoing' })),
            ...shares.incoming.map((s) => ({ ...s, direction: 'incoming' })),
          ].filter((s) => s.status === 'accepted')}
          keyExtractor={(item) => item.id || item._id}
          renderItem={renderActiveShare}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={isRefreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>👥</Text>
              <Text style={styles.emptyTitle}>No active shares</Text>
              <Text style={styles.emptyDescription}>
                Search for contacts by phone number to start sharing
              </Text>
            </View>
          }
        />
      )}

      {/* Pending Requests */}
      {activeTab === 'pending' && (
        <FlatList
          data={pendingRequests}
          keyExtractor={(item) => item.id || item._id}
          renderItem={renderPendingRequest}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={isRefreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>📭</Text>
              <Text style={styles.emptyTitle}>No pending requests</Text>
            </View>
          }
        />
      )}

      {/* Search / Add Contact */}
      {activeTab === 'search' && (
        <View style={styles.searchContainer}>
          <Text style={styles.searchTitle}>Find by phone number</Text>
          <View style={styles.searchRow}>
            <TextInput
              style={styles.searchInput}
              placeholder="+91 98765 43210"
              placeholderTextColor={colors.text.tertiary}
              value={searchPhone}
              onChangeText={setSearchPhone}
              keyboardType="phone-pad"
              maxLength={15}
            />
            <TouchableOpacity
              style={styles.searchButton}
              onPress={handleSearch}
              disabled={isSearching}>
              {isSearching ? (
                <ActivityIndicator color={colors.text.primary} size="small" />
              ) : (
                <Text style={styles.searchButtonText}>Search</Text>
              )}
            </TouchableOpacity>
          </View>

          {searchResult && (
            <View style={styles.resultCard}>
              <View style={styles.shareInfo}>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>
                    {searchResult.name?.[0]?.toUpperCase() || '?'}
                  </Text>
                </View>
                <View style={styles.shareDetails}>
                  <Text style={styles.shareName}>{searchResult.name}</Text>
                  <View style={styles.onlineRow}>
                    <View
                      style={[
                        styles.onlineDot,
                        {
                          backgroundColor: searchResult.is_online
                            ? colors.status.online
                            : colors.status.offline,
                        },
                      ]}
                    />
                    <Text style={styles.shareStatus}>
                      {searchResult.is_online ? 'Online' : 'Offline'}
                    </Text>
                  </View>
                </View>
              </View>
              <TouchableOpacity
                style={styles.requestButton}
                onPress={() => handleSendRequest(searchResult.id)}>
                <Text style={styles.requestButtonText}>Request</Text>
              </TouchableOpacity>
            </View>
          )}

          {searchResult === null && searchPhone.length >= 10 && !isSearching && (
            <Text style={styles.notFound}>No user found with this number</Text>
          )}

          <View style={styles.privacyNote}>
            <Text style={styles.privacyText}>
              🔒 Finding a user does NOT grant access to their location.
              They must explicitly accept your request.
            </Text>
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg.primary,
  },

  // Tabs
  tabBar: {
    flexDirection: 'row',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.bg.tertiary,
  },
  tab: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderRadius: borderRadius.sm,
  },
  tabActive: {
    backgroundColor: colors.brand.primary + '22',
  },
  tabText: {
    ...typography.caption,
    color: colors.text.tertiary,
  },
  tabTextActive: {
    color: colors.brand.primaryLight,
    fontWeight: '600',
  },

  // List
  list: {
    padding: spacing.md,
    flexGrow: 1,
  },

  // Share cards
  shareCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    ...shadows.sm,
  },
  shareInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.brand.primary + '33',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  pendingAvatar: {
    backgroundColor: colors.brand.warning + '33',
  },
  avatarText: {
    color: colors.text.primary,
    fontWeight: '700',
    fontSize: 18,
  },
  shareDetails: {
    flex: 1,
  },
  shareName: {
    ...typography.bodyBold,
    color: colors.text.primary,
  },
  shareStatus: {
    ...typography.small,
    color: colors.text.tertiary,
    marginTop: 2,
  },

  // Actions
  stopButton: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.brand.danger + '22',
    borderWidth: 1,
    borderColor: colors.brand.danger + '44',
  },
  stopText: {
    color: colors.brand.danger,
    fontWeight: '600',
    fontSize: 13,
  },
  pendingActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  acceptButton: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.brand.secondary + '22',
    borderWidth: 1,
    borderColor: colors.brand.secondary + '44',
  },
  acceptText: {
    color: colors.brand.secondary,
    fontWeight: '600',
    fontSize: 13,
  },
  declineButton: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.brand.danger + '22',
  },
  declineText: {
    color: colors.brand.danger,
    fontWeight: '600',
    fontSize: 14,
  },

  // Empty state
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 80,
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
  emptyDescription: {
    ...typography.caption,
    color: colors.text.tertiary,
    textAlign: 'center',
    maxWidth: 250,
  },

  // Search
  searchContainer: {
    padding: spacing.lg,
  },
  searchTitle: {
    ...typography.h3,
    color: colors.text.primary,
    marginBottom: spacing.md,
  },
  searchRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  searchInput: {
    flex: 1,
    backgroundColor: colors.bg.secondary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    color: colors.text.primary,
    fontSize: 16,
    borderWidth: 1,
    borderColor: colors.bg.tertiary,
  },
  searchButton: {
    backgroundColor: colors.brand.primary,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchButtonText: {
    color: colors.text.primary,
    fontWeight: '600',
  },
  resultCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    ...shadows.md,
  },
  onlineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  onlineDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing.xs,
  },
  requestButton: {
    backgroundColor: colors.brand.secondary,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
  },
  requestButtonText: {
    color: colors.text.inverse,
    fontWeight: '700',
  },
  notFound: {
    ...typography.caption,
    color: colors.text.tertiary,
    textAlign: 'center',
    marginTop: spacing.md,
  },
  privacyNote: {
    marginTop: spacing.xl,
    padding: spacing.md,
    backgroundColor: colors.brand.info + '11',
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.brand.info + '22',
  },
  privacyText: {
    ...typography.small,
    color: colors.brand.info,
    lineHeight: 20,
  },
});

export default ContactsScreen;
