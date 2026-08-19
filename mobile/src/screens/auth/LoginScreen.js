/**
 * GeoPulse — Login Screen (Phone OTP)
 */

import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Animated,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { colors, spacing, borderRadius, typography } from '../../theme';
import authApi from '../../api/auth';
import { useAuth } from '../../store/AuthContext';

const LoginScreen = () => {
  const { login } = useAuth();
  const [step, setStep] = useState('phone'); // phone | otp | name
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [devCode, setDevCode] = useState('');

  const fadeAnim = useRef(new Animated.Value(1)).current;

  const animateTransition = (callback) => {
    Animated.sequence([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true,
      }),
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
    setTimeout(callback, 150);
  };

  const handleSendOtp = async () => {
    if (phone.length < 10) {
      Alert.alert('Invalid Phone', 'Please enter a valid phone number');
      return;
    }

    setIsLoading(true);
    try {
      const { data } = await authApi.sendOtp(phone);
      if (data.detail) {
        setDevCode(data.detail);
      }
      animateTransition(() => setStep('otp'));
    } catch (error) {
      const message = error.response?.data?.error?.message || 'Failed to send OTP';
      Alert.alert('Error', message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otp.length < 4) {
      Alert.alert('Invalid OTP', 'Please enter the verification code');
      return;
    }

    setIsLoading(true);
    try {
      const data = await authApi.verifyOtp(
        phone,
        otp,
        name || undefined,
        undefined,
        Platform.OS,
      );

      if (data.is_new_user && !name) {
        animateTransition(() => setStep('name'));
        return;
      }

      await login(data);
    } catch (error) {
      const message = error.response?.data?.error?.message || 'Invalid OTP';
      Alert.alert('Verification Failed', message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSetName = async () => {
    if (!name.trim()) {
      Alert.alert('Name Required', 'Please enter your display name');
      return;
    }
    // Re-verify with name
    setIsLoading(true);
    try {
      const data = await authApi.verifyOtp(phone, otp, name, undefined, Platform.OS);
      await login(data);
    } catch (error) {
      Alert.alert('Error', 'Failed to complete registration');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={styles.content}>
        {/* Logo Area */}
        <View style={styles.logoArea}>
          <View style={styles.logoCircle}>
            <Text style={styles.logoIcon}>📍</Text>
          </View>
          <Text style={styles.appName}>GeoPulse</Text>
          <Text style={styles.tagline}>
            Privacy-first location sharing
          </Text>
        </View>

        {/* Form Area */}
        <Animated.View style={[styles.formArea, { opacity: fadeAnim }]}>
          {step === 'phone' && (
            <>
              <Text style={styles.stepTitle}>Enter your phone number</Text>
              <Text style={styles.stepDescription}>
                We'll send you a verification code
              </Text>
              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="+91 98765 43210"
                  placeholderTextColor={colors.text.tertiary}
                  value={phone}
                  onChangeText={setPhone}
                  keyboardType="phone-pad"
                  autoFocus
                  maxLength={15}
                />
              </View>
              <TouchableOpacity
                style={[styles.button, !phone && styles.buttonDisabled]}
                onPress={handleSendOtp}
                disabled={isLoading || !phone}>
                {isLoading ? (
                  <ActivityIndicator color={colors.text.primary} />
                ) : (
                  <Text style={styles.buttonText}>Send Code</Text>
                )}
              </TouchableOpacity>
            </>
          )}

          {step === 'otp' && (
            <>
              <Text style={styles.stepTitle}>Verification code</Text>
              <Text style={styles.stepDescription}>
                Enter the 6-digit code sent to {phone}
              </Text>
              {devCode ? (
                <View style={styles.devBanner}>
                  <Text style={styles.devBannerText}>Dev code: {devCode}</Text>
                </View>
              ) : null}
              <View style={styles.inputContainer}>
                <TextInput
                  style={[styles.input, styles.otpInput]}
                  placeholder="000000"
                  placeholderTextColor={colors.text.tertiary}
                  value={otp}
                  onChangeText={setOtp}
                  keyboardType="number-pad"
                  maxLength={6}
                  autoFocus
                  textAlign="center"
                />
              </View>
              <TouchableOpacity
                style={[styles.button, !otp && styles.buttonDisabled]}
                onPress={handleVerifyOtp}
                disabled={isLoading || !otp}>
                {isLoading ? (
                  <ActivityIndicator color={colors.text.primary} />
                ) : (
                  <Text style={styles.buttonText}>Verify</Text>
                )}
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.backButton}
                onPress={() => animateTransition(() => setStep('phone'))}>
                <Text style={styles.backText}>Change number</Text>
              </TouchableOpacity>
            </>
          )}

          {step === 'name' && (
            <>
              <Text style={styles.stepTitle}>Welcome!</Text>
              <Text style={styles.stepDescription}>
                What should we call you?
              </Text>
              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="Your name"
                  placeholderTextColor={colors.text.tertiary}
                  value={name}
                  onChangeText={setName}
                  maxLength={100}
                  autoFocus
                />
              </View>
              <TouchableOpacity
                style={[styles.button, !name && styles.buttonDisabled]}
                onPress={handleSetName}
                disabled={isLoading || !name.trim()}>
                {isLoading ? (
                  <ActivityIndicator color={colors.text.primary} />
                ) : (
                  <Text style={styles.buttonText}>Get Started</Text>
                )}
              </TouchableOpacity>
            </>
          )}
        </Animated.View>

        {/* Footer */}
        <Text style={styles.footer}>
          Your phone number is used for identity only.{'\n'}
          Location is never shared without your explicit consent.
        </Text>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg.primary,
  },
  content: {
    flex: 1,
    paddingHorizontal: spacing.xl,
    justifyContent: 'center',
  },
  logoArea: {
    alignItems: 'center',
    marginBottom: spacing.xxl,
  },
  logoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.bg.tertiary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  logoIcon: {
    fontSize: 36,
  },
  appName: {
    ...typography.h1,
    color: colors.text.primary,
    marginBottom: spacing.xs,
  },
  tagline: {
    ...typography.caption,
    color: colors.text.tertiary,
  },
  formArea: {
    marginBottom: spacing.xl,
  },
  stepTitle: {
    ...typography.h3,
    color: colors.text.primary,
    marginBottom: spacing.xs,
  },
  stepDescription: {
    ...typography.caption,
    color: colors.text.secondary,
    marginBottom: spacing.lg,
  },
  inputContainer: {
    marginBottom: spacing.lg,
  },
  input: {
    backgroundColor: colors.bg.secondary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    color: colors.text.primary,
    fontSize: 18,
    borderWidth: 1,
    borderColor: colors.bg.tertiary,
  },
  otpInput: {
    fontSize: 28,
    letterSpacing: 12,
    fontWeight: '700',
  },
  button: {
    backgroundColor: colors.brand.primary,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
    height: 52,
  },
  buttonDisabled: {
    opacity: 0.4,
  },
  buttonText: {
    ...typography.bodyBold,
    color: colors.text.primary,
  },
  backButton: {
    marginTop: spacing.md,
    alignItems: 'center',
  },
  backText: {
    ...typography.caption,
    color: colors.brand.primaryLight,
  },
  devBanner: {
    backgroundColor: colors.brand.warning + '22',
    borderRadius: borderRadius.sm,
    padding: spacing.sm,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.brand.warning + '44',
  },
  devBannerText: {
    color: colors.brand.warning,
    textAlign: 'center',
    fontWeight: '600',
    fontSize: 16,
  },
  footer: {
    ...typography.small,
    color: colors.text.tertiary,
    textAlign: 'center',
    lineHeight: 18,
  },
});

export default LoginScreen;
