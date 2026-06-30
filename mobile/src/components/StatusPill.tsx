import { AppIcon } from "./AppIcon";
import { StyleSheet, Text, View } from "react-native";

import { colors } from "../theme/colors";
import type { AccessStatus } from "../types/contracts";

const statusCopy: Record<AccessStatus, { label: string; tone: string; background: string }> = {
  green: { label: "Green", tone: colors.green, background: colors.greenSoft },
  yellow: { label: "Yellow", tone: colors.yellow, background: colors.yellowSoft },
  red: { label: "Red", tone: colors.red, background: colors.redSoft },
  unknown: { label: "Unknown", tone: colors.inkMuted, background: colors.surfaceMuted }
};

function StatusIcon({ status, color }: { status: AccessStatus; color: string }) {
  const common = { size: 15, color, strokeWidth: 2.4 };
  if (status === "green") return <AppIcon name="CheckCircle2" {...common} />;
  if (status === "yellow") return <AppIcon name="AlertTriangle" {...common} />;
  if (status === "red") return <AppIcon name="XCircle" {...common} />;
  return <AppIcon name="CircleHelp" {...common} />;
}

export function StatusPill({ status }: { status: AccessStatus }) {
  const copy = statusCopy[status];

  return (
    <View style={[styles.pill, { backgroundColor: copy.background }]}>
      <StatusIcon status={status} color={copy.tone} />
      <Text style={[styles.text, { color: copy.tone }]}>{copy.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    alignItems: "center",
    alignSelf: "flex-start",
    borderRadius: 999,
    flexDirection: "row",
    gap: 6,
    height: 30,
    paddingHorizontal: 10
  },
  text: {
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0,
    textTransform: "uppercase"
  }
});
