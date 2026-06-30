import { AppIcon } from "./AppIcon";
import { StyleSheet, Text, View } from "react-native";

import { SectionHeader } from "./SectionHeader";
import { colors } from "../theme/colors";
import type { CallSession } from "../types/contracts";

const factLabels = {
  step_free_entrance: "Entry",
  accessible_restroom: "Restroom",
  wheelchair_seating_or_path: "Path"
} as const;

export function CallSummary({ call }: { call?: CallSession | null }) {
  if (!call) {
    return (
      <View style={styles.wrap}>
        <SectionHeader title="Call Summary" meta="Not placed" />
        <Text style={styles.empty}>Buddy will call when public evidence leaves critical facts unresolved.</Text>
      </View>
    );
  }

  return (
    <View style={styles.wrap}>
      <SectionHeader title="Call Summary" meta={call.status.replace("_", " ")} />
      <View style={styles.summaryRow}>
        <View style={styles.iconBox}>
          <AppIcon name="PhoneCall" color={colors.blue} size={20} strokeWidth={2.4} />
        </View>
        <Text style={styles.summary}>{call.conversation_summary ?? "Call transcript received."}</Text>
      </View>
      <View style={styles.facts}>
        {Object.entries(factLabels).map(([key, label]) => {
          const value = call.extracted_facts[key as keyof typeof factLabels];
          return (
            <View key={key} style={styles.fact}>
              <Text style={styles.factLabel}>{label}</Text>
              <Text style={[styles.factValue, value === "yes" ? styles.yes : value === "no" ? styles.no : styles.unknown]}>
                {value}
              </Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderTopColor: colors.line,
    borderTopWidth: StyleSheet.hairlineWidth,
    padding: 14
  },
  empty: {
    color: colors.inkMuted,
    fontSize: 14,
    letterSpacing: 0,
    lineHeight: 20
  },
  summaryRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: 10
  },
  iconBox: {
    alignItems: "center",
    backgroundColor: colors.blueSoft,
    borderRadius: 8,
    height: 38,
    justifyContent: "center",
    width: 38
  },
  summary: {
    color: colors.ink,
    flex: 1,
    fontSize: 14,
    fontWeight: "700",
    letterSpacing: 0,
    lineHeight: 20
  },
  facts: {
    flexDirection: "row",
    gap: 8,
    marginTop: 12
  },
  fact: {
    borderColor: colors.line,
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    minHeight: 58,
    paddingHorizontal: 9,
    paddingVertical: 8
  },
  factLabel: {
    color: colors.inkMuted,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0
  },
  factValue: {
    fontSize: 16,
    fontWeight: "900",
    letterSpacing: 0,
    marginTop: 4,
    textTransform: "uppercase"
  },
  yes: {
    color: colors.green
  },
  no: {
    color: colors.red
  },
  unknown: {
    color: colors.yellow
  }
});
