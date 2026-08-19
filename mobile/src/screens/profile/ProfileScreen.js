/**
 * GeoPulse — Profile Screen
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  Switch,
} from 'react-native';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme';
import { useAuth } from '../../store/AuthContext';
import { userApi } from '../../api/endpoints';
import { privacyApi } from '../../api/endpoints';
import { getTokens } from '../../api/client';
import authApi from '../../api/auth';

const ProfileScreen = () => {
  const { user, logout, refreshProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(user?.name || '');
  const [editEmail, setEditEmail] = useState(user?.email || '');

  const handleSave = async () => {
    try {
      await userApi.updateProfile({
        name: editName,
        email: editEmail || undefined,
      });
      await refreshProfile();
      setIsEditing(false);
    } catch (e) {
      Alert.alert('Error', 'Failed to update profile');
    }
  };

  const handleLogout = async () => {
    Alert.alert('Logout', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        onPress: async () => {
          const { refreshToken } = await getTokens();
          await authApi.logout(refreshToken);
          await logout();
        },
      },
    ]);
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      '⚠️ Delete Account',
      'This will permanently delete your account, all shares, location history, and data. This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete Everything',
          style: 'destructive',
          onPress: () => {
            Alert.alert('Final Confirmation', 'Are you absolutely sure?', [
              { text: 'Cancel', style: 'cancel' },
              {
                text: 'Delete',
                style: 'destructive',
                onPress: async () => {
                  try {
                    await privacyApi.deleteAccount();
                    await logout();
                  } catch (e) {
                    Alert.alert('Error', 'Failed to delete account');
                  }
                },
              },
            ]);
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Profile Header */}
      <View style={styles.profileHeader}>
        <View style={styles.avatarLarge}>
          <Text style={styles.avatarLargeText}>
            {(user?.name || 'U')[0].toUpperCase()}
          </Text>
        </View>
        {isEditing ? (
          <TextInput
            style={styles.nameInput}
            value={editName}
            onChangeText={setEditName}
            placeholder="Your name"
            placeholderTextColor={colors.text.tertiary}
          />
        ) : (
          <Text style={styles.profileName}>{user?.name || 'User'}</Text>
        )}
        <Text style={styles.profilePhone}>{user?.phone}</Text>
      </View>

      {/* Edit Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Profile</Text>

        <View style={styles.card}>
          <View style={styles.row}>
            <Text style={styles.rowLabel}>Name</Text>
            {isEditing ? (
              <TextInput
                style={styles.rowInput}
                value={editName}
                onChangeText={setEditName}
              />
            ) : (
              <Text style={styles.rowValue}>{user?.name}</Text>
            )}
          </View>

          <View style={styles.divider} />

          <View style={styles.row}>
            <Text style={styles.rowLabel}>Email</Text>
            {isEditing ? (
              <TextInput
                style={styles.rowInput}
                value={editEmail}
                onChangeText={setEditEmail}
                keyboardType="email-address"
                placeholder="Optional"
                placeholderTextColor={colors.text.tertiary}
              />
            ) : (
              <Text style={styles.rowValue}>{user?.email || 'Not set'}</Text>
            )}
          </View>

          <View style={styles.divider} />

          <View style={styles.row}>
            <Text style={styles.rowLabel}>Phone</Text>
            <Text style={styles.rowValue}>{user?.phone}</Text>
          </View>
        </View>

        {isEditing ? (
          <View style={styles.editActions}>
            <TouchableOpacity
              style={styles.saveButton}
              onPress={handleSave}>
              <Text style={styles.saveText}>Save Changes</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.cancelEditButton}
              onPress={() => {
                setIsEditing(false);
                setEditName(user?.name || '');
                setEditEmail(user?.email || '');
              }}>
              <Text style={styles.cancelEditText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <TouchableOpacity
            style={styles.editButton}
            onPress={() => setIsEditing(true)}>
            <Text style={styles.editButtonText}>Edit Profile</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Privacy Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Privacy</Text>
        <View style={styles.card}>
          <View style={styles.row}>
            <Text style={styles.rowLabel}>Discoverability</Text>
            <Text style={styles.rowValue}>
              {user?.privacy_settings?.discoverability || 'everyone'}
            </Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.row}>
            <Text style={styles.rowLabel}>Location sharing</Text>
            <Text style={styles.rowValue}>
              {user?.privacy_settings?.location_sharing_enabled ? 'Enabled' : 'Disabled'}
            </Text>
          </View>
        </View>
      </View>

      {/* Account Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account</Text>
        <TouchableOpacity style={styles.actionButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>Log Out</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.deleteButton]}
          onPress={handleDeleteAccount}>
          <Text style={styles.deleteText}>Delete Account</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>GeoPulse v1.0</Text>
        <Text style={styles.footerText}>Privacy-first location sharing</Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg.primary,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl * 2,
  },

  // Header
  profileHeader: {
    alignItems: 'center',
    marginBottom: spacing.xl,
    paddingTop: spacing.lg,
  },
  avatarLarge: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.brand.primary + '44',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
    ...shadows.glow(colors.brand.primary),
  },
  avatarLargeText: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.brand.primaryLight,
  },
  profileName: {
    ...typography.h2,
    color: colors.text.primary,
    marginBottom: spacing.xs,
  },
  profilePhone: {
    ...typography.caption,
    color: colors.text.tertiary,
  },
  nameInput: {
    ...typography.h2,
    color: colors.text.primary,
    textAlign: 'center',
    borderBottomWidth: 2,
    borderBottomColor: colors.brand.primary,
    marginBottom: spacing.xs,
    paddingBottom: spacing.xs,
  },

  // Sections
  section: {
    marginBottom: spacing.xl,
  },
  sectionTitle: {
    ...typography.label,
    color: colors.text.tertiary,
    textTransform: 'uppercase',
    marginBottom: spacing.sm,
    paddingLeft: spacing.xs,
  },
  card: {
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.md,
  },
  rowLabel: {
    ...typography.body,
    color: colors.text.secondary,
  },
  rowValue: {
    ...typography.body,
    color: colors.text.primary,
  },
  rowInput: {
    ...typography.body,
    color: colors.text.primary,
    textAlign: 'right',
    flex: 1,
    marginLeft: spacing.md,
  },
  divider: {
    height: 1,
    backgroundColor: colors.bg.tertiary,
    marginHorizontal: spacing.md,
  },

  // Actions
  editButton: {
    marginTop: spacing.md,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.brand.primary + '22',
    alignItems: 'center',
  },
  editButtonText: {
    ...typography.bodyBold,
    color: colors.brand.primaryLight,
  },
  editActions: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.md,
  },
  saveButton: {
    flex: 1,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.brand.secondary,
    alignItems: 'center',
  },
  saveText: {
    ...typography.bodyBold,
    color: colors.text.inverse,
  },
  cancelEditButton: {
    flex: 1,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.bg.tertiary,
    alignItems: 'center',
  },
  cancelEditText: {
    ...typography.bodyBold,
    color: colors.text.secondary,
  },
  actionButton: {
    padding: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.bg.card,
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  logoutText: {
    ...typography.bodyBold,
    color: colors.brand.warning,
  },
  deleteButton: {
    backgroundColor: colors.brand.danger + '11',
    borderWidth: 1,
    borderColor: colors.brand.danger + '33',
  },
  deleteText: {
    ...typography.bodyBold,
    color: colors.brand.danger,
  },

  // Footer
  footer: {
    alignItems: 'center',
    paddingTop: spacing.lg,
  },
  footerText: {
    ...typography.small,
    color: colors.text.tertiary,
    marginBottom: 2,
  },
});

export default ProfileScreen;
