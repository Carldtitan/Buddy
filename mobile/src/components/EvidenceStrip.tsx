import { AppIcon } from "./AppIcon";
import { Image, ScrollView, StyleSheet, Text, View } from "react-native";

import { SectionHeader } from "./SectionHeader";
import { colors } from "../theme/colors";
import type { EvidenceItem } from "../types/contracts";

const featureLabel: Record<string, string> = {
  entrance: "Entrance",
  restroom: "Restroom",
  seating: "Seating",
  route: "Route",
  temporary_blocker: "Blockers",
  hours: "Hours",
  unknown: "Unknown"
};

export function EvidenceStrip({ evidence }: { evidence: EvidenceItem[] }) {
  return (
    <View style={styles.wrap}>
      <SectionHeader title="Evidence" meta={`${evidence.length} items`} />
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
        {evidence.map((item) => (
          <View key={item.id} style={styles.item}>
            {item.image_url ? (
              <Image source={{ uri: item.image_url }} style={styles.image} resizeMode="cover" />
            ) : (
              <View style={styles.placeholder}>
                {item.source_type === "photo" ? (
                  <AppIcon name="Camera" color={colors.blue} size={24} strokeWidth={2.2} />
                ) : item.source_url ? (
                  <AppIcon name="LinkIcon" color={colors.blue} size={24} strokeWidth={2.2} />
                ) : (
                  <AppIcon name="FileText" color={colors.blue} size={24} strokeWidth={2.2} />
                )}
              </View>
            )}
            <View style={styles.body}>
              <Text style={styles.feature}>{featureLabel[item.feature] ?? "Evidence"}</Text>
              <Text style={styles.claim} numberOfLines={4}>
                {item.claim}
              </Text>
              <Text style={styles.meta}>
                {item.source_type} · {Math.round(item.confidence * 100)}%
              </Text>
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderTopColor: colors.line,
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingBottom: 14,
    paddingTop: 14
  },
  row: {
    gap: 10,
    paddingHorizontal: 14
  },
  item: {
    borderColor: colors.line,
    borderRadius: 8,
    borderWidth: 1,
    overflow: "hidden",
    width: 232
  },
  image: {
    backgroundColor: colors.surfaceMuted,
    height: 108,
    width: "100%"
  },
  placeholder: {
    alignItems: "center",
    backgroundColor: colors.blueSoft,
    height: 108,
    justifyContent: "center",
    width: "100%"
  },
  body: {
    padding: 10
  },
  feature: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0,
    textTransform: "uppercase"
  },
  claim: {
    color: colors.inkMuted,
    fontSize: 13,
    letterSpacing: 0,
    lineHeight: 18,
    marginTop: 6
  },
  meta: {
    color: colors.blue,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0,
    marginTop: 8,
    textTransform: "uppercase"
  }
});
