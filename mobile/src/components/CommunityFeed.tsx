import { AppIcon } from "./AppIcon";
import { StyleSheet, Text, View } from "react-native";

import { SectionHeader } from "./SectionHeader";
import { StatusPill } from "./StatusPill";
import { colors } from "../theme/colors";
import type { CommunityReport } from "../types/contracts";

export function CommunityFeed({ reports }: { reports: CommunityReport[] }) {
  return (
    <View style={styles.wrap}>
      <SectionHeader title="Community Feed" meta={`${reports.length} reports`} />
      {reports.map((report) => (
        <View key={report.id} style={styles.item}>
          <View style={styles.itemTop}>
            <StatusPill status={report.status} />
            <View style={styles.placeBlock}>
              <Text style={styles.place}>{report.place.name}</Text>
              <Text style={styles.address} numberOfLines={1}>
                {report.place.address ?? "Address pending"}
              </Text>
            </View>
          </View>
          <Text style={styles.summary}>{report.public_summary}</Text>
          <View style={styles.expiryRow}>
            <AppIcon name="Clock" color={colors.inkMuted} size={13} strokeWidth={2.1} />
            <Text style={styles.expiry}>Expires {new Date(report.expires_at).toLocaleDateString()}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderTopColor: colors.line,
    borderTopWidth: StyleSheet.hairlineWidth,
    padding: 14
  },
  item: {
    borderColor: colors.line,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 10,
    padding: 10
  },
  itemTop: {
    alignItems: "center",
    flexDirection: "row",
    gap: 10
  },
  placeBlock: {
    flex: 1,
    minWidth: 0
  },
  place: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: "900",
    letterSpacing: 0
  },
  address: {
    color: colors.inkMuted,
    fontSize: 12,
    fontWeight: "600",
    letterSpacing: 0,
    marginTop: 2
  },
  summary: {
    color: colors.ink,
    fontSize: 14,
    letterSpacing: 0,
    lineHeight: 20,
    marginTop: 10
  },
  expiryRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 5,
    marginTop: 9
  },
  expiry: {
    color: colors.inkMuted,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0
  }
});
