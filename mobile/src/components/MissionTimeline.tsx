import { AppIcon } from "./AppIcon";
import { StyleSheet, Text, View } from "react-native";

import { SectionHeader } from "./SectionHeader";
import { colors } from "../theme/colors";
import type { CheckStage, TimelineEvent } from "../types/contracts";

const stageLabels: Record<CheckStage, string> = {
  created: "Created",
  resolving_place: "Place",
  scraping_public_web: "Web",
  extracting_evidence: "Extract",
  scoring_evidence: "Score",
  warming_voice_agent: "Warm",
  calling_venue: "Call",
  parsing_call: "Parse",
  generating_report: "Report",
  published: "Live",
  failed: "Failed"
};

export function MissionTimeline({ events, currentStage }: { events: TimelineEvent[]; currentStage: CheckStage }) {
  const visible = events.slice(-6);
  const latest = visible[visible.length - 1];

  return (
    <View style={styles.wrap}>
      <SectionHeader title="Mission Control" meta={stageLabels[currentStage]} />
      <View style={styles.liveRow}>
        <View style={styles.liveDot} />
        <AppIcon name="RadioTower" color={colors.blue} size={16} strokeWidth={2.2} />
        <Text style={styles.liveText}>{latest?.message ?? "Waiting for the first access check."}</Text>
      </View>
      <View style={styles.timeline}>
        {visible.map((event, index) => (
          <View key={`${event.stage}-${event.created_at}`} style={styles.event}>
            <View style={[styles.marker, index === visible.length - 1 && styles.markerActive]} />
            <View style={styles.eventBody}>
              <Text style={styles.eventTitle}>{stageLabels[event.stage]}</Text>
              <Text style={styles.eventText}>{event.message}</Text>
            </View>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    padding: 14
  },
  liveRow: {
    alignItems: "center",
    backgroundColor: colors.blueSoft,
    borderRadius: 8,
    flexDirection: "row",
    gap: 8,
    minHeight: 42,
    paddingHorizontal: 10,
    paddingVertical: 8
  },
  liveDot: {
    backgroundColor: colors.green,
    borderRadius: 4,
    height: 8,
    width: 8
  },
  liveText: {
    color: colors.blue,
    flex: 1,
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 0
  },
  timeline: {
    marginTop: 12
  },
  event: {
    flexDirection: "row",
    gap: 10,
    paddingBottom: 12
  },
  marker: {
    backgroundColor: colors.lineStrong,
    borderRadius: 5,
    height: 10,
    marginTop: 3,
    width: 10
  },
  markerActive: {
    backgroundColor: colors.blue
  },
  eventBody: {
    flex: 1
  },
  eventTitle: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 0
  },
  eventText: {
    color: colors.inkMuted,
    fontSize: 13,
    letterSpacing: 0,
    lineHeight: 18,
    marginTop: 2
  }
});
