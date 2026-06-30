import { StyleSheet, Text, View } from "react-native";

import { SectionHeader } from "./SectionHeader";
import { colors } from "../theme/colors";
import type { TranscriptTurn } from "../types/contracts";

export function TranscriptView({ turns }: { turns: TranscriptTurn[] }) {
  return (
    <View style={styles.wrap}>
      <SectionHeader title="Transcript" meta={`${turns.length} turns`} />
      {turns.length === 0 ? (
        <Text style={styles.empty}>No transcript yet.</Text>
      ) : (
        turns.map((turn, index) => (
          <View key={`${turn.speaker}-${index}`} style={styles.turn}>
            <Text style={[styles.speaker, turn.speaker === "venue" ? styles.venue : styles.buddy]}>
              {turn.speaker}
            </Text>
            <Text style={styles.text}>{turn.text}</Text>
          </View>
        ))
      )}
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
    letterSpacing: 0
  },
  turn: {
    borderLeftColor: colors.lineStrong,
    borderLeftWidth: 2,
    marginBottom: 12,
    paddingLeft: 10
  },
  speaker: {
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0,
    marginBottom: 3,
    textTransform: "uppercase"
  },
  buddy: {
    color: colors.blue
  },
  venue: {
    color: colors.green
  },
  text: {
    color: colors.ink,
    fontSize: 14,
    letterSpacing: 0,
    lineHeight: 20
  }
});
