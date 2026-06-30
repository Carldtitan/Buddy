import { AppIcon } from "./AppIcon";
import { StyleSheet, Text, View } from "react-native";

import { SectionHeader } from "./SectionHeader";
import { StatusPill } from "./StatusPill";
import { buildRenderPayload, renderPayloadToModel } from "../services/renderPayload";
import { colors } from "../theme/colors";
import type { AccessCheck } from "../types/contracts";

export function LocalReportRenderer({ check }: { check: AccessCheck }) {
  if (!check.final_report) {
    return null;
  }

  const payload = buildRenderPayload(check.final_report, check.place);
  const model = renderPayloadToModel(payload, check.final_report);

  return (
    <View style={styles.wrap}>
      <SectionHeader title="Access Report" meta={`${Math.round(model.confidence * 100)}% confidence`} />
      <View style={styles.topRow}>
        <StatusPill status={model.status} />
        <View style={styles.placeBlock}>
          <Text style={styles.place}>{model.placeName}</Text>
          {model.placeAddress ? <Text style={styles.address}>{model.placeAddress}</Text> : null}
        </View>
      </View>
      <Text style={styles.summary}>{model.summary}</Text>
      <View style={styles.recommendation}>
        <AppIcon name="ShieldCheck" color={colors.green} size={18} strokeWidth={2.3} />
        <Text style={styles.recommendationText}>{model.recommendation}</Text>
      </View>
      <View style={styles.sectionGrid}>
        {model.sections.map((section) => (
          <View key={section.title} style={styles.renderSection}>
            <Text style={styles.sectionTitle}>{section.title}</Text>
            {section.items.length > 0 ? (
              section.items.map((item) => (
                <Text key={item} style={styles.sectionItem}>
                  {item}
                </Text>
              ))
            ) : (
              <Text style={styles.empty}>None logged</Text>
            )}
          </View>
        ))}
      </View>
      <Text style={styles.expiry}>Expires {new Date(model.expiresAt).toLocaleString()}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderTopColor: colors.line,
    borderTopWidth: StyleSheet.hairlineWidth,
    padding: 14
  },
  topRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12
  },
  placeBlock: {
    flex: 1
  },
  place: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "900",
    letterSpacing: 0
  },
  address: {
    color: colors.inkMuted,
    fontSize: 13,
    fontWeight: "600",
    letterSpacing: 0,
    marginTop: 2
  },
  summary: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "800",
    letterSpacing: 0,
    lineHeight: 25,
    marginTop: 14
  },
  recommendation: {
    alignItems: "flex-start",
    backgroundColor: colors.greenSoft,
    borderRadius: 8,
    flexDirection: "row",
    gap: 9,
    marginTop: 12,
    padding: 11
  },
  recommendationText: {
    color: colors.green,
    flex: 1,
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 0,
    lineHeight: 19
  },
  sectionGrid: {
    gap: 10,
    marginTop: 14
  },
  renderSection: {
    borderColor: colors.line,
    borderRadius: 8,
    borderWidth: 1,
    padding: 11
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "900",
    letterSpacing: 0,
    marginBottom: 7,
    textTransform: "uppercase"
  },
  sectionItem: {
    color: colors.inkMuted,
    fontSize: 14,
    letterSpacing: 0,
    lineHeight: 20,
    marginBottom: 5
  },
  empty: {
    color: colors.inkMuted,
    fontSize: 14,
    fontStyle: "italic",
    letterSpacing: 0
  },
  expiry: {
    color: colors.inkMuted,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0,
    marginTop: 10
  }
});
