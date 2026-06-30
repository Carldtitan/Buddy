import { AppIcon } from "./AppIcon";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

import { colors } from "../theme/colors";
import type { AccessNeeds } from "../types/contracts";

type NeedFlag = Exclude<keyof AccessNeeds, "notes">;

const items: Array<{ key: NeedFlag; label: string }> = [
  { key: "step_free_entrance", label: "Step-free entry" },
  { key: "accessible_restroom", label: "Restroom" },
  { key: "wheelchair_seating_or_path", label: "Clear path" },
  { key: "avoid_temporary_blockers", label: "No blockers" }
];

export function NeedToggles({
  needs,
  onChange
}: {
  needs: AccessNeeds;
  onChange: (needs: AccessNeeds) => void;
}) {
  return (
    <View style={styles.wrap}>
      {items.map((item) => {
        const enabled = Boolean(needs[item.key]);
        return (
          <TouchableOpacity
            accessibilityRole="checkbox"
            accessibilityState={{ checked: enabled }}
            key={item.key}
            onPress={() => onChange({ ...needs, [item.key]: !enabled })}
            style={[styles.toggle, enabled && styles.toggleActive]}
          >
            <AppIcon
              color={enabled ? colors.green : colors.inkMuted}
              name={enabled ? "CheckCircle2" : "Circle"}
              size={17}
              strokeWidth={2.3}
            />
            <Text style={[styles.label, enabled && styles.labelActive]} numberOfLines={1}>
              {item.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 12
  },
  toggle: {
    alignItems: "center",
    borderColor: colors.line,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: "row",
    gap: 7,
    minHeight: 36,
    paddingHorizontal: 10
  },
  toggleActive: {
    backgroundColor: colors.greenSoft,
    borderColor: colors.green
  },
  label: {
    color: colors.inkMuted,
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 0,
    maxWidth: 112
  },
  labelActive: {
    color: colors.green
  }
});
