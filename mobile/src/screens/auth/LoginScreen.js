/**
 * GeoPulse — Login Screen (Phone OTP Authentication)
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
import { colors, spacing, borderRadius, typography, shadows } from '../../theme';
import authApi from '../../api/auth';
import { useAuth } from '../../store/AuthContext';

const LoginScreen = () => {
  const { login } = useAuth();
  const [step, setStep] = useState('phone'); // phone | otp | name
  const [phone, setPhone] = useState('+91 98765 43210');
  const [otp, setOtp] = useState('');
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [devCode, setDevCode] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fadeAnim = useRef(new Animated.Value(1)).current;

  const animateTransition = (callback) => {
    setErrorMsg('');
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
      setErrorMsg('Please enter a valid phone number');
      return;
    }

    setIsLoading(true);
    setErrorMsg('');
    try {
      const { data } = await authApi.sendOtp(phone);
      if (data?.detail) {
        setDevCode(data.detail);
      } else {
        setDevCode('123456');
      }
      animateTransition(() => setStep('otp'));
    } catch (error) {
      // Fallback in case backend is offline or dev mode
      setDevCode('123456');
      animateTransition(() => setStep('otp'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otp.length < 4) {
      setErrorMsg('Please enter the 6-digit code');
      return;
    }

    setIsLoading(true);
    setErrorMsg('');
    try {
      const data = await authApi.verifyOtp(
        phone,
        otp,
        name || undefined,
        undefined,
        Platform.OS
      );

      if (data?.is_new_user && !name) {
        animateTransition(() => setStep('name'));
        return;
      }

      await login(data);
    } catch (error) {
      const msg =
        error?.response?.data?.detail ||
        error?.message ||
        'Verification failed. Please check the code and try again.';
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.content}>
        {/* Logo Area */}
        <View style={styles.logoArea}>
          <View style={styles.logoCircle}>
            <Text style={styles.logoIcon}>📍</Text>
          </View>
          <Text style={styles.appName}>GeoPulse</Text>
          <Text style={styles.tagline}>Privacy-First Real-Time Location</Text>
        </View>

        {/* Error banner */}
        {errorMsg ? (
          <View style={styles.errorBanner}>
            <Text style={styles.errorText}>⚠️ {errorMsg}</Text>
          </View>
        ) : null}

        {/* Form Area */}
        <Animated.View style={[styles.formArea, { opacity: fadeAnim }]}>
          {step === 'phone' && (
            <>
              <Text style={styles.stepTitle}>Enter phone number</Text>
              <Text style={styles.stepDescription}>
                We'll send a 6-digit verification code
              </Text>
              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="+91 98765 43210"
                  placeholderTextColor={colors.text.tertiary}
                  value={phone}
                  onChangeText={setPhone}
                  keyboardType="phone-pad"
                  maxLength={16}
                />
              </View>
              <TouchableOpacity
                style={[styles.button, !phone && styles.buttonDisabled]}
                onPress={handleSendOtp}
                disabled={isLoading || !phone}>
                {isLoading ? (
                  <ActivityIndicator color={colors.text.primary} />
                ) : (
                  <Text style={styles.buttonText}>Send Code ➔</Text>
                )}
              </TouchableOpacity>


            </>
          )}

          {step === 'otp' && (
            <>
              <Text style={styles.stepTitle}>Verification Code</Text>
              <Text style={styles.stepDescription}>
                Enter the code sent to {phone}
              </Text>

              <View style={styles.devBanner}>
                <Text style={styles.devBannerText}>
                  🔑 Code: <Text style={styles.codeHighlight}>{devCode || '123456'}</Text>
                </Text>
              </View>

              <View style={styles.inputContainer}>
                <TextInput
                  style={[styles.input, styles.otpInput]}
                  placeholder="123456"
                  placeholderTextColor={colors.text.tertiary}
                  value={otp}
                  onChangeText={setOtp}
                  keyboardType="number-pad"
                  maxLength={6}
                  textAlign="center"
                  autoFocus
                />
              </View>

              <TouchableOpacity
                style={[styles.button, !otp && styles.buttonDisabled]}
                onPress={handleVerifyOtp}
                disabled={isLoading || !otp}>
                {isLoading ? (
                  <ActivityIndicator color={colors.text.primary} />
                ) : (
                  <Text style={styles.buttonText}>Verify & Continue ➔</Text>
                )}
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.backButton}
                onPress={() => animateTransition(() => setStep('phone'))}>
                <Text style={styles.backText}>← Change phone number</Text>
              </TouchableOpacity>
            </>
          )}
        </Animated.View>

        {/* Footer */}
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
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    justifyContent: 'center',
  },
  logoArea: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  logoCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: colors.bg.tertiary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xs,
    borderWidth: 2,
    borderColor: colors.brand.primary,
    ...shadows.glow(colors.brand.primary),
  },
  logoIcon: {
    fontSize: 28,
  },
  appName: {
    ...typography.h1,
    color: colors.text.primary,
    fontSize: 26,
    marginBottom: 2,
  },
  tagline: {
    ...typography.caption,
    color: colors.brand.primaryLight,
  },
  errorBanner: {
    backgroundColor: colors.brand.danger + '22',
    borderRadius: borderRadius.sm,
    padding: spacing.sm,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.brand.danger + '44',
  },
  errorText: {
    color: colors.brand.danger,
    fontSize: 13,
    textAlign: 'center',
  },
  formArea: {
    marginBottom: spacing.lg,
  },
  stepTitle: {
    ...typography.h3,
    color: colors.text.primary,
    marginBottom: spacing.xs,
  },
  stepDescription: {
    ...typography.caption,
    color: colors.text.secondary,
    marginBottom: spacing.md,
  },
  inputContainer: {
    marginBottom: spacing.md,
  },
  input: {
    backgroundColor: colors.bg.secondary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 12,
    color: colors.text.primary,
    fontSize: 16,
    borderWidth: 1,
    borderColor: colors.bg.tertiary,
  },
  otpInput: {
    fontSize: 24,
    letterSpacing: 8,
    fontWeight: '700',
  },
  button: {
    backgroundColor: colors.brand.primary,
    borderRadius: borderRadius.md,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.glow(colors.brand.primary),
  },
  buttonDisabled: {
    opacity: 0.4,
  },
  buttonText: {
    ...typography.bodyBold,
    color: colors.text.primary,
    fontSize: 15,
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
    fontSize: 13,
  },
  codeHighlight: {
    fontWeight: '700',
    color: '#FFF',
  },
  backButton: {
    marginTop: spacing.md,
    alignItems: 'center',
  },
  backText: {
    ...typography.caption,
    color: colors.brand.primaryLight,
  },
  footerBox: {
    padding: spacing.sm,
    backgroundColor: colors.bg.card,
    borderRadius: borderRadius.sm,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 11,
    color: colors.text.tertiary,
    textAlign: 'center',
  },
  footerSub: {
    fontSize: 10,
    color: colors.brand.primaryLight,
    marginTop: 2,
    textAlign: 'center',
  },
});

export default LoginScreen;
