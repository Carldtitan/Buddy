import { StyleSheet, Text, View } from "react-native";

import { colors } from "../theme/colors";

export function SectionHeader({ title, meta }: { title: string; meta?: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.title}>{title}</Text>
      {meta ? <Text style={styles.meta}>{meta}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    alignItems: "baseline",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 10
  },
  title: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "800",
    letterSpacing: 0
  },
  meta: {
    color: colors.inkMuted,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0
  }
});
