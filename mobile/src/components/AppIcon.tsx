import { StyleSheet, Text } from "react-native";

import { colors } from "../theme/colors";

const glyphs = {
  AlertTriangle: "!",
  Camera: "[]",
  CheckCircle2: "✓",
  Circle: "○",
  CircleHelp: "?",
  Clock: "t",
  FileText: "≡",
  LinkIcon: "↗",
  MapPin: "⌖",
  Navigation: "→",
  PhoneCall: "☎",
  RadioTower: "≋",
  RefreshCw: "↻",
  Search: "⌕",
  ShieldCheck: "✓",
  Wifi: "on",
  WifiOff: "off",
  XCircle: "×"
} as const;

export type AppIconName = keyof typeof glyphs;

export function AppIcon({
  name,
  color = colors.ink,
  size = 16
}: {
  name: AppIconName;
  color?: string;
  size?: number;
  strokeWidth?: number;
}) {
  return (
    <Text
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={[styles.icon, { color, fontSize: Math.max(10, size - 2), minWidth: size }]}
    >
      {glyphs[name]}
    </Text>
  );
}

const styles = StyleSheet.create({
  icon: {
    fontWeight: "900",
    letterSpacing: 0,
    lineHeight: 18,
    textAlign: "center"
  }
});
